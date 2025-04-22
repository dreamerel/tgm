import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import TelegramVerification from './TelegramVerification';

function AccountManager({ accounts, onAddAccount }) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newAccount, setNewAccount] = useState({ 
    account_name: '', 
    phone: '',
    api_id: '',
    api_hash: ''
  });
  const [formError, setFormError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showVerification, setShowVerification] = useState(false);
  const [addedAccount, setAddedAccount] = useState(null);
  
  const navigate = useNavigate();
  
  // Эти обработчики определены ниже, удалим дублирование

  // Обработчик добавления нового аккаунта
  const handleAddAccount = async (e) => {
    e.preventDefault();
    setFormError('');
    setLoading(true);
    
    // Проверяем обязательные поля
    if (!newAccount.account_name || !newAccount.phone) {
      setFormError('Заполните все обязательные поля');
      setLoading(false);
      return;
    }
    
    // Проверяем формат телефона
    if (!newAccount.phone.startsWith('+') || newAccount.phone.length < 10) {
      setFormError('Номер телефона должен начинаться с + и содержать не менее 10 цифр');
      setLoading(false);
      return;
    }
    
    // Проверяем API ID и API Hash (теперь обязательные поля)
    // Если одно из полей заполнено, а другое нет
    if (!newAccount.api_id || !newAccount.api_hash) {
      setFormError('Необходимо указать оба параметра: API ID и API Hash');
      setLoading(false);
      return;
    }
    
    // Проверяем формат API ID
    if (isNaN(newAccount.api_id) || newAccount.api_id.length < 6) {
      setFormError('API ID должен быть числом не менее 6 знаков');
      setLoading(false);
      return;
    }
    
    // Проверяем формат API Hash
    if (newAccount.api_hash.length < 30) {
      setFormError('API Hash должен содержать не менее 30 символов');
      setLoading(false);
      return;
    }
    
    try {
      // Теперь всегда отправляем API ID и API Hash
      const accountData = newAccount;
      
      const response = await onAddAccount(accountData);
      
      if (response.account) {
        // Сохраняем добавленный аккаунт и показываем экран верификации
        if (response.account.status === 'pending') {
          // Начинаем процесс верификации
          setAddedAccount(response.account);
          setShowVerification(true);
          setShowAddForm(false);
        } else {
          // Аккаунт добавлен без необходимости верификации (маловероятно)
          setNewAccount({ account_name: '', phone: '', api_id: '', api_hash: '' });
          setShowAddForm(false);
          
          // Перенаправляем на страницу чатов
          navigate('/dashboard');
        }
      } else {
        setFormError(response.error || 'Не удалось добавить аккаунт');
      }
    } catch (err) {
      setFormError('Произошла ошибка при добавлении аккаунта');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  // Обработчик успешной верификации
  const handleVerificationSuccess = (data) => {
    console.log('Верификация успешна:', data);
    setShowVerification(false);
    setAddedAccount(null);
    // Перенаправляем на страницу чатов
    navigate('/dashboard');
  };
  
  // Обработчик отмены верификации
  const handleVerificationCancel = () => {
    setShowVerification(false);
    setAddedAccount(null);
  };

  // Рендер списка аккаунтов
  const renderAccountsList = () => {
    if (accounts.length === 0) {
      return (
        <div className="no-accounts">
          <p>У вас пока нет аккаунтов Telegram</p>
        </div>
      );
    }

    return (
      <div className="accounts-list">
        {accounts.map(account => (
          <div key={account.id} className="account-card">
            <div className="account-card-header">
              <div className="account-avatar">
                {account.account_name.charAt(0)}
              </div>
              <div className="account-info">
                <h5 className="account-name">{account.account_name}</h5>
                <p className="account-phone">{account.phone}</p>
              </div>
            </div>
            <div className="account-card-body">
              <div className="account-stats">
                <div className="stat">
                  <span className="stat-icon">
                    <i data-feather="message-square"></i>
                  </span>
                  <span className="stat-value">-</span>
                  <span className="stat-label">Чатов</span>
                </div>
                <div className="stat">
                  <span className="stat-icon">
                    <i data-feather="users"></i>
                  </span>
                  <span className="stat-value">-</span>
                  <span className="stat-label">Контактов</span>
                </div>
                <div className="stat">
                  <span className="stat-icon">
                    <i data-feather="send"></i>
                  </span>
                  <span className="stat-value">-</span>
                  <span className="stat-label">Отправлено</span>
                </div>
              </div>
            </div>
            <div className="account-card-footer">
              <button 
                className="btn btn-outline-primary btn-sm" 
                onClick={() => navigate('/dashboard')}
              >
                Открыть чаты
              </button>
              <button className="btn btn-outline-secondary btn-sm">
                Настройки
              </button>
            </div>
          </div>
        ))}
      </div>
    );
  };

  // Рендер формы добавления аккаунта
  const renderAddAccountForm = () => {
    return (
      <div className="card add-account-form">
        <div className="card-header">
          <h5>Добавить аккаунт Telegram</h5>
          <button 
            className="btn-close"
            onClick={() => setShowAddForm(false)}
          ></button>
        </div>
        <div className="card-body">
          {formError && (
            <div className="alert alert-danger" role="alert">
              {formError}
            </div>
          )}
          
          <form onSubmit={handleAddAccount}>
            <div className="mb-3">
              <label htmlFor="accountName" className="form-label">Название аккаунта</label>
              <input 
                type="text" 
                className="form-control" 
                id="accountName"
                value={newAccount.account_name}
                onChange={(e) => setNewAccount({ ...newAccount, account_name: e.target.value })}
                placeholder="Например: Личный, Рабочий и т.д."
                required
              />
            </div>
            
            <div className="mb-3">
              <label htmlFor="phoneNumber" className="form-label">Номер телефона</label>
              <input 
                type="text" 
                className="form-control" 
                id="phoneNumber"
                value={newAccount.phone}
                onChange={(e) => setNewAccount({ ...newAccount, phone: e.target.value })}
                placeholder="+79123456789"
                required
              />
              <div className="form-text">Укажите номер телефона, привязанный к аккаунту Telegram</div>
            </div>
            
            <div className="mb-3">
              <div className="form-text mb-2">
                Для работы с Telegram необходимо указать API ID и API Hash.
                <a href="https://my.telegram.org/apps" target="_blank" rel="noopener noreferrer" className="ms-1">
                  Получить их можно здесь
                </a>
              </div>
            
              <div className="mb-3">
                <label htmlFor="apiId" className="form-label">API ID</label>
                <input 
                  type="text" 
                  className="form-control" 
                  id="apiId"
                  value={newAccount.api_id}
                  onChange={(e) => setNewAccount({ ...newAccount, api_id: e.target.value })}
                  placeholder="12345678"
                  required
                />
              </div>
              
              <div className="mb-3">
                <label htmlFor="apiHash" className="form-label">API Hash</label>
                <input 
                  type="text" 
                  className="form-control" 
                  id="apiHash"
                  value={newAccount.api_hash}
                  onChange={(e) => setNewAccount({ ...newAccount, api_hash: e.target.value })}
                  placeholder="1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p"
                  required
                />
              </div>
            </div>
            
            <div className="text-end">
              <button 
                type="button" 
                className="btn btn-secondary me-2"
                onClick={() => setShowAddForm(false)}
              >
                Отмена
              </button>
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? 'Добавление...' : 'Добавить аккаунт'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="account-manager">
      <div className="account-manager-header">
        <h2>Управление аккаунтами Telegram</h2>
        <button 
          className="btn btn-primary"
          onClick={() => setShowAddForm(true)}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-plus">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg> Добавить аккаунт
        </button>
      </div>
      
      <div className="account-manager-description mb-3">
        <p>
          Добавьте один или несколько аккаунтов Telegram для управления сообщениями и рассылками.
          Вы можете добавить как личные, так и рабочие аккаунты.
        </p>
      </div>
      
      {renderAccountsList()}
      
      {showAddForm && renderAddAccountForm()}
      
      {showVerification && addedAccount && (
        <TelegramVerification 
          account={addedAccount} 
          onSuccess={handleVerificationSuccess}
          onCancel={handleVerificationCancel}
        />
      )}
    </div>
  );
}

export default AccountManager;
