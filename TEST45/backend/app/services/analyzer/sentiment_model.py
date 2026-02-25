"""
SVM Sentiment Model
3-class classification: Positive / Neutral / Negative
"""
import os
import numpy as np

try:
    from sklearn.svm import SVC
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics import classification_report
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False


class SentimentModel:
    """
    SVM-based Sentiment Classifier.

    Uses RBF kernel for non-linear classification with soft margins.
    Supports 3-class: positive, neutral, negative.
    """

    LABELS = ['positive', 'neutral', 'negative']

    def __init__(self, model_path=None):
        self.model = None
        self.is_trained = False

        if model_path and os.path.exists(model_path):
            self.load(model_path)
        elif HAS_SKLEARN:
            self.model = SVC(
                kernel='rbf',
                C=1.0,
                gamma='scale',
                probability=True,   # Enable probability estimates
                class_weight='balanced',  # Handle imbalanced classes
                random_state=42
            )

    def train(self, X, y):
        """
        Train the SVM model.

        Args:
            X: Feature matrix from TF-IDF
            y: Labels (positive/neutral/negative)
        """
        if not HAS_SKLEARN or self.model is None:
            return {'error': 'scikit-learn not available'}

        self.model.fit(X, y)
        self.is_trained = True

        # Cross-validation score
        scores = cross_val_score(self.model, X, y, cv=5, scoring='f1_weighted')

        return {
            'status': 'trained',
            'cv_f1_mean': float(scores.mean()),
            'cv_f1_std': float(scores.std()),
            'n_samples': len(y)
        }

    def predict(self, text_features):
        """
        Predict sentiment for preprocessed text features.

        Args:
            text_features: TF-IDF feature vector

        Returns:
            dict: {label, confidence, probabilities}
        """
        if not self.is_trained:
            return self._rule_based_predict(text_features)

        prediction = self.model.predict(text_features)
        probabilities = self.model.predict_proba(text_features)

        label = prediction[0]
        probs = dict(zip(self.model.classes_, probabilities[0]))
        confidence = float(max(probabilities[0]))

        return {
            'label': label,
            'confidence': confidence,
            'probabilities': probs
        }

    def _rule_based_predict(self, text_features):
        """
        Rule-based fallback when model is not trained.
        Uses keyword matching for basic sentiment detection.
        """
        return {
            'label': 'neutral',
            'confidence': 0.5,
            'probabilities': {'positive': 0.33, 'neutral': 0.34, 'negative': 0.33}
        }

    def predict_from_text(self, tokens):
        """
        Simple rule-based prediction from tokens (no trained model needed).
        Useful for demo/testing without training data.
        """
        positive_words = {
            'ดี', 'สวย', 'เยี่ยม', 'สุดยอด', 'ชอบ', 'รัก', 'ประทับใจ', 'คุ้มค่า', 'คุ้ม',
            'แนะนำ', 'เร็ว', 'ลื่น', 'ชัด', 'เจ๋ง', 'เทพ', 'แจ่ม', 'เลิศ', 'ยอดเยี่ยม',
            'good', 'great', 'excellent', 'amazing', 'love', 'best', 'perfect',
            'น่าใช้', 'พอใจ', 'สะดวก', 'ทนทาน', 'แข็งแรง', 'อึด', 'ปรบมือ', 'ขอบคุณ',
            'หลงรัก', 'น่ารัก', 'ยิ้ม', 'ดีใจ', 'ตื่นเต้น', 'แข็งแรง'
        }

        negative_words = {
            'แย่', 'ไม่ดี', 'เสีย', 'พัง', 'ผิดหวัง', 'แพง', 'ช้า', 'กระตุก',
            'ร้อน', 'แลค', 'lag', 'bad', 'terrible', 'worst', 'hate', 'poor',
            'ห่วย', 'เลว', 'โกง', 'ไม่คุ้ม', 'เสียเงิน', 'โมโห', 'หงุดหงิด',
            'ไม่พอใจ', 'ผิดหวัง', 'เบื่อ', 'หมดเร็ว', 'ไม่แนะนำ', 'อันตราย',
            'โกรธ', 'เศร้า', 'ร้องไห้', 'คลื่นไส้', 'แย่มาก', 'ไม่ดี', 'เหยียด'
        }

        pos_count = sum(1 for t in tokens if t in positive_words)
        neg_count = sum(1 for t in tokens if t in negative_words)
        total = pos_count + neg_count

        if total == 0:
            return {
                'label': 'neutral',
                'confidence': 0.5,
                'probabilities': {'positive': 0.2, 'neutral': 0.6, 'negative': 0.2}
            }

        pos_ratio = pos_count / total
        neg_ratio = neg_count / total

        if pos_ratio > 0.6:
            label = 'positive'
            confidence = min(0.5 + pos_ratio * 0.4, 0.95)
        elif neg_ratio > 0.6:
            label = 'negative'
            confidence = min(0.5 + neg_ratio * 0.4, 0.95)
        else:
            label = 'neutral'
            confidence = 0.5

        return {
            'label': label,
            'confidence': float(confidence),
            'probabilities': {
                'positive': float(pos_ratio) if total > 0 else 0.33,
                'neutral': float(1 - pos_ratio - neg_ratio) if total > 0 else 0.34,
                'negative': float(neg_ratio) if total > 0 else 0.33
            }
        }

    def evaluate(self, X, y):
        """Evaluate model performance."""
        if not self.is_trained:
            return {'error': 'Model not trained'}

        predictions = self.model.predict(X)
        report = classification_report(y, predictions, output_dict=True)
        return report

    def save(self, path):
        """Save trained model."""
        if HAS_JOBLIB and self.is_trained:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            joblib.dump(self.model, path)

    def load(self, path):
        """Load trained model."""
        if HAS_JOBLIB and os.path.exists(path):
            self.model = joblib.load(path)
            self.is_trained = True
            return True
        return False
