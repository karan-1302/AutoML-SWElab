// src/pages/UploadPage.js
// UC-01: Upload Dataset  |  UC-02: Preview Dataset
// Drag-and-drop CSV upload → validates → sends to ingestion service → shows DataGrid preview.

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useApp } from '../context/AppContext';
import DataGrid from '../components/DataGrid';

export default function UploadPage() {
  const [status,  setStatus]  = useState('idle'); // 'idle'|'uploading'|'done'|'error'
  const [message, setMessage] = useState('');
  const { dataset, setDataset } = useApp();
  const navigate = useNavigate();

  // ── Drop handler ──────────────────────────────────────────
  const onDrop = useCallback(async (acceptedFiles, rejectedFiles) => {
    // Validate: only CSV allowed
    if (rejectedFiles.length > 0) {
      setStatus('error');
      setMessage('Only .csv files are accepted. Please try again.');
      return;
    }

    const file = acceptedFiles[0];
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setStatus('error');
      setMessage('Invalid file type. Please upload a CSV file.');
      return;
    }

    setStatus('uploading');
    setMessage('');

    try {
      const form = new FormData();
      form.append('file', file);

      const res = await axios.post('/api/ingest/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      // res.data: { dataset_id, filename, columns, preview, row_count }
      setDataset({
        datasetId: res.data.dataset_id,
        filename:  res.data.filename,
        columns:   res.data.columns,
        preview:   res.data.preview,
        rowCount:  res.data.row_count,
      });
      setStatus('done');
      setMessage(`Successfully uploaded "${res.data.filename}" with ${res.data.row_count} rows.`);
    } catch (err) {
      setStatus('error');
      setMessage(err.response?.data?.detail || 'Upload failed. Please try again.');
    }
  }, [setDataset]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1,
    multiple: false,
  });

  // ── Render ────────────────────────────────────────────────
  return (
    <div>
      <div className="page-header">
        <h1>📂 Upload Dataset</h1>
        <p>Upload a real estate CSV dataset to begin the AutoML pipeline</p>
      </div>

      {/* Step 1: Drop zone */}
      <div className="card">
        <div className="card-title">Step 1 — Select Your Dataset</div>
        <div className="card-subtitle">
          Supported format: CSV with property features (bedrooms, area, location, price, etc.)
        </div>

        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? 'active' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="dropzone-icon">
            {status === 'uploading' ? '⏳' : isDragActive ? '📥' : '📄'}
          </div>
          {status === 'uploading' ? (
            <p>Uploading and validating… please wait.</p>
          ) : isDragActive ? (
            <p><strong>Drop it here!</strong></p>
          ) : (
            <p>
              <strong>Drag & drop a CSV file here</strong>
              <br />or click to browse
            </p>
          )}
        </div>

        {/* Feedback messages */}
        {status === 'done' && (
          <div className="alert alert-success mt-4">
            ✓ {message}
          </div>
        )}
        {status === 'error' && (
          <div className="alert alert-error mt-4">
            ⚠ {message}
          </div>
        )}
      </div>

      {/* Step 2: Preview */}
      {dataset && (
        <div className="card">
          <div className="flex-between mb-4">
            <div>
              <div className="card-title">Step 2 — Dataset Preview</div>
              <div className="card-subtitle" style={{ marginBottom: 0 }}>
                {dataset.filename} &nbsp;·&nbsp;
                <span className="tag tag-blue">{dataset.rowCount.toLocaleString()} rows</span>
                &nbsp;&nbsp;
                <span className="tag tag-orange">{dataset.columns.length} columns</span>
              </div>
            </div>
            <button
              className="btn btn-primary"
              onClick={() => navigate('/train')}
            >
              Proceed to Training →
            </button>
          </div>

          {/* Column chips */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 20 }}>
            {dataset.columns.map(col => (
              <span key={col} className="tag tag-blue">{col}</span>
            ))}
          </div>

          {/* Data grid */}
          <DataGrid columns={dataset.columns} rows={dataset.preview} />
        </div>
      )}

      {/* Instructions if no dataset yet */}
      {!dataset && status === 'idle' && (
        <div className="card mt-4">
          <div className="card-title">Expected Dataset Format</div>
          <div className="card-subtitle">Your CSV should contain columns such as:</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {['bedrooms', 'bathrooms', 'sqft_living', 'sqft_lot', 'floors',
              'waterfront', 'view', 'condition', 'grade', 'yr_built',
              'zipcode', 'lat', 'long', 'price'].map(c => (
              <span key={c} className="tag tag-blue">{c}</span>
            ))}
          </div>
          <p className="text-muted mt-4" style={{ fontSize: 13 }}>
            The <strong>price</strong> (or equivalent) column will be used as the prediction target in the next step.
          </p>
        </div>
      )}
    </div>
  );
}
