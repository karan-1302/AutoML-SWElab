// src/pages/TrainPage.js
// UC-04: Initiate AutoML  |  UC-05: Select Target  |  UC-06–08: Train, Evaluate, Select Best Model
// Triggers the AutoML pipeline and polls for per-algorithm progress via SSE / polling.

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useApp } from '../context/AppContext';
import ProgressBar from '../components/ProgressBar';

const ALGORITHMS = ['LinearRegression', 'RandomForest', 'XGBoost'];

export default function TrainPage() {
  const {
    dataset,
    trainingStatus, setTrainingStatus,
    trainingProgress, setTrainingProgress,
    bestModel, setBestModel,
  } = useApp();

  const [targetCol, setTargetCol] = useState('');
  const [error,     setError]     = useState('');
  const pollRef = useRef(null);
  const navigate = useNavigate();

  // ── Clean up polling on unmount ───────────────────────────
  useEffect(() => () => clearInterval(pollRef.current), []);

  // ── Start training ────────────────────────────────────────
  const handleStartTraining = async () => {
    if (!targetCol) { setError('Please select a target variable.'); return; }
    setError('');
    setTrainingStatus('running');
    setTrainingProgress({});
    setBestModel(null);

    try {
      await axios.post('/api/train/start', {
        dataset_id:    dataset.datasetId,
        target_column: targetCol,
      });

      // Poll for progress every 2 seconds
      pollRef.current = setInterval(async () => {
        try {
          const res = await axios.get('/api/train/status');
          setTrainingProgress(res.data.progress);

          if (res.data.complete) {
            clearInterval(pollRef.current);
            setBestModel(res.data.best_model);
            setTrainingStatus('done');
          }
        } catch {
          // swallow poll errors — backend may be busy
        }
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start training. Please try again.');
      setTrainingStatus('idle');
    }
  };

  // ── Guard: need a dataset ─────────────────────────────────
  if (!dataset) {
    return (
      <div>
        <div className="page-header">
          <h1>🤖 AutoML Training</h1>
          <p>Train multiple ML models and select the best one automatically</p>
        </div>
        <div className="card">
          <div className="alert alert-warning">
            ⚠ No dataset found. Please <a href="/upload" style={{ color: 'inherit', fontWeight: 700 }}>upload a dataset</a> first.
          </div>
        </div>
      </div>
    );
  }

  const isRunning = trainingStatus === 'running';
  const isDone    = trainingStatus === 'done';

  return (
    <div>
      <div className="page-header">
        <h1>🤖 AutoML Training</h1>
        <p>Select a target variable and let AutoML find the best model for you</p>
      </div>

      {/* Step 1: Target selection */}
      <div className="card">
        <div className="card-title">Step 1 — Configure Training</div>
        <div className="card-subtitle">
          Dataset: <strong>{dataset.filename}</strong> &nbsp;·&nbsp; {dataset.rowCount.toLocaleString()} rows
        </div>

        {error && <div className="alert alert-error">⚠ {error}</div>}

        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div className="form-group" style={{ flex: 1, minWidth: 220, marginBottom: 0 }}>
            <label className="form-label" htmlFor="target">Target Variable (Column to Predict)</label>
            <select
              id="target"
              className="form-control"
              value={targetCol}
              onChange={e => setTargetCol(e.target.value)}
              disabled={isRunning || isDone}
            >
              <option value="">-- Select column --</option>
              {dataset.columns.map(col => (
                <option key={col} value={col}>{col}</option>
              ))}
            </select>
          </div>

          <button
            className="btn btn-primary"
            onClick={handleStartTraining}
            disabled={!targetCol || isRunning || isDone}
            style={{ minWidth: 160 }}
          >
            {isRunning ? (
              <><span className="spinner" /> Training…</>
            ) : isDone ? (
              '✓ Training Complete'
            ) : (
              '▶ Start AutoML'
            )}
          </button>
        </div>

        {isRunning && (
          <div className="alert alert-info mt-4">
            🔄 AutoML is evaluating {ALGORITHMS.length} algorithms. This may take a few minutes.
          </div>
        )}
      </div>

      {/* Step 2: Progress */}
      {(isRunning || isDone) && (
        <div className="card">
          <div className="card-title">Step 2 — Training Progress</div>
          <div className="card-subtitle">
            Target: <span className="tag tag-blue">{targetCol}</span>
          </div>

          <div className="progress-list">
            {ALGORITHMS.map(algo => (
              <ProgressBar
                key={algo}
                label={algo}
                value={trainingProgress[algo] || 0}
                score={trainingProgress[`${algo}_score`] || null}
              />
            ))}
          </div>
        </div>
      )}

      {/* Step 3: Best model banner */}
      {isDone && bestModel && (
        <div>
          <div className="best-model-banner">
            <span className="trophy">🏆</span>
            <div>
              <h3>Best Model: {bestModel.name}</h3>
              <p>
                RMSE: {Number(bestModel.rmse).toFixed(2)} &nbsp;·&nbsp;
                R²: {Number(bestModel.r2).toFixed(4)} &nbsp;·&nbsp;
                MAE: {Number(bestModel.mae).toFixed(2)}
              </p>
            </div>
            <button
              className="btn"
              style={{ marginLeft: 'auto', background: '#fff', color: 'var(--color-primary)' }}
              onClick={() => navigate('/predict')}
            >
              Predict Now →
            </button>
          </div>

          {/* All model scores */}
          <div className="card mt-4">
            <div className="card-title">Model Comparison</div>
            <div className="card-subtitle">All models evaluated on the test split (80/20)</div>
            <div className="data-grid-wrap">
              <table className="data-grid">
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>R² Score</th>
                    <th>RMSE</th>
                    <th>MAE</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {(bestModel.all_models || [bestModel]).map((m, i) => (
                    <tr key={i}>
                      <td><strong>{m.name}</strong></td>
                      <td>{Number(m.r2).toFixed(4)}</td>
                      <td>{Number(m.rmse).toFixed(2)}</td>
                      <td>{Number(m.mae).toFixed(2)}</td>
                      <td>
                        {m.name === bestModel.name
                          ? <span className="tag tag-green">✓ Selected</span>
                          : <span className="tag tag-blue">Evaluated</span>
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
