// src/pages/ExplainPage.js
// UC-11: View Explainable Predictions  |  UC-12: Decision-Support Recommendations
// Renders SHAP feature importance bar chart and investment recommendation cards.

import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
  ResponsiveContainer, ReferenceLine, CartesianGrid,
} from 'recharts';
import { useApp } from '../context/AppContext';

const COLOR_POS = '#2E75B6';
const COLOR_NEG = '#E74C3C';

// ── Custom tooltip ────────────────────────────────────────────
function ShapTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{
      background: '#fff', border: '1px solid #DDE3F0',
      borderRadius: 8, padding: '10px 14px', fontSize: 13, boxShadow: '0 2px 12px rgba(0,0,0,.1)',
    }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{d.feature}</div>
      <div style={{ color: d.value >= 0 ? COLOR_POS : COLOR_NEG }}>
        SHAP value: {d.value >= 0 ? '+' : ''}{d.value.toFixed(4)}
      </div>
      <div style={{ color: '#6B7280', fontSize: 12, marginTop: 2 }}>
        {d.value >= 0 ? '↑ Increases' : '↓ Decreases'} predicted price
      </div>
    </div>
  );
}

export default function ExplainPage() {
  const { lastPrediction, bestModel } = useApp();
  const [shapData,  setShapData]  = useState([]);
  const [recs,      setRecs]      = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState('');

  useEffect(() => {
    const fetchExplain = async () => {
      setLoading(true);
      try {
        const res = await axios.get('/api/explain/latest');
        // res.data: { shap_values: [{feature, value}], recommendations: [...] }
        const sorted = [...res.data.shap_values].sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
        setShapData(sorted);
        setRecs(res.data.recommendations);
      } catch (err) {
        setError(err.response?.data?.detail || 'Could not load explainability data.');
      } finally {
        setLoading(false);
      }
    };
    fetchExplain();
  }, []);

  // Guard
  if (!bestModel) {
    return (
      <div>
        <div className="page-header"><h1>📊 Explainability</h1></div>
        <div className="card">
          <div className="alert alert-warning">
            ⚠ No trained model available. Please <a href="/train" style={{ color: 'inherit', fontWeight: 700 }}>train a model</a> first.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1>📊 Explainability & Decision Support</h1>
        <p>Understand why the model predicted the price it did</p>
      </div>

      {/* Info banner */}
      {lastPrediction && (
        <div className="alert alert-info" style={{ marginBottom: 20 }}>
          📌 Explaining prediction for last property estimate &nbsp;·&nbsp;
          <strong>Model: {bestModel.name}</strong>
        </div>
      )}

      {/* SHAP Chart */}
      <div className="card">
        <div className="card-title">Feature Importance (SHAP Values)</div>
        <div className="card-subtitle">
          Each bar shows how much a feature pushed the prediction higher or lower than the average price.
        </div>

        {/* Legend */}
        <div className="shap-legend">
          <span><span className="dot dot-pos" />Increases price</span>
          <span><span className="dot dot-neg" />Decreases price</span>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-muted)' }}>
            <span className="spinner" style={{ borderTopColor: 'var(--color-accent)', borderColor: 'var(--color-border)' }} />
            <p style={{ marginTop: 12 }}>Calculating SHAP values…</p>
          </div>
        ) : error ? (
          <div className="alert alert-error">⚠ {error}</div>
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(300, shapData.length * 36)}>
            <BarChart
              data={shapData}
              layout="vertical"
              margin={{ top: 8, right: 30, left: 140, bottom: 8 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#EEF0F6" />
              <XAxis
                type="number"
                tickFormatter={v => v.toFixed(3)}
                style={{ fontSize: 12 }}
                stroke="#9CA3AF"
              />
              <YAxis
                type="category"
                dataKey="feature"
                width={130}
                style={{ fontSize: 12, fontWeight: 500 }}
                stroke="#9CA3AF"
              />
              <Tooltip content={<ShapTooltip />} />
              <ReferenceLine x={0} stroke="#9CA3AF" strokeWidth={1.5} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {shapData.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={entry.value >= 0 ? COLOR_POS : COLOR_NEG}
                    fillOpacity={0.85}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Feature importance table */}
      {!loading && shapData.length > 0 && (
        <div className="card">
          <div className="card-title">Feature Contribution Table</div>
          <div className="card-subtitle">Ranked by absolute SHAP value (highest impact first)</div>
          <div className="data-grid-wrap">
            <table className="data-grid">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Feature</th>
                  <th>SHAP Value</th>
                  <th>Direction</th>
                  <th>Impact</th>
                </tr>
              </thead>
              <tbody>
                {shapData.map((row, i) => (
                  <tr key={i}>
                    <td style={{ color: 'var(--color-muted)' }}>#{i + 1}</td>
                    <td><strong>{row.feature}</strong></td>
                    <td style={{ color: row.value >= 0 ? COLOR_POS : COLOR_NEG, fontWeight: 600 }}>
                      {row.value >= 0 ? '+' : ''}{row.value.toFixed(4)}
                    </td>
                    <td>
                      {row.value >= 0
                        ? <span className="tag tag-blue">↑ Increases</span>
                        : <span style={{ background: '#FEE2E2', color: '#991B1B', padding: '3px 10px', borderRadius: 100, fontSize: 11.5, fontWeight: 600 }}>↓ Decreases</span>
                      }
                    </td>
                    <td>
                      <div style={{
                        background: row.value >= 0 ? COLOR_POS : COLOR_NEG,
                        opacity: 0.15 + 0.7 * (Math.abs(row.value) / Math.abs(shapData[0].value)),
                        height: 8, borderRadius: 100,
                        width: `${80 * (Math.abs(row.value) / Math.abs(shapData[0].value))}%`,
                        minWidth: 8,
                        background: row.value >= 0 ? COLOR_POS : COLOR_NEG,
                      }} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Investment recommendations */}
      {!loading && recs.length > 0 && (
        <div className="card">
          <div className="card-title">💡 Investment Recommendations</div>
          <div className="card-subtitle">
            AI-generated actionable insights based on the model's feature analysis
          </div>
          <div className="rec-grid">
            {recs.map((rec, i) => (
              <div className="rec-card" key={i}>
                <span className="rec-icon">{['📈', '🏡', '📍', '🔧', '💰', '🌊'][i % 6]}</span>
                {rec}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
