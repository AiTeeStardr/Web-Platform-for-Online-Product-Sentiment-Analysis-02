"""
Feature Extractor - TF-IDF and Delta TF-IDF
"""
import numpy as np
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

import os
try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False


class FeatureExtractor:
    """
    Feature extraction using TF-IDF and Delta TF-IDF.

    Delta TF-IDF weights terms by their discriminative power between
    positive and negative classes, useful for sentiment analysis.
    """

    def __init__(self, max_features=5000, ngram_range=(1, 2)):
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.vectorizer = None
        self.delta_weights = None

        if HAS_SKLEARN:
            self.vectorizer = TfidfVectorizer(
                max_features=max_features,
                ngram_range=ngram_range,
                sublinear_tf=True,
                strip_accents=None,   # Keep Thai characters
                token_pattern=r'(?u)\b\w+\b'
            )

    def fit_transform(self, texts, labels=None):
        """
        Fit the vectorizer and optionally compute Delta TF-IDF.

        Args:
            texts: List of pre-tokenized text strings (space-joined tokens)
            labels: Optional sentiment labels for Delta TF-IDF computation

        Returns:
            Feature matrix (sparse or dense)
        """
        if not HAS_SKLEARN:
            return np.zeros((len(texts), 1))

        # Standard TF-IDF
        tfidf_matrix = self.vectorizer.fit_transform(texts)

        # Compute Delta TF-IDF if labels provided
        if labels is not None:
            self.delta_weights = self._compute_delta_weights(tfidf_matrix, labels)
            # Apply delta weights
            tfidf_matrix = tfidf_matrix.multiply(self.delta_weights)

        return tfidf_matrix

    def transform(self, texts):
        """Transform new texts using fitted vectorizer."""
        if not HAS_SKLEARN or self.vectorizer is None:
            return np.zeros((len(texts), 1))

        tfidf_matrix = self.vectorizer.transform(texts)

        if self.delta_weights is not None:
            tfidf_matrix = tfidf_matrix.multiply(self.delta_weights)

        return tfidf_matrix

    def _compute_delta_weights(self, tfidf_matrix, labels):
        """
        Compute Delta TF-IDF weights.

        Delta TF-IDF = TF-IDF(positive) - TF-IDF(negative)
        Terms important for positive class get positive weights,
        terms important for negative class get negative weights.
        """
        labels = np.array(labels)
        n_features = tfidf_matrix.shape[1]

        # Separate positive and negative documents
        pos_mask = labels == 'positive'
        neg_mask = labels == 'negative'

        if pos_mask.sum() == 0 or neg_mask.sum() == 0:
            return np.ones(n_features)

        # Average TF-IDF per class
        pos_avg = np.array(tfidf_matrix[pos_mask].mean(axis=0)).flatten()
        neg_avg = np.array(tfidf_matrix[neg_mask].mean(axis=0)).flatten()

        # Delta = difference in importance
        delta = pos_avg - neg_avg

        # Normalize to [0.5, 1.5] range to avoid zeroing out features
        delta_min = delta.min()
        delta_max = delta.max()
        if delta_max - delta_min > 0:
            delta = 0.5 + (delta - delta_min) / (delta_max - delta_min)
        else:
            delta = np.ones(n_features)

        return delta

    def get_feature_names(self):
        """Get feature names from vectorizer."""
        if self.vectorizer and hasattr(self.vectorizer, 'get_feature_names_out'):
            return self.vectorizer.get_feature_names_out()
        return []

    def get_top_features(self, tfidf_vector, n=10):
        """Get top N features for a single document."""
        feature_names = self.get_feature_names()
        if len(feature_names) == 0:
            return []

        if hasattr(tfidf_vector, 'toarray'):
            scores = tfidf_vector.toarray().flatten()
        else:
            scores = np.array(tfidf_vector).flatten()

        top_indices = scores.argsort()[-n:][::-1]
        return [(feature_names[i], float(scores[i])) for i in top_indices if scores[i] > 0]

    def save(self, path):
        """Save vectorizer and weights."""
        if HAS_JOBLIB and self.vectorizer:
            data = {
                'vectorizer': self.vectorizer,
                'delta_weights': self.delta_weights
            }
            joblib.dump(data, path)

    def load(self, path):
        """Load vectorizer and weights."""
        if HAS_JOBLIB and os.path.exists(path):
            data = joblib.load(path)
            self.vectorizer = data['vectorizer']
            self.delta_weights = data.get('delta_weights')
            return True
        return False
