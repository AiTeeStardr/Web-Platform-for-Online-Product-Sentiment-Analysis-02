import axios from 'axios';

const API_BASE = 'https://web-platform-for-online-product.onrender.com/api';

const api = axios.create({
    baseURL: API_BASE,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// === Products ===
export const getProducts = (page = 1, limit = 20) =>
    api.get(`/products?page=${page}&limit=${limit}`).then(res => res.data);

export const getProduct = (id) =>
    api.get(`/products/${id}`).then(res => res.data);

export const deleteProduct = (id) =>
    api.delete(`/products/${id}`).then(res => res.data);

// === Scraping ===
export const startScraping = (data) =>
    api.post('/scrape', data).then(res => res.data);

export const getScrapeStatus = (taskId) =>
    api.get(`/scrape/status/${taskId}`).then(res => res.data);

// === Analysis ===
export const startAnalysis = (productId) =>
    api.post(`/analyze/${productId}`).then(res => res.data);

export const getAnalysis = (productId) =>
    api.get(`/analysis/${productId}`).then(res => res.data);

export const getAspectAnalysis = (productId) =>
    api.get(`/analysis/${productId}/aspects`).then(res => res.data);

export const getAnalysisStatus = (analysisId) =>
    api.get(`/analysis/status/${analysisId}`).then(res => res.data);

export default api;
