// src/components/Sidebar.js

import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useApp } from '../context/AppContext';

const NAV_ITEMS = [
  { to: '/', icon: '🏠', label: 'Dashboard' },
  { to: '/upload', icon: '📂', label: 'Upload Dataset' },
  { to: '/train', icon: '🤖', label: 'AutoML Training' },
  { to: '/predict', icon: '🏠', label: 'Predict Price' },
  { to: '/explain', icon: '📊', label: 'Explainability' },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const { trainingStatus } = useApp();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <h2>🏢 Real Estate<br />AutoML</h2>
        <span>Prediction System</span>
      </div>

      {/* Nav links */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <span className="icon">{icon}</span>
            {label}
            {/* Training badge */}
            {to === '/train' && trainingStatus === 'running' && (
              <span style={{ marginLeft: 'auto' }}>
                <span className="spinner" style={{ width: 12, height: 12, borderWidth: 2 }} />
              </span>
            )}
            {to === '/train' && trainingStatus === 'done' && (
              <span style={{ marginLeft: 'auto', color: '#52D98C', fontSize: 14 }}>✓</span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User footer */}
      <div className="sidebar-footer">
        {user && (
          <div style={{ marginBottom: 8 }}>
            <div style={{ color: 'rgba(255,255,255,0.7)', fontWeight: 600, fontSize: 12 }}>
              {user.name || user.email}
            </div>
            <div style={{ fontSize: 10 }}>Real Estate Professional</div>
          </div>
        )}
        <button
          onClick={handleLogout}
          style={{
            background: 'rgba(255,255,255,0.1)', border: 'none', color: 'rgba(255,255,255,0.65)',
            borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 12, width: '100%',
          }}
        >
          ↩ Sign Out
        </button>
      </div>
    </aside>
  );
}
