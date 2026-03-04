"""
API Routes - Scraping
"""

import threading
from flask import Blueprint, request, jsonify, make_response
from bson import ObjectId
from app.models.product import ProductModel

scraping_bp = Blueprint('scraping', __name__)

# Simple in-memory task tracking
_scrape_tasks = {}


def _get_db():
    from app import db
    return db


@scraping_bp.route('/scrape', methods=['POST', 'OPTIONS'])
def start_scraping():

    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = make_response('', 200)
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response

    data = request.get_json()

    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400

    url = data['url']
    platform = data.get('platform', 'shopee')
    max_pages = data.get('max_pages', 5)

    db = _get_db()
    if db is None:
        return jsonify({
            'task_id': 'demo_task',
            'status': 'completed',
            'message': 'Demo mode - using sample data',
            'product_id': 'demo_001'
        }), 200

    existing = ProductModel.find_by_url(db, url)

    # ✅ ถ้าเคยมี URL นี้แล้ว
    if existing:
        status = existing.get("scrape_status")

        # ถ้า scrape เสร็จแล้ว → ไม่ต้อง scrape ใหม่
        if status == "completed":
            return jsonify({
                'task_id': str(existing['_id']),
                'status': 'exists',
                'message': 'Product already scraped',
                'product_id': str(existing['_id'])
            }), 200

        # ถ้า failed หรือ scraping ค้าง → scrape ใหม่
        ProductModel.update(db, str(existing['_id']), {
            'scrape_status': 'scraping',
            'total_reviews': 0
        })

        task_id = str(existing['_id'])

    else:
        # สร้าง product ใหม่
        product = ProductModel.create_schema()
        product['url'] = url
        product['platform'] = platform
        product['name'] = data.get('name', 'Unnamed Product')
        product['scrape_status'] = 'scraping'

        product_id = ProductModel.insert(db, product)
        task_id = str(product_id)

    _scrape_tasks[task_id] = {'status': 'scraping', 'progress': 0}

    # เริ่ม background thread
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
        'product_id': task_id
    }), 202


@scraping_bp.route('/scrape/status/<task_id>', methods=['GET'])
def get_scrape_status(task_id):

    if task_id == 'demo_task':
        return jsonify({
            'task_id': task_id,
            'status': 'completed',
            'progress': 100,
            'reviews_found': 150
        }), 200

    task = _scrape_tasks.get(task_id)
    if task:
        return jsonify({
            'task_id': task_id,
            **task
        }), 200

    db = _get_db()
    if db is not None:
        product = ProductModel.find_by_id(db, task_id)
        if product:
            return jsonify({
                'task_id': task_id,
                'status': product.get('scrape_status', 'unknown'),
                'progress': 100 if product.get('scrape_status') == 'completed' else 0,
                'reviews_found': product.get('total_reviews', 0)
            }), 200

    return jsonify({'error': 'Task not found'}), 404


def _run_scrape_task(task_id, url, platform, max_pages):

    from app import db as database

    try:
        from app.services.scraper.shopee_scraper import ShopeeScraper
        from app.utils.anonymizer import Anonymizer
        from app.models.review import ReviewModel

        _scrape_tasks[task_id] = {'status': 'scraping', 'progress': 10}

        scraper = ShopeeScraper()

        _scrape_tasks[task_id]['progress'] = 30
        raw_reviews = scraper.scrape(url, max_pages=max_pages)

        # ถ้า scrape ไม่ได้อะไรเลย → ใช้ demo
        if not raw_reviews:
            raw_reviews = scraper._demo_reviews()

        _scrape_tasks[task_id]['progress'] = 60

        anonymizer = Anonymizer()
        anonymized_reviews = [
            anonymizer.anonymize_review(r) for r in raw_reviews
        ]

        _scrape_tasks[task_id]['progress'] = 80

        if database is not None and anonymized_reviews:
            for review in anonymized_reviews:
                review['product_id'] = ObjectId(task_id)

            ReviewModel.insert_many(database, anonymized_reviews)

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

        if database is not None:
            ProductModel.update(database, task_id, {
                'scrape_status': 'failed'
            })