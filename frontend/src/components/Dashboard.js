import React, { useState, useEffect, useContext } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import ChatWindow from './ChatWindow';
import ContactList from './ContactList';
import AutoReplies from './AutoReplies';
import MassSending from './MassSending';
import Statistics from './Statistics';
import AccountManager from './AccountManager';

import { AuthContext } from '../context/AuthContext';
import api from '../api';

function Dashboard() {
  const { user, logout, addTelegramAccount } = useContext(AuthContext);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const navigate = useNavigate();
  const location = useLocation();

  // Загрузка аккаунтов пользователя при монтировании
  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        setLoading(true);
        const response = await api.get('/api/telegram/accounts');
        setAccounts(response.data.accounts);
        
        // Если есть аккаунты, выбираем первый по умолчанию
        if (response.data.accounts.length > 0) {
          setSelectedAccount(response.data.accounts[0]);
        }
      } catch (err) {
        setError('Не удалось загрузить аккаунты Telegram');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAccounts();
  }, []);

  // Обработчик смены выбранного аккаунта
  const handleAccountChange = (account) => {
    setSelectedAccount(account);
  };

  // Обработчик добавления нового аккаунта
  const handleAddAccount = async (accountData) => {
    try {
      console.log('Отправка данных аккаунта:', accountData);
      // Используем функцию из контекста авторизации
      const result = await addTelegramAccount(accountData);
      console.log('Результат добавления аккаунта:', result);
      
      if (result.success) {
        console.log('Успешно добавлен аккаунт:', result.account);
        // Обновляем список аккаунтов, если аккаунт добавлен успешно
        if (result.account && result.account.id) {
          setAccounts(prevAccounts => [...prevAccounts, result.account]);
          
          // Выбираем новый аккаунт
          setSelectedAccount(result.account);
        }
        
        return { 
          success: true, 
          account: result.account 
        };
      } else {
        console.error('Ошибка при добавлении аккаунта:', result.error);
        return { 
          success: false, 
          error: result.error || 'Неизвестная ошибка при добавлении аккаунта'
        };
      }
    } catch (err) {
      console.error('Исключение при добавлении аккаунта:', err);
      return { 
        success: false, 
        error: err.message || 'Ошибка при добавлении аккаунта' 
      };
    }
  };

  // Обработчик выхода из аккаунта
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Рендер содержимого страницы в зависимости от наличия аккаунтов
  const renderContent = () => {
    if (loading) {
      return (
        <div className="dashboard-loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Загрузка...</span>
          </div>
          <p>Загрузка данных...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="dashboard-error">
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
          <button className="btn btn-primary" onClick={() => window.location.reload()}>
            Повторить
          </button>
        </div>
      );
    }

    if (accounts.length === 0) {
      return (
        <div className="dashboard-no-accounts">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title">Добро пожаловать в Telegram Manager!</h5>
              <p className="card-text">У вас еще нет добавленных аккаунтов Telegram. Добавьте аккаунт, чтобы начать работу.</p>
              <button 
                className="btn btn-primary"
                onClick={() => navigate('/dashboard/accounts')}
              >
                Добавить аккаунт Telegram
              </button>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="dashboard-content">
        <Routes>
          <Route path="/" element={<ChatWindow account={selectedAccount} />} />
          <Route path="/contacts" element={<ContactList account={selectedAccount} />} />
          <Route path="/auto-replies" element={<AutoReplies account={selectedAccount} />} />
          <Route path="/mass-sending" element={<MassSending account={selectedAccount} />} />
          <Route path="/statistics" element={<Statistics account={selectedAccount} />} />
          <Route path="/accounts" element={<AccountManager accounts={accounts} onAddAccount={handleAddAccount} />} />

        </Routes>
      </div>
    );
  };

  return (
    <div className="dashboard">
      <Sidebar 
        user={user}
        accounts={accounts}
        selectedAccount={selectedAccount}
        onAccountChange={handleAccountChange}
        onLogout={handleLogout}
        activePath={location.pathname}
      />
      {renderContent()}
    </div>
  );
}

export default Dashboard;
