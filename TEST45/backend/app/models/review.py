"""
MongoDB Models - Reviews
"""
from datetime import datetime, timezone
from bson import ObjectId


class ReviewModel:
    """MongoDB operations for review documents."""

    COLLECTION = 'reviews'

    @staticmethod
    def create_schema():
        """Return the review document schema."""
        return {
            'product_id': None,           # Reference to product
            'text': '',                    # Original review text
            'text_cleaned': '',            # Preprocessed text
            'tokens': [],                  # Tokenized words
            'rating': 0,                   # Star rating (1-5)
            'sentiment': None,             # Overall sentiment: positive/neutral/negative
            'sentiment_confidence': 0.0,   # Confidence score
            'aspects': [],                 # List of {aspect, sentiment, keywords}
            'source_platform': '',         # shopee, lazada, pantip, etc.
            'reviewer_hash': '',           # SHA-256 anonymized username (PDPA)
            'review_date': None,           # Original review date
            'scraped_at': datetime.now(timezone.utc),
            'created_at': datetime.now(timezone.utc)
        }

    @staticmethod
    def insert_many(db, reviews):
        """Insert multiple reviews."""
        if not reviews:
            return []
        result = db[ReviewModel.COLLECTION].insert_many(reviews)
        return result.inserted_ids

    @staticmethod
    def find_by_product(db, product_id, skip=0, limit=50):
        """Get reviews for a product with pagination."""
        cursor = db[ReviewModel.COLLECTION].find(
            {'product_id': ObjectId(product_id)}
        ).sort('scraped_at', -1).skip(skip).limit(limit)
        return list(cursor)

    @staticmethod
    def count_by_product(db, product_id):
        """Count reviews for a product."""
        return db[ReviewModel.COLLECTION].count_documents(
            {'product_id': ObjectId(product_id)}
        )

    @staticmethod
    def delete_by_product(db, product_id):
        """Delete all reviews for a product."""
        result = db[ReviewModel.COLLECTION].delete_many(
            {'product_id': ObjectId(product_id)}
        )
        return result.deleted_count

    @staticmethod
    def get_sentiment_distribution(db, product_id):
        """Get sentiment count distribution for a product."""
        pipeline = [
            {'$match': {'product_id': ObjectId(product_id)}},
            {'$group': {
                '_id': '$sentiment',
                'count': {'$sum': 1}
            }}
        ]
        result = db[ReviewModel.COLLECTION].aggregate(pipeline)
        return {item['_id']: item['count'] for item in result if item['_id']}
