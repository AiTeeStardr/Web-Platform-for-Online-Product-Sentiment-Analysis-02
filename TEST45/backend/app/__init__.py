"""
Flask Application Factory
เว็บแพลตฟอร์มวิเคราะห์ความคิดเห็นสินค้าออนไลน์
"""
from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient
from app.config import Config

# Global MongoDB client
mongo_client = None
db = None


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for React frontend
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Initialize MongoDB
    _init_db(app)

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    return app


def _init_db(app):
    """Initialize MongoDB connection."""
    global mongo_client, db
    try:
        mongo_client = MongoClient(app.config['MONGO_URI'], serverSelectionTimeoutMS=5000)
        # Test connection
        mongo_client.admin.command('ping')
        db = mongo_client[app.config['MONGO_DB_NAME']]
        app.logger.info(f"✅ Connected to MongoDB: {app.config['MONGO_DB_NAME']}")
    except Exception as e:
        app.logger.warning(f"⚠️ MongoDB connection failed: {e}. Running in demo mode.")
        db = None


def _register_blueprints(app):
    """Register all API blueprints."""
    from app.routes.products import products_bp
    from app.routes.scraping import scraping_bp
    from app.routes.analysis import analysis_bp

    app.register_blueprint(products_bp, url_prefix='/api')
    app.register_blueprint(scraping_bp, url_prefix='/api')
    app.register_blueprint(analysis_bp, url_prefix='/api')


def _register_error_handlers(app):
    """Register global error handlers."""
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
