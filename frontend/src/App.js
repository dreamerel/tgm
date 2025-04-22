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

  // Инициализация Feather иконок
  useEffect(() => {
    // Подгружаем иконки Feather если доступны
    if (window.feather) {
      window.feather.replace();
    } else {
      // Если feather еще не загружен, ждем загрузки
      const featherScript = document.createElement('script');
      featherScript.src = 'https://cdn.jsdelivr.net/npm/feather-icons/dist/feather.min.js';
      featherScript.onload = () => window.feather.replace();
      document.head.appendChild(featherScript);
    }

    // Функция для периодического вызова feather.replace()
    const replaceIcons = () => {
      if (window.feather) {
        window.feather.replace();
      }
    };

    // Вызываем replaceIcons каждые 2 секунды, чтобы подхватить новые иконки
    const intervalId = setInterval(replaceIcons, 2000);

    // Очистка при размонтировании
    return () => {
      clearInterval(intervalId);
    };
  }, []);

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
