"""
API Routes - Products
"""
from flask import Blueprint, request, jsonify
from bson import ObjectId
from app.models.product import ProductModel
from app.models.review import ReviewModel
from app.models.analysis import AnalysisModel

products_bp = Blueprint('products', __name__)


def _get_db():
    """Get database instance."""
    from app import db
    return db


@products_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products with pagination."""
    db = _get_db()
    if db is None:
        return jsonify(_demo_products()), 200

    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    skip = (page - 1) * limit

    products = ProductModel.find_all(db, skip=skip, limit=limit)

    # Add review counts
    for p in products:
        p['total_reviews'] = ReviewModel.count_by_product(db, p['_id'])

    return jsonify({
        'products': products,
        'page': page,
        'limit': limit
    }), 200


@products_bp.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get a single product by ID."""
    db = _get_db()
    if db is None:
        return jsonify(_demo_product_detail()), 200

    try:
        product = ProductModel.find_by_id(db, product_id)
    except Exception:
        return jsonify({'error': 'Invalid product ID'}), 400

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Include reviews
    reviews = ReviewModel.find_by_product(db, product_id, limit=10)
    for r in reviews:
        r['_id'] = str(r['_id'])
        r['product_id'] = str(r['product_id'])

    product['recent_reviews'] = reviews
    return jsonify(product), 200


@products_bp.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product and all its data."""
    db = _get_db()
    if db is None:
        return jsonify({'message': 'Demo mode - no data to delete'}), 200

    try:
        # Delete reviews, analyses, then product
        ReviewModel.delete_by_product(db, product_id)
        AnalysisModel.delete_by_product(db, product_id)
        deleted = ProductModel.delete(db, product_id)
    except Exception:
        return jsonify({'error': 'Invalid product ID'}), 400

    if deleted == 0:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify({'message': 'Product deleted successfully'}), 200


def _demo_products():
    """Demo data when DB is unavailable."""
    return {
        'products': [
            {
                '_id': 'demo_001',
                'name': 'Samsung Galaxy S24 Ultra',
                'platform': 'shopee',
                'category': 'smartphone',
                'total_reviews': 150,
                'average_rating': 4.2,
                'summary_stats': {
                    'positive': 95, 'neutral': 30, 'negative': 25,
                    'aspects': {
                        'camera': {'positive': 40, 'neutral': 8, 'negative': 5},
                        'battery': {'positive': 30, 'neutral': 10, 'negative': 12},
                        'price': {'positive': 10, 'neutral': 5, 'negative': 20}
                    }
                },
                'scrape_status': 'completed'
            },
            {
                '_id': 'demo_002',
                'name': 'iPhone 16 Pro Max',
                'platform': 'shopee',
                'category': 'smartphone',
                'total_reviews': 200,
                'average_rating': 4.5,
                'summary_stats': {
                    'positive': 140, 'neutral': 35, 'negative': 25,
                    'aspects': {
                        'camera': {'positive': 55, 'neutral': 5, 'negative': 3},
                        'battery': {'positive': 35, 'neutral': 15, 'negative': 8},
                        'price': {'positive': 5, 'neutral': 10, 'negative': 30}
                    }
                },
                'scrape_status': 'completed'
            }
        ],
        'page': 1,
        'limit': 20
    }


def _demo_product_detail():
    """Demo product detail."""
    return {
        '_id': 'demo_001',
        'name': 'Samsung Galaxy S24 Ultra',
        'platform': 'shopee',
        'category': 'smartphone',
        'total_reviews': 150,
        'average_rating': 4.2,
        'summary_stats': {
            'positive': 95, 'neutral': 30, 'negative': 25,
            'aspects': {}
        },
        'recent_reviews': [
            {
                '_id': 'rev_001', 'text': 'กล้องถ่ายรูปสวยมาก ชอบมาก',
                'rating': 5, 'sentiment': 'positive',
                'aspects': [{'aspect': 'camera', 'sentiment': 'positive'}]
            },
            {
                '_id': 'rev_002', 'text': 'แบตหมดเร็วมาก ใช้ไม่ถึงครึ่งวัน',
                'rating': 2, 'sentiment': 'negative',
                'aspects': [{'aspect': 'battery', 'sentiment': 'negative'}]
            }
        ]
    }
