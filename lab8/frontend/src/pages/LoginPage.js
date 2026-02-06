// src/pages/LoginPage.js
// UC: Authentication — allows real estate professionals to log in securely.

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

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
      navigate('/dashboard');
    } catch (err) {
      let msg = 'Login failed. Please try again.';

      if (err.response) {
        const status = err.response.status;
        const detail = err.response.data?.detail;

        if (status === 401) {
          msg = Array.isArray(detail) ? detail.join(' ') : (detail || 'Invalid email or password.');
        } else if (status === 422) {
          msg = Array.isArray(detail) ? detail.join(' ') : (detail || 'Please check your input.');
        } else if (status >= 500) {
          msg = 'Server error. Please try again later.';
        } else {
          msg = Array.isArray(detail) ? detail.join(' ') : (detail || `Error ${status}: Please try again.`);
        }
      } else if (err.request) {
        msg = 'Cannot connect to server. Please check if backend is running.';
      }

      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-outer">
      <div className="login-card">
        <div className="login-logo">
          <div className="logo-icon">🏠</div>
          <h1>Real Estate AutoML</h1>
          <p>Sign in to your account to continue</p>
        </div>

        {error && (
          <div className="alert alert-error">
            <span>!</span> {error}
          </div>
        )}

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
              'Sign In'
            )}
          </button>
        </form>

        <hr className="divider" />
        <p className="text-center text-muted" style={{ fontSize: 12 }}>
          Demo credentials: <strong>demo@realestate.com</strong> / <strong>password123</strong>
        </p>
        <p className="text-center text-muted" style={{ fontSize: 12, marginTop: 8 }}>
          Don't have an account? <a href="/register" style={{ color: '#0066cc', textDecoration: 'none' }}>Create one</a>
        </p>
      </div>
    </div>
  );
}
