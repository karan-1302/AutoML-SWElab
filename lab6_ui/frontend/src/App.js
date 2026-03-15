// src/App.js
// Root component: sets up providers, routing, and protected routes.

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppProvider } from './context/AppContext';

import Sidebar    from './components/Sidebar';
import LoginPage  from './pages/LoginPage';
import UploadPage from './pages/UploadPage';
import TrainPage  from './pages/TrainPage';
import PredictPage from './pages/PredictPage';
import ExplainPage from './pages/ExplainPage';

// ── Protected Route wrapper ───────────────────────────────────
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

// ── Authenticated shell (sidebar + content) ───────────────────
function AppShell({ children }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">{children}</main>
    </div>
  );
}

// ── Root ──────────────────────────────────────────────────────
export default function App() {
  return (
    <AuthProvider>
      <AppProvider>
        <BrowserRouter>
          <Routes>
            {/* Public */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected */}
            <Route path="/upload" element={
              <ProtectedRoute>
                <AppShell><UploadPage /></AppShell>
              </ProtectedRoute>
            }/>
            <Route path="/train" element={
              <ProtectedRoute>
                <AppShell><TrainPage /></AppShell>
              </ProtectedRoute>
            }/>
            <Route path="/predict" element={
              <ProtectedRoute>
                <AppShell><PredictPage /></AppShell>
              </ProtectedRoute>
            }/>
            <Route path="/explain" element={
              <ProtectedRoute>
                <AppShell><ExplainPage /></AppShell>
              </ProtectedRoute>
            }/>

            {/* Default redirect */}
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </BrowserRouter>
      </AppProvider>
    </AuthProvider>
  );
}
