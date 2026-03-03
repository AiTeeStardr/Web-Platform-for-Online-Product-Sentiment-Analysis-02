"""
API Routes - Scraping
"""
import threading
from flask import Blueprint, request, jsonify
from bson import ObjectId
from app.models.product import ProductModel

scraping_bp = Blueprint('scraping', __name__)

# Simple in-memory task tracking
_scrape_tasks = {}


def _get_db():
    from app import db
    return db


@scraping_bp.route('/scrape', methods=['POST','OPTIONS'])
def start_scraping():
    
    if request.method == 'OPTIONS':
        response = make_response('', 200)
        # เปิดให้ทุก Domain และทุก Header เข้าถึงได้
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response
    
    """Start a new scraping task."""
    data = request.get_json()

    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400

    url = data['url']
    platform = data.get('platform', 'shopee')
    max_pages = data.get('max_pages', 5)

    db = _get_db()
    if db is None:
        # Demo mode
        return jsonify({
            'task_id': 'demo_task',
            'status': 'completed',
            'message': 'Demo mode - using sample data',
            'product_id': 'demo_001'
        }), 200

    # Check if product already exists
    existing = ProductModel.find_by_url(db, url)
    if existing:
        return jsonify({
            'task_id': existing['_id'],
            'status': 'exists',
            'message': 'Product already scraped',
            'product_id': existing['_id']
        }), 200

    # Create product entry
    product = ProductModel.create_schema()
    product['url'] = url
    product['platform'] = platform
    product['name'] = data.get('name', 'Unnamed Product')
    product['scrape_status'] = 'scraping'
    product_id = ProductModel.insert(db, product)

    # Start scraping in background
    task_id = product_id
    _scrape_tasks[task_id] = {'status': 'scraping', 'progress': 0}

    thread = threading.Thread(
        target=_run_scrape_task,
        args=(task_id, url, platform, max_pages)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'task_id': task_id,
        'status': 'scraping',
        'message': f'Scraping started for {platform}',
        'product_id': product_id
    }), 202


@scraping_bp.route('/scrape/status/<task_id>', methods=['GET'])
def get_scrape_status(task_id):
    """Check scraping task status."""
    if task_id == 'demo_task':
        return jsonify({
            'task_id': task_id,
            'status': 'completed',
            'progress': 100,
            'reviews_found': 150
        }), 200

    task = _scrape_tasks.get(task_id)
    if not task:
        # Check DB for product status
        db = _get_db()
        if db:
            product = ProductModel.find_by_id(db, task_id)
            if product:
                return jsonify({
                    'task_id': task_id,
                    'status': product.get('scrape_status', 'unknown'),
                    'progress': 100 if product.get('scrape_status') == 'completed' else 0,
                    'reviews_found': product.get('total_reviews', 0)
                }), 200

        return jsonify({'error': 'Task not found'}), 404

    return jsonify({
        'task_id': task_id,
        **task
    }), 200


def _run_scrape_task(task_id, url, platform, max_pages):
    """Background scraping task."""
    from app import create_app
    app = create_app()

    with app.app_context():
        try:
            from app import db as database
            from app.services.scraper.shopee_scraper import ShopeeScraper
            from app.utils.anonymizer import Anonymizer

            _scrape_tasks[task_id] = {'status': 'scraping', 'progress': 10}

            # Select scraper based on platform
            if platform == 'shopee':
                scraper = ShopeeScraper()
            else:
                scraper = ShopeeScraper()  # Default fallback

            # Execute scraping
            _scrape_tasks[task_id]['progress'] = 20
            raw_reviews = scraper.scrape(url, max_pages=max_pages)

            _scrape_tasks[task_id]['progress'] = 60

            # Anonymize data (PDPA compliance)
            anonymizer = Anonymizer()
            anonymized_reviews = [anonymizer.anonymize_review(r) for r in raw_reviews]

            _scrape_tasks[task_id]['progress'] = 80

            # Store in MongoDB
            if database and anonymized_reviews:
                from app.models.review import ReviewModel
                for review in anonymized_reviews:
                    review['product_id'] = ObjectId(task_id)
                ReviewModel.insert_many(database, anonymized_reviews)

                # Update product
                ProductModel.update(database, task_id, {
                    'scrape_status': 'completed',
                    'total_reviews': len(anonymized_reviews)
                })

            _scrape_tasks[task_id] = {
                'status': 'completed',
                'progress': 100,
                'reviews_found': len(anonymized_reviews)
            }

        except Exception as e:
            _scrape_tasks[task_id] = {
                'status': 'failed',
                'progress': 0,
                'error': str(e)
            }
            if database:
                ProductModel.update(database, task_id, {'scrape_status': 'failed'})
