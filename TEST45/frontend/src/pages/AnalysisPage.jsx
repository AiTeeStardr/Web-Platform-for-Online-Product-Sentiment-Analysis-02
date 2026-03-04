import { useState, useEffect, useRef } from 'react';
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
    const intervalRef = useRef(null);

    const [analysis, setAnalysis] = useState(null);
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);

    useEffect(() => {
        fetchAnalysis();
        return () => clearInterval(intervalRef.current);
    }, [productId]);

    const fetchAnalysis = async () => {
        try {
            const data = await getAnalysis(productId);

            // ถ้ามี overall_sentiment แปลว่ามีผลแล้ว
            if (data && data.overall_sentiment) {
                setAnalysis(data);
            } else {
                setAnalysis(null);
            }
        } catch {
            setAnalysis(null);
        } finally {
            setLoading(false);
        }
    };

    const handleStartAnalysis = async () => {
        setAnalyzing(true);

        try {
            await startAnalysis(productId);

            intervalRef.current = setInterval(async () => {
                try {
                    const data = await getAnalysis(productId);

                    // 🔥 หยุด polling เมื่อมีผลจริง
                    if (data && data.overall_sentiment) {
                        clearInterval(intervalRef.current);
                        setAnalysis(data);
                        setAnalyzing(false);
                    }
                } catch {
                    // ยังไม่เสร็จ ให้ polling ต่อ
                }
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
                    <h3>ยังไม่มีผลวิเคราะห์</h3>
                    <button
                        className="btn btn-primary btn-lg"
                        onClick={handleStartAnalysis}
                        disabled={analyzing}
                    >
                        {analyzing ? '⏳ กำลังวิเคราะห์...' : '🧠 เริ่มวิเคราะห์ Sentiment'}
                    </button>
                </div>
            </div>
        );
    }

    const overall = analysis.overall_sentiment || {};
    const aspects = analysis.aspect_sentiments || {};
    const aspectNames = Object.keys(aspects);

    const doughnutData = {
        labels: ['Positive', 'Neutral', 'Negative'],
        datasets: [{
            data: [
                overall.positive || 0,
                overall.neutral || 0,
                overall.negative || 0
            ],
            backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
            borderWidth: 0
        }]
    };

    const barData = {
        labels: aspectNames.map(a => ASPECT_NAMES[a] || a),
        datasets: [
            {
                label: 'Positive',
                data: aspectNames.map(a => aspects[a]?.positive || 0),
                backgroundColor: 'rgba(16,185,129,0.8)'
            },
            {
                label: 'Neutral',
                data: aspectNames.map(a => aspects[a]?.neutral || 0),
                backgroundColor: 'rgba(245,158,11,0.8)'
            },
            {
                label: 'Negative',
                data: aspectNames.map(a => aspects[a]?.negative || 0),
                backgroundColor: 'rgba(239,68,68,0.8)'
            }
        ]
    };

    return (
        <div className="page-container">

            <div className="page-header">
                <h1>🔬 ผลวิเคราะห์ Sentiment</h1>
                <button
                    className="btn btn-secondary"
                    onClick={() => navigate('/dashboard')}
                >
                    ← กลับแดชบอร์ด
                </button>
            </div>

            <div className="grid-2">

                <div className="chart-container">
                    <h3>📊 ภาพรวม Sentiment</h3>
                    <div style={{ height: '300px' }}>
                        <Doughnut data={doughnutData} />
                    </div>
                </div>

                <div className="chart-container">
                    <h3>📈 Sentiment ตามมุมมอง</h3>
                    <div style={{ height: '300px' }}>
                        <Bar data={barData} />
                    </div>
                </div>

            </div>
        </div>
    );
}

export default AnalysisPage;