"""
MongoDB Models - Products
"""
from datetime import datetime, timezone
from bson import ObjectId


class ProductModel:
    """MongoDB operations for product documents."""

    COLLECTION = 'products'

    @staticmethod
    def create_schema():
        """Return the product document schema."""
        return {
            'name': '',
            'url': '',
            'platform': '',          # shopee, lazada, pantip
            'category': '',
            'image_url': '',
            'price': None,
            'total_reviews': 0,
            'average_rating': 0.0,
            'summary_stats': {
                'positive': 0,
                'neutral': 0,
                'negative': 0,
                'aspects': {}        # {aspect_name: {positive, neutral, negative}}
            },
            'scrape_status': 'pending',  # pending, scraping, completed, failed
            'last_scraped_at': None,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }

    @staticmethod
    def insert(db, product):
        """Insert a new product."""
        result = db[ProductModel.COLLECTION].insert_one(product)
        return str(result.inserted_id)

    @staticmethod
    def find_all(db, skip=0, limit=20):
        """Get all products with pagination."""
        cursor = db[ProductModel.COLLECTION].find().sort(
            'created_at', -1
        ).skip(skip).limit(limit)
        products = []
        for p in cursor:
            p['_id'] = str(p['_id'])
            products.append(p)
        return products

    @staticmethod
    def find_by_id(db, product_id):
        """Get a product by ID."""
        product = db[ProductModel.COLLECTION].find_one(
            {'_id': ObjectId(product_id)}
        )
        if product:
            product['_id'] = str(product['_id'])
        return product

    @staticmethod
    def update(db, product_id, update_data):
        """Update a product."""
        update_data['updated_at'] = datetime.now(timezone.utc)
        result = db[ProductModel.COLLECTION].update_one(
            {'_id': ObjectId(product_id)},
            {'$set': update_data}
        )
        return result.modified_count

    @staticmethod
    def delete(db, product_id):
        """Delete a product."""
        result = db[ProductModel.COLLECTION].delete_one(
            {'_id': ObjectId(product_id)}
        )
        return result.deleted_count

    @staticmethod
    def find_by_url(db, url):
        """Find product by URL."""
        product = db[ProductModel.COLLECTION].find_one({'url': url})
        if product:
            product['_id'] = str(product['_id'])
        return product
