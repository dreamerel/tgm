import React, { useState, useEffect } from 'react';
import api from '../api';

function MassSending({ account }) {
  const [massSendings, setMassSendings] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [showAddForm, setShowAddForm] = useState(false);
  const [newMassSending, setNewMassSending] = useState({
    message: '',
    contacts: [],
    delay: 60,
    frequency: 5
  });
  const [formError, setFormError] = useState('');

  // Загрузка массовых рассылок и контактов при изменении аккаунта
  useEffect(() => {
    const fetchData = async () => {
      if (!account) return;
      
      try {
        setLoading(true);
        
        // Запрашиваем список рассылок
        const sendings = await api.get(`/api/telegram/mass-sendings?account_id=${account.id}`);
        setMassSendings(sendings.data.mass_sendings);
        
        // Запрашиваем список контактов
        const contactsResponse = await api.get(`/api/telegram/contacts?account_id=${account.id}`);
        setContacts(contactsResponse.data.contacts);
      } catch (err) {
        setError('Не удалось загрузить данные');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [account]);

  // Обработчик добавления новой массовой рассылки
  const handleAddMassSending = async (e) => {
    e.preventDefault();
    setFormError('');
    
    if (!newMassSending.message || newMassSending.contacts.length === 0) {
      setFormError('Заполните все обязательные поля и выберите хотя бы один контакт');
      return;
    }
    
    try {
      const response = await api.post('/api/telegram/mass-sendings', {
        account_id: account.id,
        message: newMassSending.message,
        contacts: newMassSending.contacts,
        delay: newMassSending.delay,
        frequency: newMassSending.frequency
      });
      
      // Добавляем новую рассылку в список
      setMassSendings([...massSendings, response.data.mass_sending]);
      
      // Сбрасываем форму
      setNewMassSending({
        message: '',
        contacts: [],
        delay: 60,
        frequency: 5
      });
      setShowAddForm(false);
    } catch (err) {
      setFormError(err.response?.data?.error || 'Не удалось создать массовую рассылку');
    }
  };

  // Обработчик выбора/отмены выбора контакта
  const handleToggleContact = (contactId) => {
    if (newMassSending.contacts.includes(contactId)) {
      // Удаляем контакт из списка
      setNewMassSending({
        ...newMassSending,
        contacts: newMassSending.contacts.filter(id => id !== contactId)
      });
    } else {
      // Добавляем контакт в список
      setNewMassSending({
        ...newMassSending,
        contacts: [...newMassSending.contacts, contactId]
      });
    }
  };

  // Обработчик выбора всех контактов
  const handleSelectAllContacts = () => {
    if (newMassSending.contacts.length === contacts.length) {
      // Если все выбраны, снимаем выбор
      setNewMassSending({
        ...newMassSending,
        contacts: []
      });
    } else {
      // Иначе выбираем все
      setNewMassSending({
        ...newMassSending,
        contacts: contacts.map(contact => contact.id)
      });
    }
  };

  // Рендер списка массовых рассылок
  const renderMassSendingsList = () => {
    if (loading && massSendings.length === 0) {
      return (
        <div className="mass-sendings-loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Загрузка...</span>
          </div>
          <p>Загрузка рассылок...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="mass-sendings-error">
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        </div>
      );
    }

    if (massSendings.length === 0) {
      return (
        <div className="no-mass-sendings">
          <p>У вас пока нет массовых рассылок</p>
        </div>
      );
    }

    return (
      <div className="mass-sendings-table-wrapper">
        <table className="table table-hover">
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Сообщение</th>
              <th scope="col">Контакты</th>
              <th scope="col">Частота</th>
              <th scope="col">Задержка</th>
              <th scope="col">Статус</th>
              <th scope="col">Отправлено</th>
            </tr>
          </thead>
          <tbody>
            {massSendings.map((massSending, index) => (
              <tr key={massSending.id}>
                <td>{index + 1}</td>
                <td>
                  {massSending.message.length > 50 
                    ? `${massSending.message.substring(0, 50)}...` 
                    : massSending.message}
                </td>
                <td>{Array.isArray(massSending.contacts) ? massSending.contacts.length : 0}</td>
                <td>{massSending.frequency} сообщ/мин</td>
                <td>{massSending.delay} сек</td>
                <td>
                  <span className={`badge ${massSending.status === 'completed' ? 'bg-success' : massSending.status === 'pending' ? 'bg-warning' : 'bg-primary'}`}>
                    {massSending.status === 'pending' ? 'В ожидании' : 
                     massSending.status === 'in_progress' ? 'Выполняется' : 
                     massSending.status === 'completed' ? 'Завершено' : 
                     massSending.status}
                  </span>
                </td>
                <td>{massSending.sent_count || 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Рендер формы создания массовой рассылки
  const renderAddMassSendingForm = () => {
    return (
      <div className="card add-mass-sending-form">
        <div className="card-header">
          <h5>Создать массовую рассылку</h5>
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
          
          <form onSubmit={handleAddMassSending}>
            <div className="mb-3">
              <label htmlFor="message" className="form-label">Текст сообщения</label>
              <textarea 
                className="form-control" 
                id="message"
                rows="4"
                value={newMassSending.message}
                onChange={(e) => setNewMassSending({ ...newMassSending, message: e.target.value })}
                placeholder="Введите текст сообщения для рассылки"
                required
              ></textarea>
            </div>
            
            <div className="mb-3">
              <label className="form-label">Выберите контакты</label>
              <div className="contact-select-header">
                <div className="form-check">
                  <input 
                    type="checkbox" 
                    className="form-check-input" 
                    id="selectAll"
                    checked={newMassSending.contacts.length === contacts.length && contacts.length > 0}
                    onChange={handleSelectAllContacts}
                  />
                  <label className="form-check-label" htmlFor="selectAll">
                    Выбрать все
                  </label>
                </div>
                <span className="selected-count">
                  Выбрано: {newMassSending.contacts.length} из {contacts.length}
                </span>
              </div>
              
              <div className="contact-select-list">
                {contacts.length === 0 ? (
                  <p>Нет доступных контактов</p>
                ) : (
                  contacts.map(contact => (
                    <div className="form-check" key={contact.id}>
                      <input 
                        type="checkbox" 
                        className="form-check-input" 
                        id={`contact-${contact.id}`}
                        checked={newMassSending.contacts.includes(contact.id)}
                        onChange={() => handleToggleContact(contact.id)}
                      />
                      <label className="form-check-label" htmlFor={`contact-${contact.id}`}>
                        {contact.name} ({contact.phone})
                      </label>
                    </div>
                  ))
                )}
              </div>
            </div>
            
            <div className="row mb-3">
              <div className="col-md-6">
                <label htmlFor="delay" className="form-label">Задержка между сообщениями (сек)</label>
                <input 
                  type="number" 
                  className="form-control" 
                  id="delay"
                  min="30"
                  max="600"
                  value={newMassSending.delay}
                  onChange={(e) => setNewMassSending({ ...newMassSending, delay: parseInt(e.target.value) })}
                />
              </div>
              
              <div className="col-md-6">
                <label htmlFor="frequency" className="form-label">Частота отправки (сообщ/мин)</label>
                <input 
                  type="number" 
                  className="form-control" 
                  id="frequency"
                  min="1"
                  max="20"
                  value={newMassSending.frequency}
                  onChange={(e) => setNewMassSending({ ...newMassSending, frequency: parseInt(e.target.value) })}
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
                disabled={newMassSending.contacts.length === 0}
              >
                Создать рассылку
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="mass-sending">
      <div className="mass-sending-header">
        <h2>Массовая рассылка</h2>
        <button 
          className="btn btn-primary"
          onClick={() => setShowAddForm(true)}
          disabled={contacts.length === 0}
        >
          <i data-feather="plus"></i> Создать рассылку
        </button>
      </div>
      
      <div className="mass-sending-description mb-3">
        <p>
          Создавайте массовые рассылки для отправки сообщений группе контактов. 
          Настройте частоту и задержку отправки, чтобы избежать блокировок.
        </p>
      </div>
      
      {renderMassSendingsList()}
      
      {showAddForm && renderAddMassSendingForm()}
    </div>
  );
}

export default MassSending;
