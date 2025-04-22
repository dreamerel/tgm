import React, { useContext, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import { AuthContext } from './context/AuthContext';

function App() {
  const { isAuthenticated, checkAuth } = useContext(AuthContext);
  const navigate = useNavigate();

  // При запуске приложения проверяем наличие токена
  useEffect(() => {
    const initApp = async () => {
      await checkAuth();
    };
    initApp();
  }, [checkAuth]);

  return (
    <div className="app">
      <Routes>
        <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Login />} />
        <Route path="/register" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Register />} />
        <Route path="/dashboard/*" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} />
        <Route path="/" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} />
      </Routes>
    </div>
  );
}

export default App;
