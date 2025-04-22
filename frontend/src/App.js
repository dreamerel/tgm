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
    // Загружаем скрипт Feather Icons, если он еще не загружен
    if (!document.getElementById('feather-icons-script')) {
      const featherScript = document.createElement('script');
      featherScript.id = 'feather-icons-script';
      featherScript.src = 'https://cdn.jsdelivr.net/npm/feather-icons/dist/feather.min.js';
      featherScript.async = true;
      
      // Когда скрипт загрузится, вызываем replace() и устанавливаем наблюдателя мутаций
      featherScript.onload = () => {
        if (window.feather) {
          console.log('Feather Icons loaded, initializing icons');
          window.feather.replace();
          
          // Используем MutationObserver для отслеживания изменений в DOM
          const observer = new MutationObserver((mutations) => {
            if (window.feather) {
              console.log('DOM changed, replacing icons');
              window.feather.replace();
            }
          });
          
          // Начинаем наблюдение за всем документом
          observer.observe(document.body, {
            childList: true,
            subtree: true
          });
          
          // Также периодически обновляем иконки для подстраховки
          const intervalId = setInterval(() => {
            if (window.feather) {
              window.feather.replace();
            }
          }, 2000);
          
          // Сохраняем observer и intervalId для очистки при размонтировании
          return () => {
            observer.disconnect();
            clearInterval(intervalId);
          };
        }
      };
      
      document.head.appendChild(featherScript);
    } else if (window.feather) {
      // Если скрипт уже загружен, просто вызываем replace()
      console.log('Feather script already loaded, replacing icons');
      window.feather.replace();
    }
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
