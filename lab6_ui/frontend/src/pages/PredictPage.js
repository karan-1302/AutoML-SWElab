// src/pages/PredictPage.js
// UC-09: Generate Prediction  |  UC-10: Reuse Trained Model
// Structured form for property features → calls Prediction Service → displays estimated price.

import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';

// Feature fields with validation metadata
const FIELDS = [
  { key: 'bedrooms',    label: 'Bedrooms',          type: 'number', unit: 'rooms',    min: 0, max: 20,    placeholder: 'e.g. 3'       },
  { key: 'bathrooms',   label: 'Bathrooms',          type: 'number', unit: 'rooms',    min: 0, max: 10,    placeholder: 'e.g. 2'       },
  { key: 'sqft_living', label: 'Living Area (sq ft)',type: 'number', unit: 'sq ft',    min: 0, max: 50000, placeholder: 'e.g. 1800'    },
  { key: 'sqft_lot',    label: 'Lot Size (sq ft)',   type: 'number', unit: 'sq ft',    min: 0, max: 200000,placeholder: 'e.g. 5000'    },
  { key: 'floors',      label: 'Number of Floors',   type: 'number', unit: 'floors',   min: 1, max: 5,     placeholder: 'e.g. 2'       },
  { key: 'waterfront',  label: 'Waterfront Property',type: 'select', options: [{v:0,l:'No'},{v:1,l:'Yes'}]                              },
  { key: 'view',        label: 'View Quality (0–4)', type: 'number', unit: '/4',       min: 0, max: 4,     placeholder: 'e.g. 2'       },
  { key: 'condition',   label: 'Condition (1–5)',     type: 'number', unit: '/5',       min: 1, max: 5,     placeholder: 'e.g. 3'       },
  { key: 'grade',       label: 'Grade (1–13)',        type: 'number', unit: '/13',      min: 1, max: 13,    placeholder: 'e.g. 7'       },
  { key: 'yr_built',    label: 'Year Built',          type: 'number', unit: 'year',     min: 1800, max: 2025, placeholder: 'e.g. 1990' },
  { key: 'zipcode',     label: 'ZIP Code',            type: 'text',   placeholder: 'e.g. 98103'                                        },
];

function formatPrice(val) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);
}

export default function PredictPage() {
  const { bestModel, lastPrediction, setLastPrediction } = useApp();
  const [form,    setForm]    = useState({});
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');
  const navigate = useNavigate();

  const handleChange = (key, value) => setForm(prev => ({ ...prev, [key]: value }));

  const handlePredict = async () => {
    // Basic validation
    for (const f of FIELDS) {
      if (f.key === 'waterfront') continue;
      if (!form[f.key] && form[f.key] !== 0) {
        setError(`Please fill in: ${f.label}`);
        return;
      }
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
      // smooth scroll to result
      setTimeout(() => document.getElementById('result-card')?.scrollIntoView({ behavior: 'smooth' }), 100);
    } catch (err) {
      setError(err.response?.data?.detail || 'Prediction failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Guard: need trained model
  if (!bestModel) {
    return (
      <div>
        <div className="page-header">
          <h1>🏠 Predict Price</h1>
        </div>
        <div className="card">
          <div className="alert alert-warning">
            ⚠ No trained model found. Please <a href="/train" style={{ color: 'inherit', fontWeight: 700 }}>complete training</a> first.
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

      {/* Active model banner */}
      <div className="alert alert-info" style={{ marginBottom: 20 }}>
        🤖 Active model: <strong>{bestModel.name}</strong> &nbsp;·&nbsp; R² = {Number(bestModel.r2).toFixed(4)}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Form card */}
        <div className="card">
          <div className="card-title">Property Features</div>
          <div className="card-subtitle">Fill in all fields to generate a prediction</div>

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
                  className="form-control"
                  placeholder={field.placeholder}
                  min={field.min}
                  max={field.max}
                  value={form[field.key] ?? ''}
                  onChange={e => handleChange(field.key, e.target.value)}
                />
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
              {/* Price result */}
              <div className="price-result">
                <div className="price-label">Estimated Market Value</div>
                <div className="price-value">{formatPrice(lastPrediction.predicted_price)}</div>
                <div className="price-meta">
                  Model: {lastPrediction.model_used} &nbsp;·&nbsp;
                  Confidence: {lastPrediction.confidence}%
                </div>
              </div>

              {/* Quick stats */}
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

              {/* CTA to explain */}
              <div className="card mt-4">
                <div className="card-title">Why this price?</div>
                <p style={{ color: 'var(--color-muted)', fontSize: 13, marginBottom: 16 }}>
                  View SHAP feature importance to understand which factors drove this estimate.
                </p>
                <button
                  className="btn btn-ghost"
                  onClick={() => navigate('/explain')}
                >
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
