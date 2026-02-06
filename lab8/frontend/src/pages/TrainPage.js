// src/pages/TrainPage.js
// Feature 6: Training Page - Upload New or Select Existing Dataset
// UC-04: Initiate AutoML  |  UC-05: Select Target  |  UC-06–08: Train, Evaluate, Select Best Model

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';
import ProgressBar from '../components/ProgressBar';

const ALGORITHMS = ['LinearRegression', 'RandomForest', 'XGBoost'];

export default function TrainPage() {
  const {
    dataset,
    setDataset,
    trainingStatus, setTrainingStatus,
    trainingProgress, setTrainingProgress,
    bestModel, setBestModel,
  } = useApp();

  const { apiClient } = useAuth();
  const navigate = useNavigate();

  // Feature 6: Two-tab state
  const [activeTab, setActiveTab] = useState('existing'); // 'upload' or 'existing'
  const [existingDatasets, setExistingDatasets] = useState([]);
  const [selectedExistingDataset, setSelectedExistingDataset] = useState(null);
  const [loadingDatasets, setLoadingDatasets] = useState(false);

  // Training state
  const [targetCol, setTargetCol] = useState('');
  const [error, setError] = useState('');
  const pollRef = useRef(null);

  // Feature 6: Load existing datasets on mount
  useEffect(() => {
    loadExistingDatasets();
  }, []);

  // Clean up polling on unmount
  useEffect(() => () => clearInterval(pollRef.current), []);

  const loadExistingDatasets = async () => {
    try {
      setLoadingDatasets(true);
      const res = await apiClient.get('/api/user/datasets');
      setExistingDatasets(res.data || []);
    } catch (err) {
      console.error('Error loading datasets:', err);
    } finally {
      setLoadingDatasets(false);
    }
  };

  // Feature 6: Handle selecting an existing dataset
  const handleSelectExistingDataset = async (ds) => {
    setSelectedExistingDataset(ds);
    setError('');

    // Set the dataset in AppContext (same format as upload)
    setDataset({
      datasetId: ds.dataset_id,
      filename: ds.filename,
      columns: ds.columns || [],
      rowCount: ds.row_count,
    });

    // Reset training state
    setTrainingStatus('idle');
    setTrainingProgress({});
    setBestModel(null);
    setTargetCol('');
  };

  // Start training
  const handleStartTraining = async () => {
    if (!targetCol) { setError('Please select a target variable.'); return; }
    if (!dataset) { setError('Please select a dataset first.'); return; }

    setError('');
    setTrainingStatus('running');
    setTrainingProgress({});
    setBestModel(null);

    try {
      await apiClient.post('/api/train/start', {
        dataset_id: dataset.datasetId,
        target_column: targetCol,
      });

      // Poll for progress every 2 seconds
      pollRef.current = setInterval(async () => {
        try {
          const res = await apiClient.get('/api/train/status');
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

  const isRunning = trainingStatus === 'running';
  const isDone = trainingStatus === 'done';

  // Tab styles
  const tabStyle = (isActive) => ({
    flex: 1,
    padding: '12px 24px',
    border: 'none',
    borderBottom: isActive ? '3px solid #0066cc' : '3px solid transparent',
    backgroundColor: isActive ? '#f0f7ff' : 'transparent',
    color: isActive ? '#0066cc' : '#666',
    fontWeight: isActive ? 600 : 400,
    cursor: 'pointer',
    transition: 'all 0.2s',
  });

  return (
    <div>
      <div className="page-header">
        <h1>AutoML Training</h1>
        <p>Upload a new dataset or select an existing one to train models</p>
      </div>

      {/* Feature 6: Two-tab layout for dataset selection */}
      {!dataset && (
        <div className="card">
          <div className="card-title">Step 1 — Choose Dataset Source</div>

          {/* Tab buttons */}
          <div style={{ display: 'flex', borderBottom: '1px solid #ddd', marginBottom: '20px' }}>
            <button
              style={tabStyle(activeTab === 'existing')}
              onClick={() => setActiveTab('existing')}
            >
              Select Existing Dataset
            </button>
            <button
              style={tabStyle(activeTab === 'upload')}
              onClick={() => setActiveTab('upload')}
            >
              Upload New Dataset
            </button>
          </div>

          {error && <div className="alert alert-error">! {error}</div>}

          {/* Tab content: Existing datasets */}
          {activeTab === 'existing' && (
            <div>
              {loadingDatasets ? (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <span className="spinner" /> Loading your datasets...
                </div>
              ) : existingDatasets.length === 0 ? (
                <div className="alert alert-warning">
                  No datasets found. Please upload a dataset first or switch to the "Upload New Dataset" tab.
                </div>
              ) : (
                <div>
                  <div className="card-subtitle" style={{ marginBottom: '16px' }}>
                    Select a dataset to train models on:
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {existingDatasets.map(ds => (
                      <div
                        key={ds.dataset_id}
                        onClick={() => handleSelectExistingDataset(ds)}
                        style={{
                          padding: '16px',
                          border: selectedExistingDataset?.dataset_id === ds.dataset_id ? '2px solid #0066cc' : '1px solid #ddd',
                          borderRadius: '8px',
                          cursor: 'pointer',
                          backgroundColor: selectedExistingDataset?.dataset_id === ds.dataset_id ? '#f0f7ff' : '#fff',
                          transition: 'all 0.2s',
                        }}
                      >
                        <div style={{ fontWeight: 600, marginBottom: '4px' }}>{ds.filename}</div>
                        <div style={{ fontSize: '13px', color: '#666' }}>
                          {ds.row_count} rows • {ds.column_count} columns
                          {ds.quality_score && ` • Quality: ${ds.quality_score}%`}
                        </div>
                        {ds.columns && ds.columns.length > 0 && (
                          <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
                            Columns: {ds.columns.slice(0, 5).join(', ')}{ds.columns.length > 5 ? '...' : ''}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tab content: Upload new */}
          {activeTab === 'upload' && (
            <div>
              <div className="alert alert-info">
                ℹ️ To upload a new dataset, please go to the <a href="/upload" style={{ color: 'inherit', fontWeight: 700 }}>Upload page</a>.
                After uploading, return here to train models.
              </div>
              <button
                className="btn btn-primary"
                onClick={() => navigate('/upload')}
                style={{ marginTop: '12px' }}
              >
                Go to Upload Page →
              </button>
            </div>
          )}
        </div>
      )}

      {/* Step 2: Training configuration (shown after dataset is selected) */}
      {dataset && (
        <div className="card">
          <div className="card-title">Step 2 — Configure Training</div>
          <div className="card-subtitle">
            Dataset: <strong>{dataset.filename}</strong> &nbsp;·&nbsp; {dataset.rowCount.toLocaleString()} rows
            <button
              onClick={() => {
                setDataset(null);
                setSelectedExistingDataset(null);
                setTargetCol('');
                setTrainingStatus('idle');
                setTrainingProgress({});
                setBestModel(null);
              }}
              style={{
                marginLeft: '12px',
                padding: '4px 12px',
                fontSize: '12px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                backgroundColor: '#fff',
                cursor: 'pointer',
              }}
            >
              Change Dataset
            </button>
          </div>

          {error && <div className="alert alert-error">! {error}</div>}

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
                'Start AutoML'
              )}
            </button>
          </div>

          {isRunning && (
            <div className="alert alert-info mt-4">
              AutoML is evaluating {ALGORITHMS.length} algorithms. This may take a few minutes.
            </div>
          )}
        </div>
      )}

      {/* Step 3: Progress */}
      {(isRunning || isDone) && (
        <div className="card">
          <div className="card-title">Step 3 — Training Progress</div>
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

      {/* Step 4: Best model banner */}
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
              Predict Now
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
