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
  const [showApiFields, setShowApiFields] = useState(false);
  const [formError, setFormError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();

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
    
    // Проверяем API ID и API Hash, если они заполнены
    if (showApiFields) {
      // Если одно из полей заполнено, а другое нет
      if ((newAccount.api_id && !newAccount.api_hash) || (!newAccount.api_id && newAccount.api_hash)) {
        setFormError('Необходимо указать оба параметра: API ID и API Hash');
        setLoading(false);
        return;
      }
      
      // Если API ID заполнен, проверяем его формат
      if (newAccount.api_id) {
        if (isNaN(newAccount.api_id) || newAccount.api_id.length < 6) {
          setFormError('API ID должен быть числом не менее 6 знаков');
          setLoading(false);
          return;
        }
      }
      
      // Если API Hash заполнен, проверяем его формат
      if (newAccount.api_hash && newAccount.api_hash.length < 30) {
        setFormError('API Hash должен содержать не менее 30 символов');
        setLoading(false);
        return;
      }
    }
    
    try {
      // Если API поля не отображаются, удаляем их из запроса
      const accountData = showApiFields 
        ? newAccount 
        : { account_name: newAccount.account_name, phone: newAccount.phone };
      
      const result = await onAddAccount(accountData);
      
      if (result.success) {
        // Сбрасываем форму и скрываем её
        setNewAccount({ account_name: '', phone: '', api_id: '', api_hash: '' });
        setShowApiFields(false);
        setShowAddForm(false);
        
        // Перенаправляем на страницу чатов
        navigate('/dashboard');
      } else {
        setFormError(result.error || 'Не удалось добавить аккаунт');
      }
    } catch (err) {
      setFormError('Произошла ошибка при добавлении аккаунта');
      console.error(err);
    } finally {
      setLoading(false);
    }
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
              <div className="form-check form-switch">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="showApiFieldsSwitch"
                  checked={showApiFields}
                  onChange={() => setShowApiFields(!showApiFields)}
                />
                <label className="form-check-label" htmlFor="showApiFieldsSwitch">
                  Добавить API ID и API Hash
                </label>
              </div>
              <div className="form-text">
                Для полной функциональности нужны API ID и API Hash от Telegram.
                <a href="https://my.telegram.org/apps" target="_blank" rel="noopener noreferrer" className="ms-1">
                  Получить их можно здесь
                </a>
              </div>
            </div>
            
            {showApiFields && (
              <>
                <div className="mb-3">
                  <label htmlFor="apiId" className="form-label">API ID</label>
                  <input 
                    type="text" 
                    className="form-control" 
                    id="apiId"
                    value={newAccount.api_id}
                    onChange={(e) => setNewAccount({ ...newAccount, api_id: e.target.value })}
                    placeholder="12345678"
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
                  />
                </div>
              </>
            )}
            
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
          <i data-feather="plus"></i> Добавить аккаунт
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
    </div>
  );
}

export default AccountManager;
