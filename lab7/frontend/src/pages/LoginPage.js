// src/pages/LoginPage.js
// UC: Authentication — Demonstrates BLL interaction:
//   - Real-time email format validation (BR-AUTH-01)
//   - Required field checking (BR-AUTH-02)
//   - Password length validation (BR-AUTH-03)
//   - Backend BLL error messages displayed to user

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

export default function LoginPage() {
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [errors,   setErrors]   = useState([]);
  const [loading,  setLoading]  = useState(false);

  const { login } = useAuth();
  const navigate  = useNavigate();

  // ── Client-side BLL validation (mirrors backend auth_bll) ──
  const validateForm = () => {
    const errs = [];

    // BR-AUTH-02: Required fields
    if (!email.trim()) errs.push('Email address is required.');
    if (!password)     errs.push('Password is required.');
    if (errs.length)   return errs;

    // BR-AUTH-01: Email format
    if (!EMAIL_REGEX.test(email.trim())) {
      errs.push('Email address is not in a valid format (e.g. user@domain.com).');
    }

    // BR-AUTH-03: Minimum password length
    if (password.length < 6) {
      errs.push('Password must be at least 6 characters.');
    }

    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors([]);

    // Client-side validation (same rules as BLL)
    const validationErrors = validateForm();
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    setLoading(true);
    try {
      await login(email.trim().toLowerCase(), password);
      navigate('/upload');
    } catch (err) {
      // Backend BLL returns errors as array or string
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setErrors(detail);
      } else {
        setErrors([detail || 'Login failed. Check your credentials.']);
      }
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

        {/* BLL Validation Errors */}
        {errors.length > 0 && (
          <div className="alert alert-error">
            {errors.map((err, i) => (
              <div key={i} style={{ marginBottom: i < errors.length - 1 ? 4 : 0 }}>
                ⚠ {err}
              </div>
            ))}
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
            {email && !EMAIL_REGEX.test(email.trim()) && (
              <small style={{ color: '#E74C3C', fontSize: 11, marginTop: 4, display: 'block' }}>
                ⚠ Invalid email format (BR-AUTH-01)
              </small>
            )}
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
            {password && password.length < 6 && (
              <small style={{ color: '#E74C3C', fontSize: 11, marginTop: 4, display: 'block' }}>
                ⚠ Password must be at least 6 characters (BR-AUTH-03)
              </small>
            )}
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

        {/* BLL info */}
        <div style={{ background: 'rgba(46,117,182,0.05)', borderRadius: 8, padding: '10px 14px', marginTop: 8 }}>
          <div style={{ fontSize: 11, color: '#6B7280', fontWeight: 600, marginBottom: 4 }}>
            🔒 BLL Validation Active
          </div>
          <div style={{ fontSize: 11, color: '#9CA3AF' }}>
            Client-side validation mirrors backend auth_bll.py rules: email format,
            password length, required fields. Server-side BLL performs credential verification.
          </div>
        </div>

        <p className="text-center text-muted" style={{ fontSize: 12, marginTop: 12 }}>
          Demo credentials: <strong>demo@realestate.com</strong> / <strong>password123</strong>
        </p>
      </div>
    </div>
  );
}
