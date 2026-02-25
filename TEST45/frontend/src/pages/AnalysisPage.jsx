import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getAnalysis, startAnalysis } from '../services/api';
import {
    Chart as ChartJS,
    ArcElement,
    CategoryScale,
    LinearScale,
    BarElement,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';

ChartJS.register(
    ArcElement, CategoryScale, LinearScale, BarElement,
    PointElement, LineElement, Title, Tooltip, Legend, Filler
);

// Thai aspect name mapping
const ASPECT_NAMES = {
    camera: '📷 กล้อง',
    battery: '🔋 แบตเตอรี่',
    screen: '📱 หน้าจอ',
    price: '💰 ราคา',
    design: '🎨 ดีไซน์',
    performance: '⚡ ประสิทธิภาพ',
    service: '🛎️ บริการ'
};

function AnalysisPage() {
    const { productId } = useParams();
    const navigate = useNavigate();
    const [analysis, setAnalysis] = useState(null);
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);

    useEffect(() => {
        fetchAnalysis();
    }, [productId]);

    const fetchAnalysis = async () => {
        try {
            const data = await getAnalysis(productId);
            setAnalysis(data);
        } catch {
            // Try starting analysis
            setAnalysis(null);
        } finally {
            setLoading(false);
        }
    };

    const handleStartAnalysis = async () => {
        setAnalyzing(true);
        try {
            await startAnalysis(productId);
            // Poll until complete
            const poll = setInterval(async () => {
                try {
                    const data = await getAnalysis(productId);
                    if (data && data.analysis_status === 'completed') {
                        clearInterval(poll);
                        setAnalysis(data);
                        setAnalyzing(false);
                    }
                } catch { /* keep polling */ }
            }, 3000);
        } catch {
            setAnalyzing(false);
        }
    };

    if (loading) {
        return (
            <div className="page-container loading-container">
                <div className="spinner"></div>
                <p className="loading-text">กำลังโหลดผลวิเคราะห์...</p>
            </div>
        );
    }

    if (!analysis) {
        return (
            <div className="page-container">
                <div className="glass-card empty-state">
                    <div className="empty-state-icon">🔬</div>
                    <h3 style={{ marginBottom: '0.5rem' }}>ยังไม่มีผลวิเคราะห์</h3>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                        กดปุ่มด้านล่างเพื่อเริ่มวิเคราะห์ Sentiment ของรีวิว
                    </p>
                    <button className="btn btn-primary btn-lg" onClick={handleStartAnalysis} disabled={analyzing}>
                        {analyzing ? '⏳ กำลังวิเคราะห์...' : '🧠 เริ่มวิเคราะห์ Sentiment'}
                    </button>
                </div>
            </div>
        );
    }

    const overall = analysis.overall_sentiment || {};
    const aspects = analysis.aspect_sentiments || {};
    const wordCloud = analysis.word_cloud_data || [];
    const sampleReviews = analysis.sample_reviews || {};

    const totalReviews = (overall.positive || 0) + (overall.neutral || 0) + (overall.negative || 0);
    const positivePercent = totalReviews > 0 ? ((overall.positive / totalReviews) * 100).toFixed(1) : 0;

    // Doughnut chart data
    const doughnutData = {
        labels: ['Positive', 'Neutral', 'Negative'],
        datasets: [{
            data: [overall.positive || 0, overall.neutral || 0, overall.negative || 0],
            backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
            borderColor: ['#0a0e1a', '#0a0e1a', '#0a0e1a'],
            borderWidth: 3,
            hoverOffset: 8
        }]
    };

    const doughnutOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: { color: '#94a3b8', font: { family: 'Inter', size: 13 }, padding: 20 }
            }
        },
        cutout: '65%'
    };

    // Aspect bar chart data
    const aspectNames = Object.keys(aspects);
    const barData = {
        labels: aspectNames.map(a => ASPECT_NAMES[a] || a),
        datasets: [
            {
                label: 'Positive',
                data: aspectNames.map(a => aspects[a]?.positive || 0),
                backgroundColor: 'rgba(16, 185, 129, 0.8)',
                borderRadius: 4
            },
            {
                label: 'Neutral',
                data: aspectNames.map(a => aspects[a]?.neutral || 0),
                backgroundColor: 'rgba(245, 158, 11, 0.8)',
                borderRadius: 4
            },
            {
                label: 'Negative',
                data: aspectNames.map(a => aspects[a]?.negative || 0),
                backgroundColor: 'rgba(239, 68, 68, 0.8)',
                borderRadius: 4
            }
        ]
    };

    const barOptions = {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
            legend: {
                position: 'top',
                labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 } }
            }
        },
        scales: {
            x: {
                stacked: true,
                grid: { color: 'rgba(255,255,255,0.05)' },
                ticks: { color: '#64748b' }
            },
            y: {
                stacked: true,
                grid: { display: false },
                ticks: { color: '#f1f5f9', font: { family: 'Noto Sans Thai', size: 13 } }
            }
        }
    };

    return (
        <div className="page-container">
            {/* Header */}
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    {analysis.product_name && (
                        <p style={{ color: 'var(--accent-primary)', fontSize: '0.95rem', fontWeight: 500, marginBottom: '0.25rem', letterSpacing: '0.5px' }}>
                            📦 {analysis.product_name}
                        </p>
                    )}
                    <h1 className="page-title">🔬 ผลวิเคราะห์ Sentiment</h1>
                    <p className="page-subtitle">
                        Aspect-Based Sentiment Analysis • โมเดล: {analysis.model_used?.toUpperCase() || 'SVM'}
                        {analysis.platform && <> • แพลตฟอร์ม: {analysis.platform.charAt(0).toUpperCase() + analysis.platform.slice(1)}</>}
                    </p>
                </div>
                <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
                    ← กลับแดชบอร์ด
                </button>
            </div>

            {/* Overall Stats */}
            <div className="grid-4 animate-in" style={{ marginBottom: 'var(--space-2xl)' }}>
                <div className="stat-card">
                    <div className="stat-value" style={{ color: 'var(--accent-primary)' }}>{totalReviews}</div>
                    <div className="stat-label">รีวิวทั้งหมด</div>
                </div>
                <div className="stat-card positive">
                    <div className="stat-value">{overall.positive || 0}</div>
                    <div className="stat-label">Positive ({positivePercent}%)</div>
                </div>
                <div className="stat-card neutral">
                    <div className="stat-value">{overall.neutral || 0}</div>
                    <div className="stat-label">Neutral</div>
                </div>
                <div className="stat-card negative">
                    <div className="stat-value">{overall.negative || 0}</div>
                    <div className="stat-label">Negative</div>
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid-2 animate-in animate-delay-1" style={{ marginBottom: 'var(--space-2xl)' }}>
                {/* Doughnut Chart */}
                <div className="chart-container">
                    <h3 className="chart-title">📊 สัดส่วน Sentiment โดยรวม</h3>
                    <div style={{ height: '300px', display: 'flex', justifyContent: 'center' }}>
                        <Doughnut data={doughnutData} options={doughnutOptions} />
                    </div>
                </div>

                {/* Aspect Bar Chart */}
                <div className="chart-container">
                    <h3 className="chart-title">📈 Sentiment ตามมุมมอง (ABSA)</h3>
                    <div style={{ height: '300px' }}>
                        <Bar data={barData} options={barOptions} />
                    </div>
                </div>
            </div>

            {/* Aspect Detail Cards */}
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: 'var(--space-lg)' }}>
                🎯 รายละเอียดแต่ละมุมมอง
            </h3>
            <div className="grid-3 animate-in animate-delay-2" style={{ marginBottom: 'var(--space-2xl)' }}>
                {aspectNames.map((aspect, i) => {
                    const data = aspects[aspect];
                    const total = (data.positive || 0) + (data.neutral || 0) + (data.negative || 0);
                    const score = data.score != null ? data.score : (total > 0 ? data.positive / total : 0.5);
                    const scoreColor = score >= 0.6 ? 'var(--positive)' : score >= 0.4 ? 'var(--neutral)' : 'var(--negative)';

                    return (
                        <div key={aspect} className="aspect-card animate-in" style={{ animationDelay: `${i * 0.05}s` }}>
                            <div className="aspect-header">
                                <span className="aspect-name">{ASPECT_NAMES[aspect] || aspect}</span>
                                <span className="aspect-score" style={{ color: scoreColor }}>
                                    {(score * 100).toFixed(0)}%
                                </span>
                            </div>

                            <div className="aspect-bar">
                                {total > 0 && (
                                    <>
                                        <div className="aspect-bar-positive" style={{ width: `${(data.positive / total) * 100}%` }}></div>
                                        <div className="aspect-bar-neutral" style={{ width: `${(data.neutral / total) * 100}%` }}></div>
                                        <div className="aspect-bar-negative" style={{ width: `${(data.negative / total) * 100}%` }}></div>
                                    </>
                                )}
                            </div>

                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '0.5rem 0', display: 'flex', justifyContent: 'space-between' }}>
                                <span style={{ color: 'var(--positive)' }}>👍 {data.positive || 0}</span>
                                <span style={{ color: 'var(--neutral)' }}>😐 {data.neutral || 0}</span>
                                <span style={{ color: 'var(--negative)' }}>👎 {data.negative || 0}</span>
                            </div>

                            {data.keywords && data.keywords.length > 0 && (
                                <div className="aspect-keywords">
                                    {data.keywords.slice(0, 5).map((kw, j) => (
                                        <span key={j} className="keyword-tag">{kw}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Word Cloud */}
            {wordCloud.length > 0 && (
                <div className="chart-container animate-in animate-delay-3" style={{ marginBottom: 'var(--space-2xl)' }}>
                    <h3 className="chart-title">☁️ Word Cloud — คำที่พบบ่อย</h3>
                    <div className="word-cloud">
                        {wordCloud.map((item, i) => {
                            const maxFreq = wordCloud[0]?.frequency || 1;
                            const scale = 0.7 + (item.frequency / maxFreq) * 1.3;
                            const opacity = 0.5 + (item.frequency / maxFreq) * 0.5;
                            return (
                                <span
                                    key={i}
                                    className="word-cloud-item"
                                    style={{
                                        fontSize: `${scale}rem`,
                                        opacity,
                                        fontWeight: scale > 1.2 ? 700 : 400
                                    }}
                                >
                                    {item.word}
                                </span>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Top Keywords */}
            <div className="grid-2 animate-in animate-delay-3" style={{ marginBottom: 'var(--space-2xl)' }}>
                {analysis.top_positive_keywords?.length > 0 && (
                    <div className="glass-card">
                        <h3 style={{ color: 'var(--positive)', fontWeight: 600, marginBottom: '1rem' }}>
                            👍 Top Positive Keywords
                        </h3>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                            {analysis.top_positive_keywords.map((kw, i) => (
                                <span key={i} className="badge badge-positive">{kw}</span>
                            ))}
                        </div>
                    </div>
                )}
                {analysis.top_negative_keywords?.length > 0 && (
                    <div className="glass-card">
                        <h3 style={{ color: 'var(--negative)', fontWeight: 600, marginBottom: '1rem' }}>
                            👎 Top Negative Keywords
                        </h3>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                            {analysis.top_negative_keywords.map((kw, i) => (
                                <span key={i} className="badge badge-negative">{kw}</span>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Sample Reviews */}
            {(sampleReviews.positive?.length > 0 || sampleReviews.negative?.length > 0) && (
                <div className="animate-in animate-delay-4">
                    <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: 'var(--space-lg)' }}>
                        💬 ตัวอย่างรีวิว
                    </h3>
                    <div className="grid-2">
                        <div>
                            <h4 style={{ color: 'var(--positive)', marginBottom: '1rem', fontWeight: 600 }}>✅ Positive Reviews</h4>
                            {(sampleReviews.positive || []).map((review, i) => (
                                <div key={i} className="review-card">
                                    <div className="review-header">
                                        <span className="review-stars">{'⭐'.repeat(review.rating || 5)}</span>
                                        <span className="badge badge-positive">Positive</span>
                                    </div>
                                    <p className="review-text">{review.text}</p>
                                </div>
                            ))}
                        </div>
                        <div>
                            <h4 style={{ color: 'var(--negative)', marginBottom: '1rem', fontWeight: 600 }}>❌ Negative Reviews</h4>
                            {(sampleReviews.negative || []).map((review, i) => (
                                <div key={i} className="review-card">
                                    <div className="review-header">
                                        <span className="review-stars">{'⭐'.repeat(review.rating || 1)}</span>
                                        <span className="badge badge-negative">Negative</span>
                                    </div>
                                    <p className="review-text">{review.text}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AnalysisPage;
