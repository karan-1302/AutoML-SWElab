// src/pages/RegisterPage.js
// UC: User Registration — allows new users to create accounts securely.

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function RegisterPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!email || !password || !fullName) {
            setError('Please fill in all fields.');
            return;
        }

        if (password.length < 6) {
            setError('Password must be at least 6 characters.');
            return;
        }

        setLoading(true);
        try {
            await register(email, password, fullName);
            navigate('/dashboard');
        } catch (err) {
            let msg = 'Registration failed. Please try again.';

            if (err.response) {
                const status = err.response.status;
                const detail = err.response.data?.detail;

                if (status === 409) {
                    msg = Array.isArray(detail) ? detail.join(' ') : (detail || 'An account with this email address already exists.');
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
                    <p>Create a new account to get started</p>
                </div>

                {error && (
                    <div className="alert alert-error">
                        <span>!</span> {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label" htmlFor="fullName">Full Name</label>
                        <input
                            id="fullName"
                            type="text"
                            className="form-control"
                            placeholder="John Doe"
                            value={fullName}
                            onChange={e => setFullName(e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label" htmlFor="email">Email Address</label>
                        <input
                            id="email"
                            type="email"
                            className="form-control"
                            placeholder="agent@realestate.com"
                            value={email}
                            onChange={e => {
                                setEmail(e.target.value);
                                if (error) setError('');
                            }}
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
                            autoComplete="new-password"
                            required
                        />
                        <small className="text-muted" style={{ display: 'block', marginTop: 4 }}>
                            Minimum 6 characters
                        </small>
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary w-full"
                        style={{ justifyContent: 'center', marginTop: 8, padding: '12px' }}
                        disabled={loading}
                    >
                        {loading ? (
                            <><span className="spinner" /> Creating account…</>
                        ) : (
                            'Create Account'
                        )}
                    </button>
                </form>

                <hr className="divider" />
                <p className="text-center text-muted" style={{ fontSize: 12 }}>
                    Already have an account? <Link to="/login" style={{ color: '#0066cc', textDecoration: 'none' }}>Sign in</Link>
                </p>
            </div>
        </div>
    );
}
