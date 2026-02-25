# SentimentScope — เว็บแพลตฟอร์มวิเคราะห์ความคิดเห็นสินค้าออนไลน์

Web Platform for Online Product Sentiment Analysis with ABSA for Thai language.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React + Vite |
| Backend | Flask (Python) |
| Database | MongoDB |
| AI/NLP | SVM + Delta TF-IDF + PyThaiNLP |
| Scraping | Selenium (Headless Chrome) |

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python run.py
```
Server runs at `http://localhost:5000`

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Dashboard runs at `http://localhost:5173`

## Features
- 🔍 Web Scraping — Selenium scraper for Shopee
- 🧠 Thai NLP — PyThaiNLP tokenization + emoji-to-text
- 📊 ABSA — Aspect-Based Sentiment Analysis
- 📈 Dashboard — Interactive charts with Chart.js
- 🔒 PDPA — Data anonymization (SHA-256)
