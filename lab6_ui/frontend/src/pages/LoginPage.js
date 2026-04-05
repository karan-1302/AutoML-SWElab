// src/pages/LoginPage.js
// UC: Authentication — allows real estate professionals to log in securely.

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [error,    setError]    = useState('');
  const [loading,  setLoading]  = useState(false);

  const { login } = useAuth();
  const navigate  = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
      navigate('/upload');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Login failed. Check your credentials.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-outer">
      <div className="login-card">
        {/* Logo */}
        <div className="login-logo">
          <div className="logo-icon">🏢</div>
          <h1>Real Estate AutoML</h1>
          <p>Sign in to your account to continue</p>
        </div>

        {/* Error */}
        {error && (
          <div className="alert alert-error">
            <span>⚠</span> {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              className="form-control"
              placeholder="agent@realestate.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="form-control"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary w-full"
            style={{ justifyContent: 'center', marginTop: 8, padding: '12px' }}
            disabled={loading}
          >
            {loading ? (
              <><span className="spinner" /> Signing in…</>
            ) : (
              '→ Sign In'
            )}
          </button>
        </form>

        <hr className="divider" />
        <p className="text-center text-muted" style={{ fontSize: 12 }}>
          Demo credentials: <strong>demo@realestate.com</strong> / <strong>password123</strong>
        </p>
      </div>
    </div>
  );
}
