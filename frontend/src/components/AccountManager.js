import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function AccountManager({ accounts, onAddAccount }) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newAccount, setNewAccount] = useState({ account_name: '', phone: '' });
  const [formError, setFormError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();

  // Обработчик добавления нового аккаунта
  const handleAddAccount = async (e) => {
    e.preventDefault();
    setFormError('');
    setLoading(true);
    
    if (!newAccount.account_name || !newAccount.phone) {
      setFormError('Заполните все обязательные поля');
      setLoading(false);
      return;
    }
    
    if (!newAccount.phone.startsWith('+') || newAccount.phone.length < 10) {
      setFormError('Номер телефона должен начинаться с + и содержать не менее 10 цифр');
      setLoading(false);
      return;
    }
    
    try {
      const result = await onAddAccount(newAccount);
      
      if (result.success) {
        // Сбрасываем форму и скрываем её
        setNewAccount({ account_name: '', phone: '' });
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
