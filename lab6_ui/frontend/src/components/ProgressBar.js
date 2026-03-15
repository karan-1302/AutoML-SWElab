// src/components/ProgressBar.js

import React from 'react';

export default function ProgressBar({ label, value = 0, score = null }) {
  const done = value >= 100;
  return (
    <div className="progress-item">
      <div className="progress-header">
        <span className="progress-name">{label}</span>
        <div className="flex gap-2" style={{ alignItems: 'center' }}>
          {score !== null && done && (
            <span className="tag tag-green" style={{ fontSize: 11 }}>
              R² = {Number(score).toFixed(4)}
            </span>
          )}
          <span className="progress-pct">{done ? '✓ Done' : `${value}%`}</span>
        </div>
      </div>
      <div className="progress-bar-bg">
        <div
          className={`progress-bar-fill ${done ? 'done' : ''}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}
