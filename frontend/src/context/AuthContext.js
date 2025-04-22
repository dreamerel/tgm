import React, { createContext, useState, useCallback, useEffect } from 'react';
import api from '../api';

// Создаём контекст для хранения данных авторизации
export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Проверка авторизации при загрузке приложения
  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      setIsAuthenticated(false);
      setUser(null);
      setLoading(false);
      return false;
    }
    
    try {
      const response = await api.get('/api/user');
      setUser(response.data.user);
      setIsAuthenticated(true);
      setLoading(false);
      return true;
    } catch (error) {
      console.error('Ошибка проверки авторизации:', error);
      setIsAuthenticated(false);
      setUser(null);
      setLoading(false);
      return false;
    }
  }, []);

  // Вызываем проверку авторизации при загрузке приложения
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Функция для входа пользователя
  const login = async (username, password) => {
    try {
      const response = await api.post('/api/login', { username, password });
      
      // Сохраняем токены в localStorage
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      
      // Обновляем состояние
      setUser(response.data.user);
      setIsAuthenticated(true);
      
      return response.data;
    } catch (error) {
      console.error('Ошибка входа:', error);
      throw error;
    }
  };

  // Функция для регистрации пользователя
  const register = async (username, password, email = null) => {
    try {
      const response = await api.post('/api/register', { 
        username, 
        password,
        email
      });
      
      // Сохраняем токены в localStorage
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      
      // Обновляем состояние
      setUser(response.data.user);
      setIsAuthenticated(true);
      
      return response.data;
    } catch (error) {
      console.error('Ошибка регистрации:', error);
      throw error;
    }
  };

  // Функция для выхода пользователя
  const logout = () => {
    // Удаляем токены из localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // Обновляем состояние
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        user,
        loading,
        login,
        register,
        logout,
        checkAuth
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
