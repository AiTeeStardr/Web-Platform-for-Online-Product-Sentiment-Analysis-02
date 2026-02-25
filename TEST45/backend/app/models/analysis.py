"""
MongoDB Models - Analysis Results
"""
from datetime import datetime, timezone
from bson import ObjectId


class AnalysisModel:
    """MongoDB operations for analysis result documents."""

    COLLECTION = 'analyses'

    @staticmethod
    def create_schema():
        """Return the analysis document schema."""
        return {
            'product_id': None,
            'overall_sentiment': {
                'positive': 0,
                'neutral': 0,
                'negative': 0,
                'total': 0
            },
            'aspect_sentiments': {},    # {aspect: {positive, neutral, negative, keywords}}
            'word_cloud_data': [],      # [{word, frequency}]
            'sentiment_trend': [],      # [{date, positive, neutral, negative}]
            'top_positive_keywords': [],
            'top_negative_keywords': [],
            'sample_reviews': {
                'positive': [],
                'negative': []
            },
            'model_used': 'svm',        # svm or wangchanberta
            'analysis_status': 'pending',  # pending, processing, completed, failed
            'created_at': datetime.now(timezone.utc),
            'completed_at': None
        }

    @staticmethod
    def insert(db, analysis):
        """Insert a new analysis."""
        result = db[AnalysisModel.COLLECTION].insert_one(analysis)
        return str(result.inserted_id)

    @staticmethod
    def find_by_product(db, product_id):
        """Get latest analysis for a product."""
        analysis = db[AnalysisModel.COLLECTION].find_one(
            {'product_id': ObjectId(product_id)},
            sort=[('created_at', -1)]
        )
        if analysis:
            analysis['_id'] = str(analysis['_id'])
            analysis['product_id'] = str(analysis['product_id'])
        return analysis

    @staticmethod
    def update(db, analysis_id, update_data):
        """Update an analysis."""
        result = db[AnalysisModel.COLLECTION].update_one(
            {'_id': ObjectId(analysis_id)},
            {'$set': update_data}
        )
        return result.modified_count

    @staticmethod
    def delete_by_product(db, product_id):
        """Delete analyses for a product."""
        result = db[AnalysisModel.COLLECTION].delete_many(
            {'product_id': ObjectId(product_id)}
        )
        return result.deleted_count
