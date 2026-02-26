"""
Application Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    # MongoDB
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'sentiment_analysis')

    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')

    # Scraping
    SCRAPE_MAX_PAGES = int(os.environ.get('SCRAPE_MAX_PAGES', 10))
    SCRAPE_DELAY = float(os.environ.get('SCRAPE_DELAY', 2.0))  # seconds
    SELENIUM_HEADLESS = os.environ.get('SELENIUM_HEADLESS', 'True').lower() == 'true'

    # Model paths
    MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models')
    SVM_MODEL_PATH = os.path.join(MODEL_DIR, 'svm_sentiment.joblib')
    TFIDF_MODEL_PATH = os.path.join(MODEL_DIR, 'tfidf_vectorizer.joblib')

    # NLP
    THAI_TOKENIZER_ENGINE = 'newmm'

    # Predefined aspects for ABSA
    ASPECTS = {
        'camera': ['กล้อง', 'ถ่ายรูป', 'ภาพ', 'เลนส์', 'ซูม', 'โฟกัส', 'ถ่ายภาพ'],
        'battery': ['แบตเตอรี่', 'แบต', 'ชาร์จ', 'พลังงาน', 'แบตหมด', 'ชาร์จเร็ว'],
        'screen': ['หน้าจอ', 'จอ', 'ดิสเพลย์', 'สี', 'ความสว่าง', 'AMOLED', 'LCD'],
        'price': ['ราคา', 'แพง', 'ถูก', 'คุ้มค่า', 'คุ้ม', 'โปรโมชั่น', 'ส่วนลด'],
        'design': ['ดีไซน์', 'ออกแบบ', 'สวย', 'น้ำหนัก', 'บาง', 'สี', 'วัสดุ', 'ตัวเครื่อง'],
        'performance': ['ประสิทธิภาพ', 'เร็ว', 'ช้า', 'แรง', 'ลื่น', 'กระตุก', 'แลค', 'RAM', 'ชิป'],
        'service': ['บริการ', 'ส่ง', 'จัดส่ง', 'พนักงาน', 'ร้านค้า', 'ประกัน', 'ซ่อม']
    }


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
