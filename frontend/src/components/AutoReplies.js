import React, { useState, useEffect } from 'react';
import api from '../api';

function AutoReplies({ account }) {
  const [autoReplies, setAutoReplies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [showAddForm, setShowAddForm] = useState(false);
  const [newAutoReply, setNewAutoReply] = useState({ 
    trigger_phrase: '', 
    reply_text: '',
    is_active: true
  });
  const [formError, setFormError] = useState('');

  // Загрузка авто-ответов при изменении аккаунта
  useEffect(() => {
    const fetchAutoReplies = async () => {
      if (!account) return;
      
      try {
        setLoading(true);
        const response = await api.get(`/api/telegram/auto-replies?account_id=${account.id}`);
        setAutoReplies(response.data.auto_replies);
      } catch (err) {
        setError('Не удалось загрузить авто-ответы');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAutoReplies();
  }, [account]);

  // Обработчик добавления нового авто-ответа
  const handleAddAutoReply = async (e) => {
    e.preventDefault();
    setFormError('');
    
    if (!newAutoReply.trigger_phrase || !newAutoReply.reply_text) {
      setFormError('Заполните все обязательные поля');
      return;
    }
    
    try {
      const response = await api.post('/api/telegram/auto-replies', {
        account_id: account.id,
        trigger_phrase: newAutoReply.trigger_phrase,
        reply_text: newAutoReply.reply_text,
        is_active: newAutoReply.is_active
      });
      
      // Добавляем новый авто-ответ в список
      setAutoReplies([...autoReplies, response.data.auto_reply]);
      
      // Сбрасываем форму
      setNewAutoReply({ trigger_phrase: '', reply_text: '', is_active: true });
      setShowAddForm(false);
    } catch (err) {
      setFormError(err.response?.data?.error || 'Не удалось добавить авто-ответ');
    }
  };

  // Обработчик изменения статуса авто-ответа
  const handleToggleStatus = async (autoReplyId, isActive) => {
    try {
      await api.put(`/api/telegram/auto-replies/${autoReplyId}`, {
        is_active: !isActive
      });
      
      // Обновляем статус в списке
      setAutoReplies(autoReplies.map(item => 
        item.id === autoReplyId 
          ? { ...item, is_active: !isActive } 
          : item
      ));
    } catch (err) {
      console.error('Не удалось изменить статус авто-ответа', err);
    }
  };

  // Рендер списка авто-ответов
  const renderAutoRepliesList = () => {
    if (loading && autoReplies.length === 0) {
      return (
        <div className="auto-replies-loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Загрузка...</span>
          </div>
          <p>Загрузка авто-ответов...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="auto-replies-error">
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        </div>
      );
    }

    if (autoReplies.length === 0) {
      return (
        <div className="no-auto-replies">
          <p>У вас пока нет настроенных авто-ответов</p>
        </div>
      );
    }

    return (
      <div className="auto-replies-table-wrapper">
        <table className="table table-hover">
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Фраза-триггер</th>
              <th scope="col">Текст ответа</th>
              <th scope="col">Статус</th>
              <th scope="col">Действия</th>
            </tr>
          </thead>
          <tbody>
            {autoReplies.map((autoReply, index) => (
              <tr key={autoReply.id}>
                <td>{index + 1}</td>
                <td>{autoReply.trigger_phrase}</td>
                <td>{autoReply.reply_text}</td>
                <td>
                  <span className={`badge ${autoReply.is_active ? 'bg-success' : 'bg-secondary'}`}>
                    {autoReply.is_active ? 'Активен' : 'Отключен'}
                  </span>
                </td>
                <td>
                  <button 
                    className={`btn btn-sm ${autoReply.is_active ? 'btn-outline-secondary' : 'btn-outline-success'}`}
                    onClick={() => handleToggleStatus(autoReply.id, autoReply.is_active)}
                  >
                    {autoReply.is_active ? 'Отключить' : 'Включить'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Рендер формы добавления авто-ответа
  const renderAddAutoReplyForm = () => {
    return (
      <div className="card add-auto-reply-form">
        <div className="card-header">
          <h5>Добавить авто-ответ</h5>
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
          
          <form onSubmit={handleAddAutoReply}>
            <div className="mb-3">
              <label htmlFor="triggerPhrase" className="form-label">Фраза-триггер</label>
              <input 
                type="text" 
                className="form-control" 
                id="triggerPhrase"
                value={newAutoReply.trigger_phrase}
                onChange={(e) => setNewAutoReply({ ...newAutoReply, trigger_phrase: e.target.value })}
                placeholder="Введите фразу, на которую должен быть ответ"
                required
              />
              <div className="form-text">Бот будет отвечать, если сообщение содержит эту фразу</div>
            </div>
            
            <div className="mb-3">
              <label htmlFor="replyText" className="form-label">Текст ответа</label>
              <textarea 
                className="form-control" 
                id="replyText"
                rows="3"
                value={newAutoReply.reply_text}
                onChange={(e) => setNewAutoReply({ ...newAutoReply, reply_text: e.target.value })}
                placeholder="Введите текст, который будет отправлен в ответ"
                required
              ></textarea>
            </div>
            
            <div className="mb-3 form-check">
              <input 
                type="checkbox" 
                className="form-check-input" 
                id="isActive"
                checked={newAutoReply.is_active}
                onChange={(e) => setNewAutoReply({ ...newAutoReply, is_active: e.target.checked })}
              />
              <label className="form-check-label" htmlFor="isActive">Активен</label>
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

  return (
    <div className="auto-replies">
      <div className="auto-replies-header">
        <h2>Авто-ответы</h2>
        <button 
          className="btn btn-primary"
          onClick={() => setShowAddForm(true)}
        >
          <i data-feather="plus"></i> Добавить авто-ответ
        </button>
      </div>
      
      <div className="auto-replies-description mb-3">
        <p>
          Настройте автоматические ответы на входящие сообщения. 
          Когда кто-то отправляет сообщение, содержащее указанную фразу, 
          система автоматически отвечает заданным текстом.
        </p>
      </div>
      
      {renderAutoRepliesList()}
      
      {showAddForm && renderAddAutoReplyForm()}
    </div>
  );
}

export default AutoReplies;
