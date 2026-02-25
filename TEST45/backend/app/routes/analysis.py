"""
API Routes - Analysis
"""
import threading
from flask import Blueprint, request, jsonify
from bson import ObjectId
from app.models.analysis import AnalysisModel
from app.models.product import ProductModel
from app.models.review import ReviewModel

analysis_bp = Blueprint('analysis', __name__)

# In-memory task tracking
_analysis_tasks = {}


def _get_db():
    from app import db
    return db


@analysis_bp.route('/analyze/<product_id>', methods=['POST'])
def start_analysis(product_id):
    """Start sentiment analysis for a product."""
    db = _get_db()

    if db is None:
        return jsonify(_demo_analysis_result()), 200

    # Validate product exists
    try:
        product = ProductModel.find_by_id(db, product_id)
    except Exception:
        return jsonify({'error': 'Invalid product ID'}), 400

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Create analysis record
    analysis = AnalysisModel.create_schema()
    analysis['product_id'] = ObjectId(product_id)
    analysis['analysis_status'] = 'processing'
    analysis_id = AnalysisModel.insert(db, analysis)

    _analysis_tasks[analysis_id] = {'status': 'processing', 'progress': 0}

    # Run analysis in background
    thread = threading.Thread(
        target=_run_analysis,
        args=(analysis_id, product_id)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'analysis_id': analysis_id,
        'status': 'processing',
        'message': 'Analysis started'
    }), 202


@analysis_bp.route('/analysis/<product_id>', methods=['GET'])
def get_analysis(product_id):
    """Get analysis results for a product."""
    db = _get_db()

    if db is None:
        return jsonify(_demo_analysis_result()), 200

    try:
        analysis = AnalysisModel.find_by_product(db, product_id)
    except Exception:
        return jsonify({'error': 'Invalid product ID'}), 400

    if not analysis:
        return jsonify({'error': 'No analysis found. Run analysis first.'}), 404

    return jsonify(analysis), 200


@analysis_bp.route('/analysis/<product_id>/aspects', methods=['GET'])
def get_aspect_analysis(product_id):
    """Get aspect-level analysis for a product."""
    db = _get_db()

    if db is None:
        return jsonify(_demo_aspect_data()), 200

    try:
        analysis = AnalysisModel.find_by_product(db, product_id)
    except Exception:
        return jsonify({'error': 'Invalid product ID'}), 400

    if not analysis:
        return jsonify({'error': 'No analysis found'}), 404

    return jsonify({
        'product_id': product_id,
        'aspects': analysis.get('aspect_sentiments', {}),
        'model_used': analysis.get('model_used', 'svm')
    }), 200


@analysis_bp.route('/analysis/status/<analysis_id>', methods=['GET'])
def get_analysis_status(analysis_id):
    """Check analysis task status."""
    task = _analysis_tasks.get(analysis_id)
    if task:
        return jsonify({'analysis_id': analysis_id, **task}), 200

    db = _get_db()
    if db:
        try:
            analysis = AnalysisModel.find_by_product(db, analysis_id)
            if analysis:
                return jsonify({
                    'analysis_id': analysis_id,
                    'status': analysis.get('analysis_status', 'unknown'),
                    'progress': 100 if analysis.get('analysis_status') == 'completed' else 0
                }), 200
        except Exception:
            pass

    return jsonify({'error': 'Analysis not found'}), 404


def _run_analysis(analysis_id, product_id):
    """Background analysis task."""
    from app import create_app
    app = create_app()

    with app.app_context():
        try:
            from app import db as database
            from app.services.nlp.preprocessor import TextPreprocessor
            from app.services.nlp.feature_extractor import FeatureExtractor
            from app.services.analyzer.sentiment_model import SentimentModel
            from app.services.analyzer.aspect_extractor import AspectExtractor
            from app.services.analyzer.absa_service import ABSAService
            from datetime import datetime, timezone

            _analysis_tasks[analysis_id] = {'status': 'processing', 'progress': 10}

            # Get reviews
            reviews = ReviewModel.find_by_product(database, product_id, limit=1000)
            if not reviews:
                _analysis_tasks[analysis_id] = {'status': 'failed', 'error': 'No reviews found'}
                return

            _analysis_tasks[analysis_id]['progress'] = 20

            # Initialize pipeline
            preprocessor = TextPreprocessor()
            absa_service = ABSAService()

            # Process reviews
            processed_reviews = []
            for i, review in enumerate(reviews):
                text = review.get('text', '')
                if not text:
                    continue

                # Preprocess
                cleaned = preprocessor.preprocess(text)

                # ABSA
                result = absa_service.analyze(text, cleaned)

                # Update review in DB
                ReviewModel_update = {
                    'text_cleaned': cleaned['cleaned_text'],
                    'tokens': cleaned['tokens'],
                    'sentiment': result['overall_sentiment'],
                    'sentiment_confidence': result['confidence'],
                    'aspects': result['aspects']
                }
                if database:
                    database['reviews'].update_one(
                        {'_id': review['_id']},
                        {'$set': ReviewModel_update}
                    )

                processed_reviews.append(result)

                # Update progress
                progress = 20 + int((i / len(reviews)) * 60)
                _analysis_tasks[analysis_id]['progress'] = min(progress, 80)

            _analysis_tasks[analysis_id]['progress'] = 85

            # Aggregate results
            aggregated = absa_service.aggregate_results(processed_reviews)

            _analysis_tasks[analysis_id]['progress'] = 95

            # Save analysis
            if database:
                AnalysisModel.update(database, analysis_id, {
                    'overall_sentiment': aggregated['overall_sentiment'],
                    'aspect_sentiments': aggregated['aspect_sentiments'],
                    'word_cloud_data': aggregated.get('word_cloud_data', []),
                    'top_positive_keywords': aggregated.get('top_positive_keywords', []),
                    'top_negative_keywords': aggregated.get('top_negative_keywords', []),
                    'sample_reviews': aggregated.get('sample_reviews', {}),
                    'analysis_status': 'completed',
                    'completed_at': datetime.now(timezone.utc)
                })

                # Update product summary
                ProductModel.update(database, product_id, {
                    'summary_stats': aggregated['overall_sentiment']
                })

            _analysis_tasks[analysis_id] = {'status': 'completed', 'progress': 100}

        except Exception as e:
            _analysis_tasks[analysis_id] = {
                'status': 'failed',
                'progress': 0,
                'error': str(e)
            }


def _demo_analysis_result():
    """Demo analysis data."""
    return {
        '_id': 'demo_analysis_001',
        'product_id': 'demo_001',
        'product_name': 'Samsung Galaxy S24 Ultra',
        'platform': 'shopee',
        'overall_sentiment': {
            'positive': 95, 'neutral': 30, 'negative': 25, 'total': 150
        },
        'aspect_sentiments': {
            'camera': {
                'positive': 40, 'neutral': 8, 'negative': 5,
                'score': 0.75,
                'keywords': ['กล้องสวย', 'ถ่ายรูปชัด', 'ซูมไกล']
            },
            'battery': {
                'positive': 30, 'neutral': 10, 'negative': 12,
                'score': 0.58,
                'keywords': ['แบตอึด', 'ชาร์จเร็ว', 'แบตหมดเร็ว']
            },
            'screen': {
                'positive': 35, 'neutral': 5, 'negative': 3,
                'score': 0.81,
                'keywords': ['จอสวย', 'สีสด', 'จอใหญ่']
            },
            'price': {
                'positive': 10, 'neutral': 5, 'negative': 20,
                'score': 0.29,
                'keywords': ['แพง', 'ไม่คุ้ม', 'ราคาสูง']
            },
            'design': {
                'positive': 28, 'neutral': 7, 'negative': 4,
                'score': 0.72,
                'keywords': ['สวย', 'ดีไซน์ดี', 'พรีเมียม']
            },
            'performance': {
                'positive': 32, 'neutral': 8, 'negative': 6,
                'score': 0.70,
                'keywords': ['เร็ว', 'ลื่น', 'แรง']
            },
            'service': {
                'positive': 15, 'neutral': 10, 'negative': 8,
                'score': 0.45,
                'keywords': ['ส่งเร็ว', 'บริการดี', 'ส่งช้า']
            }
        },
        'word_cloud_data': [
            {'word': 'กล้อง', 'frequency': 45},
            {'word': 'สวย', 'frequency': 38},
            {'word': 'แบต', 'frequency': 35},
            {'word': 'จอ', 'frequency': 30},
            {'word': 'แพง', 'frequency': 28},
            {'word': 'เร็ว', 'frequency': 25},
            {'word': 'ถ่ายรูป', 'frequency': 22},
            {'word': 'ดี', 'frequency': 42},
            {'word': 'ชอบ', 'frequency': 35},
            {'word': 'คุ้มค่า', 'frequency': 15}
        ],
        'top_positive_keywords': ['กล้องสวย', 'จอสวย', 'ลื่น', 'ชาร์จเร็ว', 'ดีไซน์ดี'],
        'top_negative_keywords': ['แพง', 'แบตหมดเร็ว', 'ส่งช้า', 'ไม่คุ้ม', 'ร้อน'],
        'sample_reviews': {
            'positive': [
                {'text': 'กล้องถ่ายรูปสวยมาก คมชัดทุกมุม ชอบมาก ๆ เลย', 'rating': 5},
                {'text': 'จอ AMOLED สีสดใส ดูคอนเทนต์สนุก', 'rating': 5}
            ],
            'negative': [
                {'text': 'ราคาแพงมาก ไม่คุ้มค่าเลย', 'rating': 2},
                {'text': 'แบตหมดเร็ว ใช้ไม่ถึงครึ่งวัน ต้องพกแบตสำรองตลอด', 'rating': 1}
            ]
        },
        'model_used': 'svm',
        'analysis_status': 'completed'
    }


def _demo_aspect_data():
    """Demo aspect data."""
    demo = _demo_analysis_result()
    return {
        'product_id': 'demo_001',
        'aspects': demo['aspect_sentiments'],
        'model_used': 'svm'
    }
