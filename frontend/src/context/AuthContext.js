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
      const response = await api.post('/api/auth/login', { username, password });
      
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
  
  // Функция для добавления аккаунта Telegram
  const addTelegramAccount = async (accountData) => {
    try {
      console.log('Отправка запроса на добавление аккаунта:', accountData);
      // Проверяем наличие всех необходимых данных
      if (!accountData.phone || !accountData.account_name || !accountData.api_id || !accountData.api_hash) {
        console.error('Отсутствуют необходимые данные для добавления аккаунта');
        return {
          success: false,
          error: 'Необходимо заполнить все поля (имя аккаунта, телефон, API ID, API Hash)'
        };
      }
      
      // Форматируем данные API ID как строку для отправки на сервер
      const formattedData = {
        ...accountData,
        api_id: String(accountData.api_id)
      };
      
      console.log('Отправка форматированных данных:', formattedData);
      const response = await api.post('/api/telegram/accounts', formattedData);
      console.log('Получен ответ от сервера:', response.data);
      
      // Обновляем информацию о пользователе, чтобы отразить новый аккаунт
      await checkAuth();
      
      return {
        success: true,
        account: response.data.account,
        message: response.data.message
      };
    } catch (error) {
      console.error('Ошибка добавления аккаунта Telegram:', error);
      let errorMessage = 'Не удалось добавить аккаунт Telegram';
      
      if (error.response) {
        console.error('Детали ошибки:', error.response.data);
        errorMessage = error.response.data.error || errorMessage;
      } else if (error.request) {
        console.error('Нет ответа от сервера:', error.request);
        errorMessage = 'Нет ответа от сервера API';
      } else {
        console.error('Ошибка запроса:', error.message);
        errorMessage = error.message || errorMessage;
      }
      
      return {
        success: false,
        error: errorMessage
      };
    }
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
        checkAuth,
        addTelegramAccount
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
