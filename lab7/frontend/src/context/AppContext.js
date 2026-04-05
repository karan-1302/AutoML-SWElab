// src/context/AppContext.js
// Shares uploaded dataset metadata and trained model info across pages.

import React, { createContext, useContext, useState } from 'react';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  // Dataset state
  const [dataset, setDataset] = useState(null);
  // { datasetId, filename, columns, preview: [{...}], rowCount }

  // Training state
  const [trainingStatus, setTrainingStatus] = useState('idle');
  // 'idle' | 'running' | 'done' | 'error'
  const [trainingProgress, setTrainingProgress] = useState({});
  // { RandomForest: 80, LinearRegression: 100, XGBoost: 45 }
  const [bestModel, setBestModel] = useState(null);
  // { name, rmse, r2, mae }

  // Latest prediction & explain state
  const [lastPrediction, setLastPrediction] = useState(null);
  // { predicted_price, model_used, confidence }

  return (
    <AppContext.Provider value={{
      dataset, setDataset,
      trainingStatus, setTrainingStatus,
      trainingProgress, setTrainingProgress,
      bestModel, setBestModel,
      lastPrediction, setLastPrediction,
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
