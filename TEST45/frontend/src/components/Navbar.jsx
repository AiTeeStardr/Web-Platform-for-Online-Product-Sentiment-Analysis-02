import { NavLink } from 'react-router-dom';

function Navbar() {
    return (
        <nav className="navbar">
            <NavLink to="/" className="navbar-brand">
                <span className="logo-icon">📊</span>
                SentimentScope
            </NavLink>
            <ul className="navbar-links">
                <li><NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>หน้าแรก</NavLink></li>
                <li><NavLink to="/scrape" className={({ isActive }) => isActive ? 'active' : ''}>เก็บข้อมูล</NavLink></li>
                <li><NavLink to="/dashboard" className={({ isActive }) => isActive ? 'active' : ''}>แดชบอร์ด</NavLink></li>
            </ul>
        </nav>
    );
}

export default Navbar;
