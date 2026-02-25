import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { startScraping, getScrapeStatus } from '../services/api';

function ScrapePage() {
    const navigate = useNavigate();
    const [url, setUrl] = useState('');
    const [productName, setProductName] = useState('');
    const [platform, setPlatform] = useState('shopee');
    const [maxPages, setMaxPages] = useState(5);
    const [loading, setLoading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [status, setStatus] = useState('');
    const [error, setError] = useState('');

    // Auto-extract product name from URL
    const extractProductName = (inputUrl) => {
        try {
            const urlObj = new URL(inputUrl);
            const path = urlObj.pathname;
            // Get last meaningful path segment
            const segments = path.split('/').filter(s => s && !s.match(/^(i\.)?\d+$/));
            const slug = segments[segments.length - 1] || '';
            // Convert slug to readable name: replace hyphens/underscores, capitalize
            const name = slug
                .replace(/[-_]/g, ' ')
                .replace(/\b\w/g, c => c.toUpperCase())
                .trim();
            return name;
        } catch {
            return '';
        }
    };

    const handleUrlChange = (e) => {
        const newUrl = e.target.value;
        setUrl(newUrl);
        // Auto-fill product name if user hasn't typed one manually
        if (newUrl.length > 10) {
            const extracted = extractProductName(newUrl);
            if (extracted) {
                setProductName(extracted);
            }
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!url.trim()) {
            setError('กรุณาใส่ URL สินค้า');
            return;
        }

        setLoading(true);
        setError('');
        setStatus('กำลังเริ่ม scraping...');
        setProgress(10);

        try {
            const result = await startScraping({
                url: url.trim(),
                name: productName.trim() || 'Unnamed Product',
                platform,
                max_pages: maxPages
            });

            if (result.status === 'exists') {
                setStatus('สินค้านี้มีข้อมูลแล้ว กำลังไปหน้าวิเคราะห์...');
                setProgress(100);
                setTimeout(() => navigate(`/analysis/${result.product_id}`), 1000);
                return;
            }

            // Poll for status
            const taskId = result.task_id;
            const pollInterval = setInterval(async () => {
                try {
                    const statusResult = await getScrapeStatus(taskId);
                    setProgress(statusResult.progress || 0);

                    if (statusResult.status === 'completed') {
                        clearInterval(pollInterval);
                        setStatus(`✅ เสร็จสิ้น! พบรีวิว ${statusResult.reviews_found || 0} รายการ`);
                        setProgress(100);
                        setTimeout(() => navigate(`/analysis/${result.product_id}`), 1500);
                    } else if (statusResult.status === 'failed') {
                        clearInterval(pollInterval);
                        setError(statusResult.error || 'Scraping failed');
                        setLoading(false);
                    } else {
                        setStatus(`กำลัง scraping... (${statusResult.progress || 0}%)`);
                    }
                } catch {
                    clearInterval(pollInterval);
                    setError('เกิดข้อผิดพลาดในการตรวจสอบสถานะ');
                    setLoading(false);
                }
            }, 2000);
        } catch (err) {
            setError(err.response?.data?.error || 'เกิดข้อผิดพลาด กรุณาลองใหม่');
            setLoading(false);
        }
    };

    const handleDemo = async () => {
        setLoading(true);
        setStatus('กำลังโหลดข้อมูลตัวอย่าง...');
        setProgress(50);

        try {
            const result = await startScraping({
                url: 'https://shopee.co.th/demo-product',
                name: 'Samsung Galaxy S24 Ultra (Demo)',
                platform: 'shopee',
                max_pages: 1
            });
            setProgress(100);
            setStatus('✅ โหลดข้อมูลตัวอย่างเสร็จสิ้น!');
            setTimeout(() => navigate(`/analysis/${result.product_id || 'demo_001'}`), 1000);
        } catch {
            setProgress(100);
            setStatus('✅ โหลดข้อมูลตัวอย่างเสร็จสิ้น!');
            setTimeout(() => navigate('/analysis/demo_001'), 1000);
        }
    };

    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">🔍 เก็บข้อมูลรีวิว</h1>
                <p className="page-subtitle">ใส่ URL สินค้าเพื่อ scrape รีวิวด้วย Selenium</p>
            </div>

            <div className="grid-2">
                {/* Form */}
                <div className="glass-card">
                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label className="form-label">URL สินค้า *</label>
                            <input
                                type="url"
                                className="form-input"
                                placeholder="https://shopee.co.th/product/..."
                                value={url}
                                onChange={handleUrlChange}
                                disabled={loading}
                            />
                        </div>

                        <div className="form-group">
                            <label className="form-label">ชื่อสินค้า</label>
                            <input
                                type="text"
                                className="form-input"
                                placeholder="เช่น Samsung Galaxy S24 Ultra"
                                value={productName}
                                onChange={(e) => setProductName(e.target.value)}
                                disabled={loading}
                            />
                        </div>

                        <div className="grid-2">
                            <div className="form-group">
                                <label className="form-label">แพลตฟอร์ม</label>
                                <select className="form-select" value={platform} onChange={(e) => setPlatform(e.target.value)} disabled={loading}>
                                    <option value="shopee">Shopee</option>
                                    <option value="lazada">Lazada</option>
                                    <option value="pantip">Pantip</option>
                                </select>
                            </div>

                            <div className="form-group">
                                <label className="form-label">จำนวนหน้า (สูงสุด)</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    min="1"
                                    max="50"
                                    value={maxPages}
                                    onChange={(e) => setMaxPages(parseInt(e.target.value) || 5)}
                                    disabled={loading}
                                />
                            </div>
                        </div>

                        {error && (
                            <div style={{
                                padding: '0.75rem 1rem',
                                background: 'var(--negative-light)',
                                border: '1px solid rgba(239,68,68,0.3)',
                                borderRadius: 'var(--radius-sm)',
                                color: 'var(--negative)',
                                fontSize: '0.9rem',
                                marginBottom: '1rem'
                            }}>
                                ❌ {error}
                            </div>
                        )}

                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <button type="submit" className="btn btn-primary btn-lg" disabled={loading} style={{ flex: 1 }}>
                                {loading ? '⏳ กำลังดำเนินการ...' : '🚀 เริ่ม Scraping'}
                            </button>
                        </div>
                    </form>

                    {/* Demo button */}
                    <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                        <button className="btn btn-secondary" onClick={handleDemo} disabled={loading}>
                            📦 ใช้ข้อมูลตัวอย่าง (Demo)
                        </button>
                    </div>
                </div>

                {/* Status Panel */}
                <div className="glass-card">
                    <h3 style={{ fontWeight: 600, marginBottom: '1.5rem' }}>📋 สถานะ</h3>

                    {!loading && !status && (
                        <div className="empty-state">
                            <div className="empty-state-icon">🔗</div>
                            <p>ใส่ URL สินค้าแล้วกด "เริ่ม Scraping" เพื่อเก็บรีวิว</p>
                        </div>
                    )}

                    {loading && (
                        <div>
                            <div style={{ marginBottom: '1rem' }}>
                                <div className="progress-container">
                                    <div className="progress-bar" style={{ width: `${progress}%` }}></div>
                                </div>
                                <p style={{ marginTop: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                    {progress}%
                                </p>
                            </div>
                            <div className="spinner" style={{ margin: '1rem auto' }}></div>
                        </div>
                    )}

                    {status && (
                        <p style={{ color: status.includes('✅') ? 'var(--positive)' : 'var(--text-secondary)', fontSize: '0.95rem' }}>
                            {status}
                        </p>
                    )}

                    {/* Info */}
                    <div style={{ marginTop: '2rem', padding: '1rem', background: 'rgba(99,102,241,0.08)', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        <strong style={{ color: 'var(--accent-primary)' }}>ℹ️ หมายเหตุ:</strong>
                        <ul style={{ marginTop: '0.5rem', paddingLeft: '1.2rem' }}>
                            <li>ระบบใช้ Selenium Headless Chrome ในการ scrape</li>
                            <li>ข้อมูลส่วนตัวจะถูก anonymize ตาม PDPA</li>
                            <li>ระยะเวลาขึ้นอยู่กับจำนวนรีวิวและหน้า</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default ScrapePage;
