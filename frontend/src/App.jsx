import { useEffect, useState } from 'react';
import { Routes, Route, NavLink } from 'react-router-dom';
import { Moon, SunMedium } from 'lucide-react';
import CitizenPage from './pages/CitizenPage';
import AuditPage from './pages/AuditPage';
import './App.css';

function App() {
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem('equityguard-theme');
    if (savedTheme === 'light' || savedTheme === 'dark') {
      return savedTheme;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('equityguard-theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme((current) => (current === 'dark' ? 'light' : 'dark'));

  return (
    <div className="app-shell">
      <div className="ambient-glow ambient-glow-left" aria-hidden="true" />
      <div className="ambient-glow ambient-glow-right" aria-hidden="true" />

      <header className="topbar">
        <div className="brand-block">
          <p className="brand-kicker">Responsible AI Intelligence</p>
          <h1 className="brand-name">EquityGuard</h1>
        </div>

        <div className="topbar-actions">
          <nav className="primary-nav" aria-label="Primary">
            <NavLink to="/" end className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
              Citizen View
            </NavLink>
            <NavLink to="/audit" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
              Organization Audit
            </NavLink>
          </nav>

          <button className="theme-toggle" type="button" onClick={toggleTheme} aria-label="Toggle color mode">
            {theme === 'dark' ? <SunMedium size={16} /> : <Moon size={16} />}
            <span>{theme === 'dark' ? 'Light' : 'Dark'} Mode</span>
          </button>
        </div>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<CitizenPage />} />
          <Route path="/audit" element={<AuditPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
