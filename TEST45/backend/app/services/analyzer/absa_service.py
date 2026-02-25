"""
ABSA Service - Aspect-Based Sentiment Analysis Orchestrator
Combines aspect extraction with per-aspect sentiment analysis.
"""
from collections import Counter
from app.services.nlp.preprocessor import TextPreprocessor
from app.services.analyzer.aspect_extractor import AspectExtractor
from app.services.analyzer.sentiment_model import SentimentModel


class ABSAService:
    """
    Orchestrates the Aspect-Based Sentiment Analysis pipeline:
    1. Preprocess text
    2. Extract aspects
    3. Classify sentiment per aspect
    4. Aggregate results
    """

    def __init__(self, model_path=None):
        self.preprocessor = TextPreprocessor()
        self.aspect_extractor = AspectExtractor()
        self.sentiment_model = SentimentModel(model_path=model_path)

    def analyze(self, original_text, preprocessed=None):
        """
        Analyze a single review text.

        Args:
            original_text: Raw review text
            preprocessed: Optional pre-processed result dict

        Returns:
            dict: {
                'overall_sentiment': str,
                'confidence': float,
                'aspects': [{aspect, sentiment, confidence, keywords}],
                'tokens': list
            }
        """
        # Step 1: Preprocess if not already done
        if preprocessed is None:
            preprocessed = self.preprocessor.preprocess(original_text)

        tokens = preprocessed['tokens']

        # Step 2: Overall sentiment
        overall = self.sentiment_model.predict_from_text(tokens)

        # Step 3: Extract aspects
        aspect_results = self.aspect_extractor.extract_aspects(tokens)

        # Step 4: Per-aspect sentiment
        analyzed_aspects = []
        for aspect_info in aspect_results:
            context_tokens = aspect_info['context_tokens']

            # Predict sentiment for the aspect's context
            aspect_sentiment = self.sentiment_model.predict_from_text(context_tokens)

            analyzed_aspects.append({
                'aspect': aspect_info['aspect'],
                'sentiment': aspect_sentiment['label'],
                'confidence': aspect_sentiment['confidence'],
                'keywords': aspect_info['keywords_found']
            })

        return {
            'overall_sentiment': overall['label'],
            'confidence': overall['confidence'],
            'probabilities': overall['probabilities'],
            'aspects': analyzed_aspects,
            'tokens': tokens
        }

    def analyze_batch(self, texts):
        """Analyze multiple review texts."""
        return [self.analyze(text) for text in texts]

    def aggregate_results(self, results):
        """
        Aggregate analysis results from multiple reviews.

        Args:
            results: List of analysis results from analyze()

        Returns:
            dict: Aggregated statistics
        """
        if not results:
            return self._empty_aggregation()

        # Overall sentiment counts
        overall_counts = Counter()
        aspect_counts = {}
        all_tokens = []
        sample_positive = []
        sample_negative = []

        for result in results:
            sentiment = result.get('overall_sentiment', 'neutral')
            overall_counts[sentiment] += 1
            all_tokens.extend(result.get('tokens', []))

            # Aggregate aspects
            for aspect_info in result.get('aspects', []):
                aspect = aspect_info['aspect']
                if aspect not in aspect_counts:
                    aspect_counts[aspect] = {
                        'positive': 0, 'neutral': 0, 'negative': 0,
                        'keywords': []
                    }
                aspect_counts[aspect][aspect_info['sentiment']] += 1
                aspect_counts[aspect]['keywords'].extend(aspect_info.get('keywords', []))

        # Calculate aspect scores
        aspect_sentiments = {}
        for aspect, counts in aspect_counts.items():
            total = counts['positive'] + counts['neutral'] + counts['negative']
            score = counts['positive'] / total if total > 0 else 0.5

            # Deduplicate and limit keywords
            unique_keywords = list(set(counts['keywords']))[:10]

            aspect_sentiments[aspect] = {
                'positive': counts['positive'],
                'neutral': counts['neutral'],
                'negative': counts['negative'],
                'total': total,
                'score': round(score, 2),
                'keywords': unique_keywords
            }

        # Word cloud data
        word_freq = Counter(all_tokens)
        word_cloud_data = [
            {'word': word, 'frequency': freq}
            for word, freq in word_freq.most_common(50)
        ]

        # Top keywords by sentiment
        positive_tokens = []
        negative_tokens = []
        for result in results:
            if result.get('overall_sentiment') == 'positive':
                positive_tokens.extend(result.get('tokens', []))
            elif result.get('overall_sentiment') == 'negative':
                negative_tokens.extend(result.get('tokens', []))

        top_positive = [w for w, _ in Counter(positive_tokens).most_common(10)]
        top_negative = [w for w, _ in Counter(negative_tokens).most_common(10)]

        total = sum(overall_counts.values())
        return {
            'overall_sentiment': {
                'positive': overall_counts.get('positive', 0),
                'neutral': overall_counts.get('neutral', 0),
                'negative': overall_counts.get('negative', 0),
                'total': total
            },
            'aspect_sentiments': aspect_sentiments,
            'word_cloud_data': word_cloud_data,
            'top_positive_keywords': top_positive,
            'top_negative_keywords': top_negative,
            'sample_reviews': {
                'positive': sample_positive[:5],
                'negative': sample_negative[:5]
            }
        }

    def _empty_aggregation(self):
        """Return empty aggregation structure."""
        return {
            'overall_sentiment': {
                'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0
            },
            'aspect_sentiments': {},
            'word_cloud_data': [],
            'top_positive_keywords': [],
            'top_negative_keywords': [],
            'sample_reviews': {'positive': [], 'negative': []}
        }
