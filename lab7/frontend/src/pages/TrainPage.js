// src/pages/TrainPage.js
// UC-04: Initiate AutoML  |  UC-05: Select Target  |  UC-06–08: Train, Evaluate, Select Best Model
// Enhanced to show BLL validation (target column type, dataset size, concurrent check)
//   - BR-TRN-01: Dataset existence
//   - BR-TRN-02: Target column existence
//   - BR-TRN-03: Target must be numeric
//   - BR-TRN-04: No concurrent training
//   - BR-TRN-05: Min 20 rows
//   - DT-TRN-01/02: Status/progress transformation

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

  const [targetCol,  setTargetCol]  = useState('');
  const [error,      setError]      = useState('');
  const [allModels,  setAllModels]  = useState([]);
  const pollRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => () => clearInterval(pollRef.current), []);

  const handleStartTraining = async () => {
    if (!targetCol) { setError('Please select a target variable (BR-TRN-02).'); return; }
    setError('');
    setTrainingStatus('running');
    setTrainingProgress({});
    setBestModel(null);
    setAllModels([]);

    try {
      await axios.post('/api/train/start', {
        dataset_id:    dataset.datasetId,
        target_column: targetCol,
      });

      pollRef.current = setInterval(async () => {
        try {
          const res = await axios.get('/api/train/status');
          setTrainingProgress(res.data.progress);

          if (res.data.complete) {
            clearInterval(pollRef.current);
            setBestModel(res.data.best_model);
            setAllModels(res.data.all_models || []);
            setTrainingStatus('done');
          }
        } catch {
          // swallow poll errors
        }
      }, 2000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.join(' '));
      } else {
        setError(detail || 'Failed to start training. Please try again.');
      }
      setTrainingStatus('idle');
    }
  };

  if (!dataset) {
    return (
      <div>
        <div className="page-header">
          <h1>🤖 AutoML Training</h1>
          <p>Train multiple ML models and select the best one automatically</p>
        </div>
        <div className="card">
          <div className="alert alert-warning">
            ⚠ No dataset found (BR-TRN-01). Please <a href="/upload" style={{ color: 'inherit', fontWeight: 700 }}>upload a dataset</a> first.
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

        {/* BLL validation info */}
        <div style={{ background: 'rgba(46,117,182,0.05)', borderRadius: 8, padding: '10px 14px', marginTop: 16 }}>
          <div style={{ fontSize: 11, color: '#6B7280', fontWeight: 600, marginBottom: 4 }}>
            🔧 BLL Validations (train_bll.py)
          </div>
          <div style={{ fontSize: 11, color: '#9CA3AF' }}>
            BR-TRN-02: Target column must exist &nbsp;·&nbsp;
            BR-TRN-03: Target must be numeric &nbsp;·&nbsp;
            BR-TRN-04: No concurrent training &nbsp;·&nbsp;
            BR-TRN-05: Min 20 rows required
          </div>
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
          <div className="card-title">Step 2 — Training Progress (DT-TRN-01/02)</div>
          <div className="card-subtitle">
            Target: <span className="tag tag-blue">{targetCol}</span>
            &nbsp;&nbsp;
            <span style={{ fontSize: 11, color: '#9CA3AF' }}>
              Progress data transformed by BLL for presentation
            </span>
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
              <h3>Best Model: {bestModel.name} (BR-TRN-06: Selected by R²)</h3>
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
            <div className="card-title">Model Comparison (BR-TRN-07: Rounded Scores)</div>
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
                  {(allModels.length > 0 ? allModels : [bestModel]).map((m, i) => (
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
