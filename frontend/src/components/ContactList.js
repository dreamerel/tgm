import React, { useState, useEffect } from 'react';
import api from '../api';

function ContactList({ account }) {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [newContact, setNewContact] = useState({ name: '', phone: '' });
  const [showAddForm, setShowAddForm] = useState(false);
  const [formError, setFormError] = useState('');
  
  const [showImportForm, setShowImportForm] = useState(false);
  const [importText, setImportText] = useState('');
  const [importError, setImportError] = useState('');

  // Загрузка контактов при изменении аккаунта
  useEffect(() => {
    const fetchContacts = async () => {
      if (!account) return;
      
      try {
        setLoading(true);
        const response = await api.get(`/api/telegram/contacts?account_id=${account.id}`);
        setContacts(response.data.contacts);
      } catch (err) {
        setError('Не удалось загрузить контакты');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchContacts();
  }, [account]);

  // Обработчик добавления нового контакта
  const handleAddContact = async (e) => {
    e.preventDefault();
    setFormError('');
    
    if (!newContact.name || !newContact.phone) {
      setFormError('Заполните все поля');
      return;
    }
    
    try {
      const response = await api.post('/api/telegram/contacts', {
        account_id: account.id,
        name: newContact.name,
        phone: newContact.phone
      });
      
      // Добавляем новый контакт в список
      setContacts([...contacts, response.data.contact]);
      
      // Сбрасываем форму
      setNewContact({ name: '', phone: '' });
      setShowAddForm(false);
    } catch (err) {
      setFormError(err.response?.data?.error || 'Не удалось добавить контакт');
    }
  };

  // Обработчик импорта контактов
  const handleImportContacts = async (e) => {
    e.preventDefault();
    setImportError('');
    
    if (!importText.trim()) {
      setImportError('Введите данные для импорта');
      return;
    }
    
    // Разбор введенных данных (формат: Имя, +79123456789)
    const lines = importText.split('\n');
    const contactsToImport = [];
    
    for (const line of lines) {
      if (!line.trim()) continue;
      
      const parts = line.split(',');
      if (parts.length < 2) {
        setImportError('Неверный формат данных. Используйте: Имя, +79123456789');
        return;
      }
      
      const name = parts[0].trim();
      const phone = parts[1].trim();
      
      if (!name || !phone || !phone.startsWith('+')) {
        setImportError('Неверный формат номера телефона. Используйте формат: +79123456789');
        return;
      }
      
      contactsToImport.push({ name, phone });
    }
    
    if (contactsToImport.length === 0) {
      setImportError('Не найдено контактов для импорта');
      return;
    }
    
    try {
      const response = await api.post('/api/telegram/contacts/import', {
        account_id: account.id,
        contacts: contactsToImport
      });
      
      // Обновляем список контактов
      setContacts([...contacts, ...response.data.contacts]);
      
      // Сбрасываем форму
      setImportText('');
      setShowImportForm(false);
      
      alert(`Успешно импортировано ${response.data.contacts.length} контактов`);
    } catch (err) {
      setImportError(err.response?.data?.error || 'Не удалось импортировать контакты');
    }
  };

  // Рендер списка контактов
  const renderContactsList = () => {
    if (loading && contacts.length === 0) {
      return (
        <div className="contacts-loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Загрузка...</span>
          </div>
          <p>Загрузка контактов...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="contacts-error">
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        </div>
      );
    }

    if (contacts.length === 0) {
      return (
        <div className="no-contacts">
          <p>У вас пока нет контактов</p>
        </div>
      );
    }

    return (
      <div className="contacts-table-wrapper">
        <table className="table table-hover">
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Имя</th>
              <th scope="col">Телефон</th>
              <th scope="col">Действия</th>
            </tr>
          </thead>
          <tbody>
            {contacts.map((contact, index) => (
              <tr key={contact.id}>
                <td>{index + 1}</td>
                <td>{contact.name}</td>
                <td>{contact.phone}</td>
                <td>
                  <button className="btn btn-sm btn-outline-primary">
                    <i data-feather="message-square"></i> Чат
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Рендер формы добавления контакта
  const renderAddContactForm = () => {
    return (
      <div className="card add-contact-form">
        <div className="card-header">
          <h5>Добавить контакт</h5>
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
          
          <form onSubmit={handleAddContact}>
            <div className="mb-3">
              <label htmlFor="contactName" className="form-label">Имя контакта</label>
              <input 
                type="text" 
                className="form-control" 
                id="contactName"
                value={newContact.name}
                onChange={(e) => setNewContact({ ...newContact, name: e.target.value })}
                placeholder="Введите имя контакта"
                required
              />
            </div>
            
            <div className="mb-3">
              <label htmlFor="contactPhone" className="form-label">Номер телефона</label>
              <input 
                type="text" 
                className="form-control" 
                id="contactPhone"
                value={newContact.phone}
                onChange={(e) => setNewContact({ ...newContact, phone: e.target.value })}
                placeholder="+79123456789"
                required
              />
              <div className="form-text">Формат: +79123456789</div>
            </div>
            
            <div className="text-end">
              <button 
                type="button" 
                className="btn btn-secondary me-2"
                onClick={() => setShowAddForm(false)}
              >
                Отмена
              </button>
              <button type="submit" className="btn btn-primary">Добавить</button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // Рендер формы импорта контактов
  const renderImportContactsForm = () => {
    return (
      <div className="card import-contacts-form">
        <div className="card-header">
          <h5>Импорт контактов</h5>
          <button 
            className="btn-close"
            onClick={() => setShowImportForm(false)}
          ></button>
        </div>
        <div className="card-body">
          {importError && (
            <div className="alert alert-danger" role="alert">
              {importError}
            </div>
          )}
          
          <form onSubmit={handleImportContacts}>
            <div className="mb-3">
              <label htmlFor="importData" className="form-label">Данные для импорта</label>
              <textarea 
                className="form-control" 
                id="importData"
                rows="5"
                value={importText}
                onChange={(e) => setImportText(e.target.value)}
                placeholder="Введите данные в формате: Имя, +79123456789 (по одному контакту на строку)"
                required
              ></textarea>
              <div className="form-text">
                Пример:<br />
                Иван Иванов, +79001112233<br />
                Мария Петрова, +79004445566
              </div>
            </div>
            
            <div className="text-end">
              <button 
                type="button" 
                className="btn btn-secondary me-2"
                onClick={() => setShowImportForm(false)}
              >
                Отмена
              </button>
              <button type="submit" className="btn btn-primary">Импортировать</button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="contact-list">
      <div className="contacts-header">
        <h2>Контакты</h2>
        <div className="contacts-actions">
          <button 
            className="btn btn-outline-primary me-2"
            onClick={() => {
              setShowImportForm(true);
              setShowAddForm(false);
            }}
          >
            <i data-feather="upload"></i> Импорт
          </button>
          <button 
            className="btn btn-primary"
            onClick={() => {
              setShowAddForm(true);
              setShowImportForm(false);
            }}
          >
            <i data-feather="plus"></i> Добавить контакт
          </button>
        </div>
      </div>
      
      <div className="contacts-search mb-3">
        <div className="input-group">
          <span className="input-group-text">
            <i data-feather="search"></i>
          </span>
          <input 
            type="text" 
            className="form-control" 
            placeholder="Поиск контактов..." 
          />
        </div>
      </div>
      
      {renderContactsList()}
      
      {showAddForm && renderAddContactForm()}
      
      {showImportForm && renderImportContactsForm()}
    </div>
  );
}

export default ContactList;
