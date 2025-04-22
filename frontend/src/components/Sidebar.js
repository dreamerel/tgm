import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

function Sidebar({ user, accounts, selectedAccount, onAccountChange, onLogout, activePath }) {
  const [isAccountDropdownOpen, setIsAccountDropdownOpen] = useState(false);
  const navigate = useNavigate();

  // Проверка активного пути для стилизации ссылок
  const isActive = (path) => {
    return activePath === `/dashboard${path}` ? 'active' : '';
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="logo">
          <i data-feather="message-circle"></i>
          <h1>Telegram Manager</h1>
        </div>
      </div>
      
      {accounts.length > 0 && (
        <div className="account-selector">
          <div 
            className="selected-account"
            onClick={() => setIsAccountDropdownOpen(!isAccountDropdownOpen)}
          >
            <div className="account-icon">
              {selectedAccount?.account_name?.charAt(0) || 'T'}
            </div>
            <div className="account-info">
              <div className="account-name">{selectedAccount?.account_name || 'Выберите аккаунт'}</div>
              <div className="account-phone">{selectedAccount?.phone || ''}</div>
            </div>
            <i data-feather="chevron-down"></i>
          </div>
          
          {isAccountDropdownOpen && (
            <div className="account-dropdown">
              {accounts.map(account => (
                <div 
                  key={account.id} 
                  className={`account-item ${selectedAccount?.id === account.id ? 'active' : ''}`}
                  onClick={() => {
                    onAccountChange(account);
                    setIsAccountDropdownOpen(false);
                  }}
                >
                  <div className="account-icon">
                    {account.account_name.charAt(0)}
                  </div>
                  <div className="account-info">
                    <div className="account-name">{account.account_name}</div>
                    <div className="account-phone">{account.phone}</div>
                  </div>
                </div>
              ))}
              
              <div 
                className="add-account-btn"
                onClick={() => {
                  navigate('/dashboard/accounts');
                  setIsAccountDropdownOpen(false);
                }}
              >
                <i data-feather="plus"></i>
                <span>Добавить аккаунт</span>
              </div>
            </div>
          )}
        </div>
      )}
      
      <nav className="sidebar-nav">
        <ul>
          <li className={isActive('')}>
            <Link to="/dashboard">
              <i data-feather="message-square"></i>
              <span>Чаты</span>
            </Link>
          </li>
          <li className={isActive('/contacts')}>
            <Link to="/dashboard/contacts">
              <i data-feather="users"></i>
              <span>Контакты</span>
            </Link>
          </li>
          <li className={isActive('/auto-replies')}>
            <Link to="/dashboard/auto-replies">
              <i data-feather="repeat"></i>
              <span>Авто-ответы</span>
            </Link>
          </li>
          <li className={isActive('/mass-sending')}>
            <Link to="/dashboard/mass-sending">
              <i data-feather="send"></i>
              <span>Массовая рассылка</span>
            </Link>
          </li>
          <li className={isActive('/statistics')}>
            <Link to="/dashboard/statistics">
              <i data-feather="bar-chart-2"></i>
              <span>Статистика</span>
            </Link>
          </li>
          <li className={isActive('/accounts')}>
            <Link to="/dashboard/accounts">
              <i data-feather="smartphone"></i>
              <span>Управление аккаунтами</span>
            </Link>
          </li>
          <li className={isActive('/api-tester')}>
            <Link to="/dashboard/api-tester">
              <i data-feather="code"></i>
              <span>API Тестер</span>
            </Link>
          </li>
        </ul>
      </nav>
      
      <div className="sidebar-footer">
        <div className="user-info">
          <div className="user-avatar">
            {user?.username?.charAt(0) || 'U'}
          </div>
          <div className="user-name">{user?.username || 'Пользователь'}</div>
        </div>
        
        <button className="logout-btn" onClick={onLogout}>
          <i data-feather="log-out"></i>
          <span>Выход</span>
        </button>
      </div>
    </div>
  );
}

export default Sidebar;
