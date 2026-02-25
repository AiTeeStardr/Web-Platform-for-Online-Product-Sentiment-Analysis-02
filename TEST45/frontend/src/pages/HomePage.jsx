import { useNavigate } from 'react-router-dom';

function HomePage() {
    const navigate = useNavigate();

    return (
        <div className="page-container">
            {/* Hero Section */}
            <section className="hero">
                <h1 className="hero-title animate-in">
                    วิเคราะห์ความคิดเห็น<br />สินค้าออนไลน์
                </h1>
                <p className="hero-subtitle animate-in animate-delay-1">
                    แพลตฟอร์ม AI สำหรับวิเคราะห์รีวิวสินค้าภาษาไทย
                    ด้วยเทคนิค Aspect-Based Sentiment Analysis
                    เจาะลึกทุกมุมมอง ทั้งกล้อง แบตเตอรี่ ราคา และอื่น ๆ
                </p>
                <div className="hero-actions animate-in animate-delay-2">
                    <button className="btn btn-primary btn-lg" onClick={() => navigate('/scrape')}>
                        🚀 เริ่มวิเคราะห์
                    </button>
                    <button className="btn btn-secondary btn-lg" onClick={() => navigate('/dashboard')}>
                        📊 ดูแดชบอร์ด
                    </button>
                </div>
            </section>

            {/* Features */}
            <section className="features-grid">
                <div className="glass-card feature-card animate-in animate-delay-1">
                    <span className="feature-icon">🔍</span>
                    <h3 className="feature-title">Web Scraping อัตโนมัติ</h3>
                    <p className="feature-desc">
                        เก็บรีวิวจาก Shopee โดยอัตโนมัติผ่าน Selenium
                        รองรับ Dynamic Content และ Lazy Loading
                    </p>
                </div>
                <div className="glass-card feature-card animate-in animate-delay-2">
                    <span className="feature-icon">🧠</span>
                    <h3 className="feature-title">Thai NLP Pipeline</h3>
                    <p className="feature-desc">
                        ประมวลผลภาษาไทยด้วย PyThaiNLP
                        ตัดคำ วิเคราะห์อารมณ์ และแปลง Emoji เป็นข้อความ
                    </p>
                </div>
                <div className="glass-card feature-card animate-in animate-delay-3">
                    <span className="feature-icon">📈</span>
                    <h3 className="feature-title">ABSA Dashboard</h3>
                    <p className="feature-desc">
                        วิเคราะห์ระดับมุมมอง (Aspect-Based) พร้อม
                        กราฟเชิงลึก Word Cloud และ Sentiment Trend
                    </p>
                </div>
            </section>

            {/* Tech Stack */}
            <section style={{ marginTop: 'var(--space-3xl)', textAlign: 'center' }}>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 'var(--space-xl)', color: 'var(--text-secondary)' }}>
                    เทคโนโลยีที่ใช้
                </h2>
                <div className="grid-4">
                    {[
                        { icon: '⚛️', name: 'React', desc: 'Interactive Dashboard' },
                        { icon: '🐍', name: 'Flask', desc: 'RESTful API Server' },
                        { icon: '🍃', name: 'MongoDB', desc: 'NoSQL Database' },
                        { icon: '🤖', name: 'SVM + TF-IDF', desc: 'Sentiment Analysis' }
                    ].map((tech, i) => (
                        <div key={i} className="stat-card animate-in" style={{ animationDelay: `${i * 0.1}s` }}>
                            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{tech.icon}</div>
                            <div className="stat-value" style={{ fontSize: '1.2rem', color: 'var(--text-primary)' }}>{tech.name}</div>
                            <div className="stat-label">{tech.desc}</div>
                        </div>
                    ))}
                </div>
            </section>

            {/* PDPA Notice */}
            <section className="glass-card animate-in" style={{ marginTop: 'var(--space-3xl)', textAlign: 'center' }}>
                <span style={{ fontSize: '1.5rem' }}>🔒</span>
                <h3 style={{ margin: '0.5rem 0', fontWeight: 600 }}>PDPA Compliant</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    ระบบปฏิบัติตาม พ.ร.บ. คุ้มครองข้อมูลส่วนบุคคล โดยทำ Anonymization
                    ข้อมูลส่วนตัวก่อนจัดเก็บ (SHA-256 Hash) เสมอ
                </p>
            </section>
        </div>
    );
}

export default HomePage;
