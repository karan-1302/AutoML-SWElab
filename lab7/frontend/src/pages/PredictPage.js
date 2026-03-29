// src/pages/PredictPage.js
// UC-09: Generate Prediction  |  UC-10: Reuse Trained Model
// Enhanced with per-field BLL validation feedback
//   - BR-PRD-01: Trained model required
//   - BR-PRD-02: All fields required
//   - BR-PRD-03: Range validation
//   - BR-PRD-04: Confidence scoring (DT-PRD-03)
//   - DT-PRD-01: Form input → DataFrame
//   - DT-PRD-02: Pipeline output → rounded price

import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';

// Feature fields with validation metadata (mirrors predict_bll.FIELD_RULES)
const FIELDS = [
  { key: 'bedrooms',    label: 'Bedrooms',           type: 'number', unit: 'rooms',    min: 0, max: 20,     placeholder: 'e.g. 3'       },
  { key: 'bathrooms',   label: 'Bathrooms',           type: 'number', unit: 'rooms',    min: 0, max: 10,     placeholder: 'e.g. 2'       },
  { key: 'sqft_living', label: 'Living Area (sq ft)', type: 'number', unit: 'sq ft',    min: 1, max: 50000,  placeholder: 'e.g. 1800'    },
  { key: 'sqft_lot',    label: 'Lot Size (sq ft)',    type: 'number', unit: 'sq ft',    min: 1, max: 200000, placeholder: 'e.g. 5000'    },
  { key: 'floors',      label: 'Number of Floors',    type: 'number', unit: 'floors',   min: 1, max: 5,      placeholder: 'e.g. 2'       },
  { key: 'waterfront',  label: 'Waterfront Property', type: 'select', options: [{v:0,l:'No'},{v:1,l:'Yes'}]                               },
  { key: 'view',        label: 'View Quality (0–4)',  type: 'number', unit: '/4',       min: 0, max: 4,      placeholder: 'e.g. 2'       },
  { key: 'condition',   label: 'Condition (1–5)',     type: 'number', unit: '/5',       min: 1, max: 5,      placeholder: 'e.g. 3'       },
  { key: 'grade',       label: 'Grade (1–13)',        type: 'number', unit: '/13',      min: 1, max: 13,     placeholder: 'e.g. 7'       },
  { key: 'yr_built',    label: 'Year Built',          type: 'number', unit: 'year',     min: 1800, max: 2026, placeholder: 'e.g. 1990'   },
  { key: 'zipcode',     label: 'ZIP Code',            type: 'text',   placeholder: 'e.g. 98103'                                          },
];

function formatPrice(val) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);
}

// Client-side field validation (mirrors predict_bll._validate_features)
function validateField(field, value) {
  if (field.key === 'waterfront') return null;
  if (!value && value !== 0) return `${field.label} is required (BR-PRD-02)`;
  if (field.type === 'number') {
    const num = Number(value);
    if (isNaN(num)) return `${field.label} must be a valid number`;
    if (num < field.min || num > field.max) {
      return `${field.label} must be between ${field.min} and ${field.max} (BR-PRD-03)`;
    }
  }
  if (field.type === 'text' && !String(value).trim()) {
    return `${field.label} must not be empty (BR-PRD-09)`;
  }
  return null;
}

export default function PredictPage() {
  const { bestModel, lastPrediction, setLastPrediction } = useApp();
  const [form,        setForm]        = useState({});
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState('');
  const navigate = useNavigate();

  const handleChange = (key, value) => {
    setForm(prev => ({ ...prev, [key]: value }));
    // Clear field error on change
    setFieldErrors(prev => ({ ...prev, [key]: null }));
  };

  const handleBlur = (field) => {
    const err = validateField(field, form[field.key]);
    if (err) setFieldErrors(prev => ({ ...prev, [field.key]: err }));
  };

  const handlePredict = async () => {
    // Validate all fields (mirrors predict_bll)
    const newErrors = {};
    let hasErrors = false;
    for (const f of FIELDS) {
      const err = validateField(f, form[f.key]);
      if (err) { newErrors[f.key] = err; hasErrors = true; }
    }
    setFieldErrors(newErrors);
    if (hasErrors) {
      setError('Please fix the validation errors below (BR-PRD-02/03).');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const payload = {};
      FIELDS.forEach(f => {
        payload[f.key] = f.type === 'number' ? Number(form[f.key]) : form[f.key];
      });

      const res = await axios.post('/api/predict', payload);
      setLastPrediction(res.data);
      setTimeout(() => document.getElementById('result-card')?.scrollIntoView({ behavior: 'smooth' }), 100);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.join(' '));
      } else {
        setError(detail || 'Prediction failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Guard: need trained model (BR-PRD-01)
  if (!bestModel) {
    return (
      <div>
        <div className="page-header"><h1>🏠 Predict Price</h1></div>
        <div className="card">
          <div className="alert alert-warning">
            ⚠ No trained model found (BR-PRD-01). Please <a href="/train" style={{ color: 'inherit', fontWeight: 700 }}>complete training</a> first.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1>🏠 Predict Property Price</h1>
        <p>Enter property features to get an instant AI-powered price estimate</p>
      </div>

      <div className="alert alert-info" style={{ marginBottom: 20 }}>
        🤖 Active model: <strong>{bestModel.name}</strong> &nbsp;·&nbsp; R² = {Number(bestModel.r2).toFixed(4)}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Form card */}
        <div className="card">
          <div className="card-title">Property Features</div>
          <div className="card-subtitle">Fill in all fields — BLL validates each field (predict_bll.py)</div>

          {error && <div className="alert alert-error">⚠ {error}</div>}

          {FIELDS.map(field => (
            <div className="form-group" key={field.key}>
              <label className="form-label" htmlFor={field.key}>
                {field.label}
                {field.unit && (
                  <span style={{ fontWeight: 400, color: 'var(--color-muted)', marginLeft: 4 }}>
                    ({field.unit})
                  </span>
                )}
                {field.min !== undefined && field.type === 'number' && (
                  <span style={{ fontWeight: 400, color: '#9CA3AF', marginLeft: 4, fontSize: 11 }}>
                    [{field.min}–{field.max}]
                  </span>
                )}
              </label>

              {field.type === 'select' ? (
                <select
                  id={field.key}
                  className="form-control"
                  value={form[field.key] ?? ''}
                  onChange={e => handleChange(field.key, e.target.value)}
                >
                  {field.options.map(o => (
                    <option key={o.v} value={o.v}>{o.l}</option>
                  ))}
                </select>
              ) : (
                <input
                  id={field.key}
                  type={field.type}
                  className={`form-control ${fieldErrors[field.key] ? 'input-error' : ''}`}
                  placeholder={field.placeholder}
                  min={field.min}
                  max={field.max}
                  value={form[field.key] ?? ''}
                  onChange={e => handleChange(field.key, e.target.value)}
                  onBlur={() => handleBlur(field)}
                  style={fieldErrors[field.key] ? { borderColor: '#EF4444' } : {}}
                />
              )}

              {/* Per-field validation error (mirrors BLL) */}
              {fieldErrors[field.key] && (
                <small style={{ color: '#EF4444', fontSize: 11, marginTop: 3, display: 'block' }}>
                  ⚠ {fieldErrors[field.key]}
                </small>
              )}
            </div>
          ))}

          <button
            className="btn btn-primary w-full"
            style={{ justifyContent: 'center', padding: '12px' }}
            onClick={handlePredict}
            disabled={loading}
          >
            {loading ? (
              <><span className="spinner" /> Calculating…</>
            ) : '🔮 Get Price Estimate'}
          </button>
        </div>

        {/* Result column */}
        <div>
          {lastPrediction ? (
            <div id="result-card">
              <div className="price-result">
                <div className="price-label">Estimated Market Value (BR-PRD-05)</div>
                <div className="price-value">{formatPrice(lastPrediction.predicted_price)}</div>
                <div className="price-meta">
                  Model: {lastPrediction.model_used} &nbsp;·&nbsp;
                  Confidence: {lastPrediction.confidence}% (BR-PRD-04: 50 + R²×49)
                </div>
              </div>

              <div className="metric-grid mt-4">
                <div className="metric-card">
                  <div className="metric-label">Price / sq ft</div>
                  <div className="metric-value">
                    ${Math.round(lastPrediction.predicted_price / (Number(form.sqft_living) || 1)).toLocaleString()}
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Model R²</div>
                  <div className="metric-value">{Number(bestModel.r2).toFixed(3)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Est. Error (±)</div>
                  <div className="metric-value">${Math.round(bestModel.rmse).toLocaleString()}</div>
                </div>
              </div>

              {/* Data Transformation note */}
              <div className="card mt-4" style={{ background: 'rgba(46,117,182,0.03)' }}>
                <div className="card-title" style={{ fontSize: 13 }}>🔄 Data Transformation Pipeline</div>
                <div style={{ fontSize: 12, color: '#6B7280', lineHeight: 1.6 }}>
                  <strong>DT-PRD-01:</strong> Form input → single-row DataFrame matching training schema<br/>
                  <strong>DT-PRD-02:</strong> sklearn pipeline.predict() → rounded float price<br/>
                  <strong>DT-PRD-03:</strong> R² score → confidence % (human-readable)
                </div>
              </div>

              <div className="card mt-4">
                <div className="card-title">Why this price?</div>
                <p style={{ color: 'var(--color-muted)', fontSize: 13, marginBottom: 16 }}>
                  View SHAP feature importance to understand which factors drove this estimate.
                </p>
                <button className="btn btn-ghost" onClick={() => navigate('/explain')}>
                  View Explainability →
                </button>
              </div>
            </div>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '60px 24px' }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>🔮</div>
              <div className="card-title">Your estimate will appear here</div>
              <p className="text-muted" style={{ fontSize: 13 }}>
                Fill in the property features and click "Get Price Estimate" to begin.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
