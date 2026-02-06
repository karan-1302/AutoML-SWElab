// src/pages/Dashboard.js
// User Dashboard - Shows datasets, models, and predictions history
// Feature 1: Show Saved Datasets Immediately After Login

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useApp } from '../context/AppContext';
import Sidebar from '../components/Sidebar';

// ── Styles ─────────────────────────────────────────────────────
const styles = {
    container: {
        padding: '20px',
        maxWidth: '1200px',
        margin: '0 auto',
    },
    header: {
        marginBottom: '30px',
    },
    title: {
        fontSize: '28px',
        fontWeight: 'bold',
        color: '#1a1a2e',
        marginBottom: '8px',
    },
    subtitle: {
        fontSize: '14px',
        color: '#666',
    },
    section: {
        marginBottom: '40px',
    },
    sectionTitle: {
        fontSize: '20px',
        fontWeight: '600',
        color: '#16213e',
        marginBottom: '16px',
        paddingBottom: '8px',
        borderBottom: '2px solid #0f3460',
    },
    card: {
        backgroundColor: '#fff',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '16px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        cursor: 'pointer',
        transition: 'transform 0.2s, box-shadow 0.2s',
    },
    cardHover: {
        transform: 'translateY(-2px)',
        boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
    },
    cardHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '12px',
    },
    cardTitle: {
        fontSize: '16px',
        fontWeight: '600',
        color: '#1a1a2e',
    },
    cardMeta: {
        fontSize: '12px',
        color: '#666',
    },
    badge: {
        backgroundColor: '#0f3460',
        color: '#fff',
        padding: '4px 12px',
        borderRadius: '16px',
        fontSize: '12px',
        fontWeight: '600',
    },
    bestBadge: {
        backgroundColor: '#e94560',
        color: '#fff',
        padding: '4px 12px',
        borderRadius: '16px',
        fontSize: '12px',
        fontWeight: '600',
    },
    modelCard: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    modelInfo: {
        flex: 1,
    },
    modelScore: {
        fontSize: '14px',
        fontWeight: '600',
        color: '#16213e',
    },
    scoreHigh: {
        color: '#27ae60',
    },
    scoreMedium: {
        color: '#f39c12',
    },
    scoreLow: {
        color: '#e74c3c',
    },
    predictSection: {
        backgroundColor: '#f8f9fa',
        borderRadius: '12px',
        padding: '24px',
    },
    predictTitle: {
        fontSize: '18px',
        fontWeight: '600',
        color: '#16213e',
        marginBottom: '16px',
    },
    formGroup: {
        marginBottom: '16px',
    },
    label: {
        display: 'block',
        fontSize: '14px',
        fontWeight: '600',
        color: '#1a1a2e',
        marginBottom: '8px',
    },
    select: {
        width: '100%',
        padding: '12px',
        border: '1px solid #ddd',
        borderRadius: '8px',
        fontSize: '14px',
        backgroundColor: '#fff',
    },
    input: {
        width: '100%',
        padding: '12px',
        border: '1px solid #ddd',
        borderRadius: '8px',
        fontSize: '14px',
    },
    predictButton: {
        backgroundColor: '#0f3460',
        color: '#fff',
        padding: '14px 28px',
        border: 'none',
        borderRadius: '8px',
        fontSize: '16px',
        fontWeight: '600',
        cursor: 'pointer',
        width: '100%',
        transition: 'background-color 0.2s',
    },
    predictButtonHover: {
        backgroundColor: '#16213e',
    },
    resultCard: {
        backgroundColor: '#e8f5e9',
        borderRadius: '12px',
        padding: '20px',
        marginTop: '20px',
    },
    resultTitle: {
        fontSize: '14px',
        fontWeight: '600',
        color: '#27ae60',
        marginBottom: '8px',
    },
    resultValue: {
        fontSize: '32px',
        fontWeight: 'bold',
        color: '#1a1a2e',
    },
    resultConfidence: {
        fontSize: '14px',
        color: '#666',
        marginTop: '8px',
    },
    emptyState: {
        textAlign: 'center',
        padding: '40px',
        color: '#666',
    },
    emptyIcon: {
        fontSize: '48px',
        marginBottom: '16px',
    },
    loading: {
        textAlign: 'center',
        padding: '40px',
        color: '#666',
    },
    spinner: {
        display: 'inline-block',
        width: '24px',
        height: '24px',
        border: '3px solid #ddd',
        borderRadius: '50%',
        borderTopColor: '#0f3460',
        animation: 'spin 1s linear infinite',
    },
    alert: {
        padding: '12px 16px',
        borderRadius: '8px',
        marginBottom: '16px',
        fontSize: '14px',
    },
    alertError: {
        backgroundColor: '#fef2f2',
        color: '#991b1b',
        border: '1px solid #fecaca',
    },
    alertSuccess: {
        backgroundColor: '#f0fdf4',
        color: '#166534',
        border: '1px solid #bbf7d0',
    },
    alertInfo: {
        backgroundColor: '#eff6ff',
        color: '#1e40af',
        border: '1px solid #bfdbfe',
    },
    alertWarning: {
        backgroundColor: '#fffbeb',
        color: '#92400e',
        border: '1px solid #fef3c7',
    },
    retryButton: {
        backgroundColor: '#0f3460',
        color: '#fff',
        padding: '8px 16px',
        border: 'none',
        borderRadius: '6px',
        fontSize: '14px',
        fontWeight: '600',
        cursor: 'pointer',
        marginTop: '12px',
    },
    uploadButton: {
        backgroundColor: '#0f3460',
        color: '#fff',
        padding: '12px 24px',
        border: 'none',
        borderRadius: '8px',
        fontSize: '16px',
        fontWeight: '600',
        cursor: 'pointer',
        marginTop: '16px',
    },
};

// ── Helper Functions ──────────────────────────────────────────
function formatPrice(price) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(price);
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown date';
    try {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    } catch {
        return 'Unknown date';
    }
}

function getScoreColor(r2) {
    if (r2 >= 0.8) return styles.scoreHigh;
    if (r2 >= 0.5) return styles.scoreMedium;
    return styles.scoreLow;
}

// ── Dashboard Component ───────────────────────────────────────
export default function Dashboard() {
    const { apiClient } = useAuth();
    const { user } = useAuth();
    const { dataset, setDataset, bestModel, setBestModel } = useApp();
    const navigate = useNavigate();

    // State
    const [datasets, setDatasets] = useState([]);
    const [models, setModels] = useState([]);
    const [predictions, setPredictions] = useState([]);
    const [selectedDataset, setSelectedDataset] = useState(null);
    const [selectedModel, setSelectedModel] = useState(null);
    const [loading, setLoading] = useState({
        datasets: true,
        models: false,
        predictions: true,
    });
    // Feature 3: Separate error state for API failures vs empty data
    const [datasetError, setDatasetError] = useState(null);
    const [predictionResult, setPredictionResult] = useState(null);
    const [predictionFeatures, setPredictionFeatures] = useState({});
    // Feature 4: Smart prediction with toggles
    const [datasetStats, setDatasetStats] = useState(null);
    const [fieldToggles, setFieldToggles] = useState({});

    // Load user data on mount (Feature 1: Show datasets immediately after login)
    useEffect(() => {
        loadDatasets();
    }, []);

    // Load datasets only
    const loadDatasets = async () => {
        try {
            setLoading(prev => ({ ...prev, datasets: true }));
            setDatasetError(null); // Feature 3: Clear error before fetching
            const datasetsRes = await apiClient.get('/api/user/datasets');
            setDatasets(datasetsRes.data || []);
        } catch (err) {
            console.error('Error loading datasets:', err);
            // Feature 3: Set error state for API failures
            setDatasetError(err.response?.data?.detail || 'Error loading your datasets. Please try again.');
            setDatasets([]); // Clear datasets on error
        } finally {
            setLoading(prev => ({ ...prev, datasets: false }));
        }
    };

    // Load models when dataset changes
    useEffect(() => {
        if (selectedDataset) {
            loadModels(selectedDataset.dataset_id);
        }
    }, [selectedDataset]);

    const loadModels = async (datasetId) => {
        try {
            setLoading(prev => ({ ...prev, models: true }));
            const modelsRes = await apiClient.get(`/api/user/datasets/${datasetId}/models`);
            setModels(modelsRes.data || []);
        } catch (err) {
            console.error('Error loading models:', err);
            // Keep models error separate from dataset error
            setModels([]);
        } finally {
            setLoading(prev => ({ ...prev, models: false }));
        }
    };

    // Handle dataset selection
    const handleDatasetSelect = (ds) => {
        setSelectedDataset(ds);
        setModels([]);
        setSelectedModel(null);
        setPredictionResult(null);
        setPredictionFeatures({});
    };

    // Handle retry button click
    const handleRetry = () => {
        setDatasetError(null);
        loadDatasets();
    };

    // Handle upload button click
    const handleUploadClick = () => {
        navigate('/upload');
    };

    // Handle model selection
    const handleModelSelect = async (model) => {
        setSelectedModel(model);
        setPredictionResult(null);
        setPredictionFeatures({});
        setFieldToggles({});

        // Feature 4: Fetch dataset statistics for smart defaults
        if (selectedDataset) {
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
                    toggles[col] = false; // All toggles start OFF
                });

                setPredictionFeatures(features);
                setFieldToggles(toggles);
            } catch (err) {
                console.error('Error loading dataset stats:', err);
                // Fallback to hardcoded defaults
                const features = {};
                const toggles = {};
                model.feature_columns.forEach(col => {
                    if (col === 'bedrooms') features[col] = 3;
                    else if (col === 'bathrooms') features[col] = 2;
                    else if (col === 'sqft_living') features[col] = 2000;
                    else if (col === 'sqft_lot') features[col] = 5000;
                    else if (col === 'floors') features[col] = 2;
                    else if (col === 'waterfront') features[col] = 0;
                    else if (col === 'view') features[col] = 2;
                    else if (col === 'condition') features[col] = 3;
                    else if (col === 'grade') features[col] = 8;
                    else if (col === 'yr_built') features[col] = 2000;
                    else if (col === 'zipcode') features[col] = '98101';
                    else features[col] = '';
                    toggles[col] = false;
                });
                setPredictionFeatures(features);
                setFieldToggles(toggles);
            }
        }
    };

    // Handle prediction (Feature 4: Smart prediction with partial inputs)
    const handlePredict = async () => {
        if (!selectedModel || !selectedDataset) return;

        try {
            // Feature 4: Send only the fields that are toggled ON
            const userInputs = {};
            Object.keys(fieldToggles).forEach(col => {
                if (fieldToggles[col]) {
                    userInputs[col] = predictionFeatures[col];
                }
            });

            // Use smart endpoint that auto-fills missing fields with averages
            const predictRes = await apiClient.post('/api/predict/smart', {
                dataset_id: selectedDataset.dataset_id,
                target_column: selectedModel.target_column,
                model_name: selectedModel.model_name,
                features: userInputs,
            });

            setPredictionResult(predictRes.data);

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
        } catch (err) {
            console.error('Prediction error:', err);
            // Prediction errors don't affect dataset state
        }
    };

    // Render datasets section (Feature 3: Distinguish between no data vs error)
    const renderDatasets = () => {
        // State 1: Loading
        if (loading.datasets) {
            return (
                <div style={styles.loading}>
                    <div style={styles.spinner} />
                    <p style={{ marginTop: '12px' }}>Loading your datasets...</p>
                </div>
            );
        }

        // State 2: Error (API call failed)
        if (datasetError) {
            return (
                <div style={styles.emptyState}>
                    <div style={{ ...styles.alert, ...styles.alertError }}>
                        <strong>⚠️ Error loading your datasets.</strong> Please try again.
                    </div>
                    <button style={styles.retryButton} onClick={handleRetry}>
                        ↻ Retry
                    </button>
                </div>
            );
        }

        // State 3: No data (API succeeded but returned empty array)
        if (datasets.length === 0) {
            return (
                <div style={styles.emptyState}>
                    <div style={styles.emptyIcon}>📂</div>
                    <p style={{ fontSize: '14px', color: '#666' }}>
                        Please upload a dataset to proceed.
                    </p>
                    <button style={styles.uploadButton} onClick={handleUploadClick}>
                        Upload Dataset
                    </button>
                </div>
            );
        }

        // State 4: Has data (API succeeded and returned datasets)
        return datasets.map(ds => (
            <div
                key={ds.dataset_id}
                style={{
                    ...styles.card,
                    ...(selectedDataset?.dataset_id === ds.dataset_id ? styles.cardHover : {}),
                }}
                onClick={() => handleDatasetSelect(ds)}
            >
                <div style={styles.cardHeader}>
                    <span style={styles.cardTitle}>{ds.filename}</span>
                    <span style={styles.badge}>{ds.row_count} rows</span>
                </div>
                <div style={styles.cardMeta}>
                    {ds.column_count} columns • {ds.quality_score ? `Quality: ${ds.quality_score}%` : 'No quality score'}
                </div>
                <div style={styles.cardMeta}>
                    Uploaded: {formatDate(ds.uploaded_at)}
                </div>
                <div style={{ ...styles.cardMeta, marginTop: '8px' }}>
                    Columns: {ds.columns && ds.columns.length > 0
                        ? ds.columns.slice(0, 5).join(', ') + (ds.columns.length > 5 ? '...' : '')
                        : 'Loading...'}
                </div>
            </div>
        ));
    };

    // Render models section
    const renderModels = () => {
        if (!selectedDataset) {
            return (
                <div style={styles.emptyState}>
                    <div style={styles.emptyIcon}>🤖</div>
                    <p>Select a dataset to see trained models</p>
                </div>
            );
        }

        if (loading.models) {
            return <div style={styles.loading}>Loading models...</div>;
        }

        if (models.length === 0) {
            return (
                <div style={styles.emptyState}>
                    <div style={styles.emptyIcon}>⚙️</div>
                    <p>No models trained for this dataset</p>
                    <button
                        onClick={() => navigate('/train')}
                        style={{ ...styles.predictButton, marginTop: '16px' }}
                    >
                        Train Model
                    </button>
                </div>
            );
        }

        return models.map((model, idx) => {
            const r2 = model.scores?.r2 || 0;
            const scoreStyle = getScoreColor(r2);

            return (
                <div
                    key={idx}
                    style={{
                        ...styles.card,
                        ...(selectedModel?.model_name === model.model_name ? styles.cardHover : {}),
                    }}
                    onClick={() => handleModelSelect(model)}
                >
                    <div style={styles.modelCard}>
                        <div style={styles.modelInfo}>
                            <div style={styles.cardHeader}>
                                <span style={styles.cardTitle}>{model.model_name}</span>
                                {idx === 0 && <span style={styles.bestBadge}>Best Model</span>}
                            </div>
                            <div style={styles.cardMeta}>
                                Target: {model.target_column} • Status: {model.status}
                            </div>
                        </div>
                        <div style={{ ...styles.modelScore, ...scoreStyle }}>
                            R²: {model.scores?.r2?.toFixed(4) || 'N/A'}
                        </div>
                    </div>
                </div>
            );
        });
    };

    // Render quick predict section (Feature 4: Smart prediction with toggles)
    const renderQuickPredict = () => {
        if (!selectedModel || !selectedDataset) {
            return (
                <div style={styles.predictSection}>
                    <div style={styles.predictTitle}>Quick Predict</div>
                    <div style={styles.emptyState}>
                        <p>Select a model to make predictions</p>
                    </div>
                </div>
            );
        }

        return (
            <div style={styles.predictSection}>
                <div style={styles.predictTitle}>Quick Predict (Smart Mode)</div>
                <div style={{ fontSize: '14px', color: '#666', marginBottom: '16px' }}>
                    Using: <strong>{selectedModel.model_name}</strong> for {selectedDataset.filename}
                </div>
                <div style={{ fontSize: '12px', color: '#0066cc', marginBottom: '16px', fontStyle: 'italic' }}>
                    💡 Toggle fields ON to specify custom values. OFF fields use dataset averages.
                </div>

                {/* Feature 4: Dynamic input fields with toggles */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '12px' }}>
                    {selectedModel.feature_columns.map(col => {
                        const isOn = fieldToggles[col] || false;
                        const stat = datasetStats?.[col];
                        const avgLabel = stat?.mean !== undefined
                            ? `(avg: ${stat.mean.toFixed(2)})`
                            : stat?.mode !== undefined
                                ? `(mode: ${stat.mode})`
                                : '';

                        return (
                            <div key={col} style={styles.formGroup}>
                                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
                                    <input
                                        type="checkbox"
                                        checked={isOn}
                                        onChange={(e) => setFieldToggles(prev => ({ ...prev, [col]: e.target.checked }))}
                                        style={{ marginRight: '8px', cursor: 'pointer' }}
                                    />
                                    <label style={{ ...styles.label, marginBottom: 0, cursor: 'pointer' }}>
                                        {col} {!isOn && <span style={{ color: '#999', fontSize: '11px' }}>{avgLabel}</span>}
                                    </label>
                                </div>
                                <input
                                    type={col === 'zipcode' ? 'text' : 'number'}
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
                                        ...styles.input,
                                        backgroundColor: isOn ? '#fff' : '#f5f5f5',
                                        color: isOn ? '#000' : '#999',
                                        cursor: isOn ? 'text' : 'not-allowed',
                                    }}
                                    placeholder={col}
                                    disabled={!isOn}
                                />
                            </div>
                        );
                    })}
                </div>

                <button
                    onClick={handlePredict}
                    style={styles.predictButton}
                    onMouseOver={(e) => e.target.style.backgroundColor = styles.predictButtonHover.backgroundColor}
                    onMouseOut={(e) => e.target.style.backgroundColor = styles.predictButton.backgroundColor}
                >
                    Make Prediction
                </button>

                {/* Prediction result */}
                {predictionResult && (
                    <div style={styles.resultCard}>
                        <div style={styles.resultTitle}>Prediction Result</div>
                        <div style={styles.resultValue}>{formatPrice(predictionResult.predicted_price)}</div>
                        <div style={styles.resultConfidence}>
                            Model: {predictionResult.model_used} • Confidence: {predictionResult.confidence}%
                        </div>

                        {/* Explainability Insights */}
                        {predictionResult.shap_values && predictionResult.shap_values.length > 0 && (
                            <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #e0e0e0' }}>
                                <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: '#16213e' }}>
                                    Top Factors Influencing This Price:
                                </div>
                                {predictionResult.shap_values.slice(0, 3).map((shap, idx) => (
                                    <div key={idx} style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                        padding: '8px 0',
                                        borderBottom: idx < 2 ? '1px solid #f0f0f0' : 'none'
                                    }}>
                                        <div style={{ flex: 1 }}>
                                            <span style={{ fontWeight: 600, fontSize: '12px' }}>{shap.feature}</span>
                                            <span style={{
                                                marginLeft: '8px',
                                                fontSize: '10px',
                                                padding: '2px 6px',
                                                borderRadius: '10px',
                                                backgroundColor: shap.value >= 0 ? '#e8f5e9' : '#ffebee',
                                                color: shap.value >= 0 ? '#27ae60' : '#e74c3c',
                                                fontWeight: 600
                                            }}>
                                                {shap.value >= 0 ? '↑' : '↓'}
                                            </span>
                                        </div>
                                        <div style={{
                                            fontWeight: 600,
                                            fontSize: '12px',
                                            color: shap.value >= 0 ? '#27ae60' : '#e74c3c'
                                        }}>
                                            {shap.value >= 0 ? '+' : ''}{shap.value.toFixed(4)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        );
    };

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <h1 style={styles.title}>User Dashboard</h1>
                <p style={styles.subtitle}>Welcome back, {user?.full_name || 'User'}!</p>
            </div>

            {/* Section A: My Datasets */}
            <div style={styles.section}>
                <h2 style={styles.sectionTitle}>My Datasets</h2>
                {renderDatasets()}
            </div>

            {/* Section B: My Models */}
            <div style={styles.section}>
                <h2 style={styles.sectionTitle}>My Models</h2>
                {renderModels()}
            </div>

            {/* Section C: Quick Predict */}
            <div style={styles.section}>
                <h2 style={styles.sectionTitle}>Quick Predict</h2>
                {renderQuickPredict()}
            </div>
        </div>
    );
}
