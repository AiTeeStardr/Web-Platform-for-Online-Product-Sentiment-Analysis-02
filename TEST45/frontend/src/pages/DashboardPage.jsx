import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProducts, deleteProduct } from '../services/api';

function DashboardPage() {
    const navigate = useNavigate();
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchProducts();
    }, []);

    const fetchProducts = async () => {
        try {
            const data = await getProducts();
            setProducts(data.products || []);
        } catch {
            // Use demo data on failure
            setProducts(getDemoProducts());
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (e, productId) => {
        e.stopPropagation();
        if (!confirm('คุณแน่ใจหรือว่าต้องการลบสินค้านี้?')) return;
        try {
            await deleteProduct(productId);
            setProducts(products.filter(p => p._id !== productId));
        } catch {
            alert('ไม่สามารถลบได้');
        }
    };

    const getSentimentColor = (stats) => {
        if (!stats) return 'var(--text-muted)';
        const { positive = 0, negative = 0 } = stats;
        if (positive > negative * 2) return 'var(--positive)';
        if (negative > positive) return 'var(--negative)';
        return 'var(--neutral)';
    };

    if (loading) {
        return (
            <div className="page-container">
                <div className="loading-container">
                    <div className="spinner"></div>
                    <p className="loading-text">กำลังโหลดข้อมูล...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="page-container">
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1 className="page-title">📊 แดชบอร์ด</h1>
                    <p className="page-subtitle">ภาพรวมสินค้าและผลวิเคราะห์ความคิดเห็น</p>
                </div>
                <button className="btn btn-primary" onClick={() => navigate('/scrape')}>
                    + เพิ่มสินค้า
                </button>
            </div>

            {/* Summary Stats */}
            <div className="grid-4" style={{ marginBottom: 'var(--space-2xl)' }}>
                <div className="stat-card">
                    <div className="stat-value" style={{ color: 'var(--accent-primary)' }}>{products.length}</div>
                    <div className="stat-label">สินค้าทั้งหมด</div>
                </div>
                <div className="stat-card positive">
                    <div className="stat-value">{products.reduce((sum, p) => sum + (p.summary_stats?.positive || 0), 0)}</div>
                    <div className="stat-label">รีวิว Positive</div>
                </div>
                <div className="stat-card neutral">
                    <div className="stat-value">{products.reduce((sum, p) => sum + (p.summary_stats?.neutral || 0), 0)}</div>
                    <div className="stat-label">รีวิว Neutral</div>
                </div>
                <div className="stat-card negative">
                    <div className="stat-value">{products.reduce((sum, p) => sum + (p.summary_stats?.negative || 0), 0)}</div>
                    <div className="stat-label">รีวิว Negative</div>
                </div>
            </div>

            {/* Product List */}
            {products.length === 0 ? (
                <div className="glass-card empty-state">
                    <div className="empty-state-icon">📦</div>
                    <h3 style={{ marginBottom: '0.5rem' }}>ยังไม่มีสินค้า</h3>
                    <p style={{ marginBottom: '1.5rem' }}>เริ่มต้นด้วยการ scrape รีวิวสินค้าจาก URL</p>
                    <button className="btn btn-primary" onClick={() => navigate('/scrape')}>
                        🚀 เริ่มเก็บข้อมูล
                    </button>
                </div>
            ) : (
                <div className="grid-2">
                    {products.map((product, i) => (
                        <div
                            key={product._id}
                            className="product-card animate-in"
                            style={{ animationDelay: `${i * 0.05}s` }}
                            onClick={() => navigate(`/analysis/${product._id}`)}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <div>
                                    <h3 className="product-name">{product.name || 'Unnamed Product'}</h3>
                                    <div className="product-meta">
                                        <span>🏪 {product.platform || 'shopee'}</span>
                                        <span>💬 {product.total_reviews || 0} รีวิว</span>
                                        <span>⭐ {product.average_rating?.toFixed(1) || '-'}</span>
                                    </div>
                                </div>
                                <button
                                    className="btn btn-danger btn-sm"
                                    onClick={(e) => handleDelete(e, product._id)}
                                >
                                    🗑️
                                </button>
                            </div>

                            {/* Sentiment Mini Bar */}
                            {product.summary_stats && (
                                <div>
                                    <div className="product-sentiment-mini">
                                        <span className="sentiment-dot positive">{product.summary_stats.positive || 0}</span>
                                        <span className="sentiment-dot neutral">{product.summary_stats.neutral || 0}</span>
                                        <span className="sentiment-dot negative">{product.summary_stats.negative || 0}</span>
                                    </div>
                                    <div className="aspect-bar" style={{ marginTop: '0.75rem' }}>
                                        {(() => {
                                            const total = (product.summary_stats.positive || 0) +
                                                (product.summary_stats.neutral || 0) +
                                                (product.summary_stats.negative || 0);
                                            if (total === 0) return null;
                                            return (
                                                <>
                                                    <div className="aspect-bar-positive" style={{ width: `${(product.summary_stats.positive / total) * 100}%` }}></div>
                                                    <div className="aspect-bar-neutral" style={{ width: `${(product.summary_stats.neutral / total) * 100}%` }}></div>
                                                    <div className="aspect-bar-negative" style={{ width: `${(product.summary_stats.negative / total) * 100}%` }}></div>
                                                </>
                                            );
                                        })()}
                                    </div>
                                </div>
                            )}

                            <div style={{ marginTop: '0.75rem', textAlign: 'right' }}>
                                <span className={`badge badge-${product.scrape_status === 'completed' ? 'positive' : 'neutral'}`}>
                                    {product.scrape_status === 'completed' ? '✅ วิเคราะห์แล้ว' : '⏳ ' + (product.scrape_status || 'pending')}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function getDemoProducts() {
    return [
        {
            _id: 'demo_001',
            name: 'Samsung Galaxy S24 Ultra',
            platform: 'shopee',
            total_reviews: 150,
            average_rating: 4.2,
            summary_stats: { positive: 95, neutral: 30, negative: 25 },
            scrape_status: 'completed'
        },
        {
            _id: 'demo_002',
            name: 'iPhone 16 Pro Max',
            platform: 'shopee',
            total_reviews: 200,
            average_rating: 4.5,
            summary_stats: { positive: 140, neutral: 35, negative: 25 },
            scrape_status: 'completed'
        }
    ];
}

export default DashboardPage;
