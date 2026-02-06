// src/context/AuthContext.js
// Provides JWT auth state and helpers to the entire app.
// Uses axios interceptors to automatically attach Bearer token to all requests.

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

// Create axios instance with base URL
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
});

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('jwt') || null);
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('user')) || null; }
    catch { return null; }
  });

  // Set up axios interceptor to attach token to all requests
  useEffect(() => {
    // Request interceptor: add Authorization header
    const requestInterceptor = apiClient.interceptors.request.use(
      (config) => {
        const storedToken = localStorage.getItem('jwt');
        if (storedToken) {
          config.headers.Authorization = `Bearer ${storedToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor: handle 401 errors
    const responseInterceptor = apiClient.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid - clear auth and redirect to login
          localStorage.removeItem('jwt');
          localStorage.removeItem('user');
          setToken(null);
          setUser(null);
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );

    return () => {
      apiClient.interceptors.request.eject(requestInterceptor);
      apiClient.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  const login = useCallback(async (email, password) => {
    console.log('🔑 AuthContext.login called');
    console.log('   Email:', email);
    console.log('   API Base URL:', apiClient.defaults.baseURL);

    try {
      console.log('   Making POST request to /api/auth/login...');
      const res = await apiClient.post('/api/auth/login', { email, password });
      console.log('   Response received:', res.status, res.data);

      const { access_token, user: userData } = res.data;
      localStorage.setItem('jwt', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      setToken(access_token);
      setUser(userData);
      console.log('   Login successful, user data saved');
      return userData;
    } catch (error) {
      console.error('   Login failed in AuthContext:', error);
      throw error;
    }
  }, []);

  const register = useCallback(async (email, password, fullName) => {
    const res = await apiClient.post('/api/auth/register', { email, password, full_name: fullName });
    const { access_token, user: userData } = res.data;
    localStorage.setItem('jwt', access_token);
    localStorage.setItem('user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('jwt');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, user, login, register, logout, isAuthenticated: !!token, apiClient }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
