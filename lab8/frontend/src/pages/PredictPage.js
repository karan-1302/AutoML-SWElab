// src/pages/PredictPage.js
// Feature 5: Prediction Page - Load Model from Existing Datasets
// UC-09: Generate Prediction  |  UC-10: Reuse Trained Model

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function formatPrice(val) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);
}

function formatDate(dateString) {
  if (!dateString) return 'Unknown date';
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return 'Unknown date';
  }
}

export default function PredictPage() {
  const { apiClient } = useAuth();
  const navigate = useNavigate();

  // State
  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [datasetStats, setDatasetStats] = useState(null);
  const [fieldToggles, setFieldToggles] = useState({});
  const [predictionFeatures, setPredictionFeatures] = useState({});
  const [predictionResult, setPredictionResult] = useState(null);
  const [loading, setLoading] = useState({
    datasets: true,
    models: false,
    predicting: false,
  });
  const [error, setError] = useState('');

  // Load datasets on mount
  useEffect(() => {
    loadDatasets();
  }, []);

  // Load models when dataset changes
  useEffect(() => {
    if (selectedDataset) {
      loadModels(selectedDataset.dataset_id);
    }
  }, [selectedDataset]);

  const loadDatasets = async () => {
    try {
      setLoading(prev => ({ ...prev, datasets: true }));
      const res = await apiClient.get('/api/user/datasets');
      setDatasets(res.data || []);
    } catch (err) {
      console.error('Error loading datasets:', err);
      setError('Failed to load datasets. Please try again.');
    } finally {
      setLoading(prev => ({ ...prev, datasets: false }));
    }
  };

  const loadModels = async (datasetId) => {
    try {
      setLoading(prev => ({ ...prev, models: true }));
      const res = await apiClient.get(`/api/user/datasets/${datasetId}/models`);
      setModels(res.data || []);
      setSelectedModel(null);
      setPredictionResult(null);
    } catch (err) {
      console.error('Error loading models:', err);
      setModels([]);
    } finally {
      setLoading(prev => ({ ...prev, models: false }));
    }
  };

  const handleDatasetSelect = (dataset) => {
    setSelectedDataset(dataset);
    setSelectedModel(null);
    setModels([]);
    setPredictionResult(null);
    setError('');
  };

  const handleModelSelect = async (model) => {
    setSelectedModel(model);
    setPredictionResult(null);
    setError('');

    // Load dataset stats for smart defaults
    try {
      const statsRes = await apiClient.get(`/api/user/datasets/${selectedDataset.dataset_id}/stats`);
      setDatasetStats(statsRes.data);

      // Initialize features with averages and all toggles OFF
      const features = {};
      const toggles = {};

      model.feature_columns.forEach(col => {
        const stat = statsRes.data[col];
        if (stat && stat.mean !== undefined) {
          features[col] = stat.mean;
        } else if (stat && stat.mode !== undefined) {
          features[col] = stat.mode;
        } else {
          features[col] = '';
        }
        toggles[col] = false;
      });

      setPredictionFeatures(features);
      setFieldToggles(toggles);
    } catch (err) {
      console.error('Error loading dataset stats:', err);
    }
  };

  const handlePredict = async () => {
    if (!selectedModel || !selectedDataset) return;

    try {
      setLoading(prev => ({ ...prev, predicting: true }));
      setError('');

      // Send only toggled-ON fields
      const userInputs = {};
      Object.keys(fieldToggles).forEach(col => {
        if (fieldToggles[col]) {
          userInputs[col] = predictionFeatures[col];
        }
      });

      const res = await apiClient.post('/api/predict/smart', {
        dataset_id: selectedDataset.dataset_id,
        target_column: selectedModel.target_column,
        model_name: selectedModel.model_name,
        features: userInputs,
      });

      setPredictionResult(res.data);

      // Fetch explainability insights automatically
      try {
        const explainRes = await apiClient.get('/api/explain/latest');
        setPredictionResult(prev => ({
          ...prev,
          shap_values: explainRes.data.shap_values || [],
          recommendations: explainRes.data.recommendations || [],
        }));
      } catch (explainErr) {
        console.error('Error loading explainability:', explainErr);
        // Don't fail the prediction if explainability fails
      }

      setTimeout(() => document.getElementById('result-card')?.scrollIntoView({ behavior: 'smooth' }), 100);
    } catch (err) {
      console.error('Prediction error:', err);
      setError(err.response?.data?.detail || 'Prediction failed. Please try again.');
    } finally {
      setLoading(prev => ({ ...prev, predicting: false }));
    }
  };

  const handleTrainNew = () => {
    navigate('/train');
  };

  return (
    <div>
      <div className="page-header">
        <h1>Predict Property Price</h1>
        <p>Select a dataset and trained model to generate predictions</p>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: 20 }}>
          ⚠️ {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Left column: Dataset & Model Selection */}
        <div>
          {/* Step 1: Select Dataset */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-title">Step 1: Select a Dataset</div>
            <div className="card-subtitle">Choose a dataset you've uploaded</div>

            {loading.datasets ? (
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <span className="spinner" /> Loading datasets...
              </div>
            ) : datasets.length === 0 ? (
              <div className="alert alert-warning">
                No datasets found. Please <a href="/upload" style={{ color: 'inherit', fontWeight: 700 }}>upload a dataset</a> first.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {datasets.map(ds => (
                  <div
                    key={ds.dataset_id}
                    onClick={() => handleDatasetSelect(ds)}
                    style={{
                      padding: '12px',
                      border: selectedDataset?.dataset_id === ds.dataset_id ? '2px solid #0066cc' : '1px solid #ddd',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      backgroundColor: selectedDataset?.dataset_id === ds.dataset_id ? '#f0f7ff' : '#fff',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ fontWeight: 600, marginBottom: '4px' }}>{ds.filename}</div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      {ds.row_count} rows • {ds.column_count} columns
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Step 2: Select Model */}
          {selectedDataset && (
            <div className="card">
              <div className="card-title">Step 2: Select a Trained Model</div>
              <div className="card-subtitle">Choose a model trained on {selectedDataset.filename}</div>

              {loading.models ? (
                <div style={{ textAlign: 'center', padding: '20px' }}>
                  <span className="spinner" /> Loading models...
                </div>
              ) : models.length === 0 ? (
                <div>
                  <div className="alert alert-warning">
                    No models trained yet. Would you like to train one?
                  </div>
                  <button
                    className="btn btn-primary w-full"
                    style={{ justifyContent: 'center', marginTop: '12px' }}
                    onClick={handleTrainNew}
                  >
                    Train Model
                  </button>
                </div>
              ) : (
                <div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '12px' }}>
                    {models.map((model, idx) => (
                      <div
                        key={idx}
                        onClick={() => handleModelSelect(model)}
                        style={{
                          padding: '12px',
                          border: selectedModel?.model_name === model.model_name ? '2px solid #0066cc' : '1px solid #ddd',
                          borderRadius: '8px',
                          cursor: 'pointer',
                          backgroundColor: selectedModel?.model_name === model.model_name ? '#f0f7ff' : '#fff',
                          transition: 'all 0.2s',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div>
                            <div style={{ fontWeight: 600, marginBottom: '4px' }}>
                              {model.model_name}
                              {idx === 0 && <span style={{ marginLeft: '8px', fontSize: '11px', backgroundColor: '#e94560', color: '#fff', padding: '2px 8px', borderRadius: '12px' }}>Best</span>}
                            </div>
                            <div style={{ fontSize: '12px', color: '#666' }}>
                              Target: {model.target_column} • Trained: {formatDate(model.trained_at)}
                            </div>
                          </div>
                          <div style={{ fontSize: '14px', fontWeight: 600, color: model.scores?.r2 >= 0.8 ? '#27ae60' : '#f39c12' }}>
                            R²: {model.scores?.r2?.toFixed(4) || 'N/A'}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <button
                    className="btn btn-ghost w-full"
                    style={{ justifyContent: 'center' }}
                    onClick={handleTrainNew}
                  >
                    + Train New Model
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right column: Prediction Form & Result */}
        <div>
          {selectedModel ? (
            <div className="card">
              <div className="card-title">Step 3: Enter Property Features</div>
              <div className="card-subtitle">
                Using: <strong>{selectedModel.model_name}</strong>
              </div>
              <div className="card-subtitle" style={{ marginBottom: '16px', fontStyle: 'italic' }}>
                Toggle fields ON to specify custom values. OFF fields use dataset averages.
              </div>

              {/* Feature inputs with toggles */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                {selectedModel.feature_columns.map(col => {
                  const isOn = fieldToggles[col] || false;
                  const stat = datasetStats?.[col];
                  const avgLabel = stat?.mean !== undefined
                    ? `(avg: ${stat.mean.toFixed(2)})`
                    : stat?.mode !== undefined
                      ? `(mode: ${stat.mode})`
                      : '';

                  return (
                    <div key={col} className="form-group">
                      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
                        <input
                          type="checkbox"
                          checked={isOn}
                          onChange={(e) => setFieldToggles(prev => ({ ...prev, [col]: e.target.checked }))}
                          style={{ marginRight: '8px', cursor: 'pointer' }}
                        />
                        <label className="form-label" style={{ marginBottom: 0, cursor: 'pointer', fontSize: '13px' }}>
                          {col} {!isOn && <span style={{ color: '#999', fontSize: '11px' }}>{avgLabel}</span>}
                        </label>
                      </div>
                      <input
                        type={col === 'zipcode' ? 'text' :
                          ['bedrooms', 'bathrooms', 'floors', 'waterfront', 'view', 'condition', 'grade', 'yr_built'].includes(col) ? 'number' : 'number'}
                        className="form-control"
                        value={predictionFeatures[col] || ''}
                        onChange={(e) => {
                          let value = e.target.value;
                          // Handle integer fields
                          if (['bedrooms', 'bathrooms', 'floors', 'waterfront', 'view', 'condition', 'grade', 'yr_built'].includes(col)) {
                            value = value === '' ? '' : parseInt(value) || 0;
                          }
                          // Handle float fields
                          else if (col !== 'zipcode') {
                            value = value === '' ? '' : parseFloat(value) || 0;
                          }
                          setPredictionFeatures(prev => ({ ...prev, [col]: value }));
                        }}
                        style={{
                          backgroundColor: isOn ? '#fff' : '#f5f5f5',
                          color: isOn ? '#000' : '#999',
                          cursor: isOn ? 'text' : 'not-allowed',
                        }}
                        placeholder={col}
                        disabled={!isOn}
                        step={['bedrooms', 'bathrooms', 'floors', 'waterfront', 'view', 'condition', 'grade', 'yr_built'].includes(col) ? '1' : '0.01'}
                        min={col === 'yr_built' ? '1800' : '0'}
                        max={col === 'bedrooms' ? '20' : col === 'bathrooms' ? '10' : col === 'floors' ? '5' : col === 'waterfront' ? '1' : col === 'view' ? '4' : col === 'condition' ? '5' : col === 'grade' ? '13' : col === 'yr_built' ? '2025' : undefined}
                      />
                    </div>
                  );
                })}
              </div>

              <button
                className="btn btn-primary w-full"
                style={{ justifyContent: 'center', padding: '12px' }}
                onClick={handlePredict}
                disabled={loading.predicting}
              >
                {loading.predicting ? (
                  <><span className="spinner" /> Calculating…</>
                ) : 'Get Price Estimate'}
              </button>

              {/* Prediction result */}
              {predictionResult && (
                <div id="result-card" style={{ marginTop: '20px' }}>
                  <div className="price-result">
                    <div className="price-label">Estimated Market Value</div>
                    <div className="price-value">{formatPrice(predictionResult.predicted_price)}</div>
                    <div className="price-meta">
                      Model: {predictionResult.model_used} • Confidence: {predictionResult.confidence}%
                    </div>
                  </div>

                  {/* Explainability Insights */}
                  {predictionResult.shap_values && predictionResult.shap_values.length > 0 && (
                    <div style={{ marginTop: '20px' }}>
                      <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px', color: '#16213e' }}>
                        Prediction Insights
                      </div>

                      {/* Top 3 SHAP features */}
                      <div style={{ backgroundColor: '#f8f9fa', borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
                        <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '12px', color: '#666' }}>
                          Top Factors Influencing This Price:
                        </div>
                        {predictionResult.shap_values.slice(0, 3).map((shap, idx) => (
                          <div key={idx} style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '8px 0',
                            borderBottom: idx < 2 ? '1px solid #e0e0e0' : 'none'
                          }}>
                            <div style={{ flex: 1 }}>
                              <span style={{ fontWeight: 600, fontSize: '13px' }}>{shap.feature}</span>
                              <span style={{
                                marginLeft: '8px',
                                fontSize: '11px',
                                padding: '2px 8px',
                                borderRadius: '12px',
                                backgroundColor: shap.value >= 0 ? '#e8f5e9' : '#ffebee',
                                color: shap.value >= 0 ? '#27ae60' : '#e74c3c',
                                fontWeight: 600
                              }}>
                                {shap.value >= 0 ? '↑' : '↓'} {shap.value >= 0 ? 'Increases' : 'Decreases'}
                              </span>
                            </div>
                            <div style={{
                              fontWeight: 600,
                              fontSize: '13px',
                              color: shap.value >= 0 ? '#27ae60' : '#e74c3c'
                            }}>
                              {shap.value >= 0 ? '+' : ''}{shap.value.toFixed(4)}
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Recommendations */}
                      {predictionResult.recommendations && predictionResult.recommendations.length > 0 && (
                        <div>
                          <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '12px', color: '#666' }}>
                            Investment Recommendations:
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {predictionResult.recommendations.slice(0, 3).map((rec, idx) => (
                              <div key={idx} style={{
                                backgroundColor: '#fff',
                                border: '1px solid #e0e0e0',
                                borderRadius: '8px',
                                padding: '12px',
                                fontSize: '12px',
                                lineHeight: '1.5',
                                color: '#333'
                              }}>
                                {rec}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Link to full explainability page */}
                      <button
                        onClick={() => navigate('/explain')}
                        style={{
                          marginTop: '16px',
                          width: '100%',
                          padding: '10px',
                          backgroundColor: '#f0f7ff',
                          border: '1px solid #0066cc',
                          borderRadius: '6px',
                          color: '#0066cc',
                          fontSize: '13px',
                          fontWeight: 600,
                          cursor: 'pointer',
                          transition: 'all 0.2s'
                        }}
                        onMouseOver={(e) => e.target.style.backgroundColor = '#e6f2ff'}
                        onMouseOut={(e) => e.target.style.backgroundColor = '#f0f7ff'}
                      >
                        View Full Explainability Analysis →
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '60px 24px' }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>🎯</div>
              <div className="card-title">Select a dataset and model</div>
              <p className="text-muted" style={{ fontSize: 13 }}>
                Choose a dataset and trained model from the left to begin making predictions.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
