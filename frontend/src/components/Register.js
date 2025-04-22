import React, { useState, useContext, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { register } = useContext(AuthContext);

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
    
    if (!username || !password || !confirmPassword) {
      setError('Пожалуйста, заполните все обязательные поля');
      setLoading(false);
      return;
    }
    
    if (password !== confirmPassword) {
      setError('Пароли не совпадают');
      setLoading(false);
      return;
    }
    
    try {
      await register(username, password, email);
    } catch (err) {
      console.error('Ошибка регистрации:', err);
      setError(err.response?.data?.error || 'Произошла ошибка при регистрации');
    } finally {
      setLoading(false);
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
          <p>Создайте новый аккаунт</p>
        </div>
        
        <div className="auth-body">
          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label htmlFor="username" className="form-label">Имя пользователя*</label>
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
              <div className="form-text">Минимум 3 символа, только латинские буквы и цифры</div>
            </div>
            
            <div className="mb-3">
              <label htmlFor="email" className="form-label">Email (опционально)</label>
              <input 
                type="email" 
                className="form-control" 
                id="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Введите email"
                autoComplete="email"
              />
              <div className="form-text">Для восстановления пароля и уведомлений</div>
            </div>
            
            <div className="mb-3">
              <label htmlFor="password" className="form-label">Пароль*</label>
              <input 
                type="password" 
                className="form-control" 
                id="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Введите пароль"
                required
                autoComplete="new-password"
              />
              <div className="form-text">Минимум 6 символов, используйте буквы и цифры</div>
            </div>
            
            <div className="mb-3">
              <label htmlFor="confirmPassword" className="form-label">Подтвердите пароль*</label>
              <input 
                type="password" 
                className="form-control" 
                id="confirmPassword" 
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Подтвердите пароль"
                required
                autoComplete="new-password"
              />
            </div>
            
            <button 
              type="submit" 
              className="btn btn-primary w-100"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  Регистрация...
                </>
              ) : (
                <>
                  <i data-feather="user-plus" className="me-2"></i>
                  Зарегистрироваться
                </>
              )}
            </button>
          </form>
        </div>
        
        <div className="auth-footer">
          <p>Уже есть аккаунт? <Link to="/login">Войти</Link></p>
        </div>
      </div>
    </div>
  );
}

export default Register;
