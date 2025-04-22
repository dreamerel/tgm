import React, { useState, useContext, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  
  const { login } = useContext(AuthContext);

  // Для инициализации Feather иконок после рендеринга
  useEffect(() => {
    if (window.feather) {
      window.feather.replace();
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    if (!username || !password) {
      setError('Пожалуйста, заполните все поля');
      setLoading(false);
      return;
    }
    
    try {
      await login(username, password);
    } catch (err) {
      console.error('Ошибка входа:', err);
      setError(err.response?.data?.error || 'Произошла ошибка при входе');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError('');
    setDemoLoading(true);
    
    try {
      await login('demo', 'demo123');
    } catch (err) {
      console.error('Ошибка входа в демо:', err);
      setError(err.response?.data?.error || 'Произошла ошибка при входе в демо-режим');
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">
            <i data-feather="message-circle"></i>
          </div>
          <h2>Telegram Manager</h2>
          <p>Войдите в свой аккаунт</p>
        </div>
        
        <div className="auth-body">
          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label htmlFor="username" className="form-label">Имя пользователя</label>
              <input 
                type="text" 
                className="form-control" 
                id="username" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Введите имя пользователя"
                required
                autoComplete="username"
              />
            </div>
            
            <div className="mb-3">
              <label htmlFor="password" className="form-label">Пароль</label>
              <input 
                type="password" 
                className="form-control" 
                id="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Введите пароль"
                required
                autoComplete="current-password"
              />
            </div>
            
            <button 
              type="submit" 
              className="btn btn-primary w-100 mb-3"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  Выполняется вход...
                </>
              ) : 'Войти'}
            </button>

            <button 
              type="button" 
              className="btn btn-outline-primary w-100"
              onClick={handleDemoLogin}
              disabled={demoLoading}
            >
              {demoLoading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  Подготовка демо-режима...
                </>
              ) : (
                <>
                  <i data-feather="play-circle" className="me-2"></i>
                  Демо-режим
                </>
              )}
            </button>
          </form>
        </div>
        
        <div className="auth-footer">
          <p>Еще нет аккаунта? <Link to="/register">Зарегистрироваться</Link></p>
        </div>
      </div>
    </div>
  );
}

export default Login;
