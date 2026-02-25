import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import ScrapePage from './pages/ScrapePage';
import DashboardPage from './pages/DashboardPage';
import AnalysisPage from './pages/AnalysisPage';

function App() {
    return (
        <Router>
            <Navbar />
            <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/scrape" element={<ScrapePage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/analysis/:productId" element={<AnalysisPage />} />
            </Routes>
        </Router>
    );
}

export default App;
