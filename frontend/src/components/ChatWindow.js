import React, { useState, useEffect, useRef } from 'react';
import api from '../api';

function ChatWindow({ account }) {
  const [chats, setChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const messagesEndRef = useRef(null);

  // Получение списка чатов при изменении аккаунта
  useEffect(() => {
    const fetchChats = async () => {
      if (!account) return;
      
      try {
        setLoading(true);
        const response = await api.get(`/api/telegram/chats?account_id=${account.id}`);
        setChats(response.data.chats);
        
        // Выбираем первый чат по умолчанию
        if (response.data.chats.length > 0 && !selectedChat) {
          setSelectedChat(response.data.chats[0]);
        }
      } catch (err) {
        setError('Не удалось загрузить чаты');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchChats();
    
    // Интервал для обновления списка чатов
    const interval = setInterval(fetchChats, 10000);
    
    return () => clearInterval(interval);
  }, [account]);

  // Получение сообщений выбранного чата
  useEffect(() => {
    const fetchMessages = async () => {
      if (!selectedChat) return;
      
      try {
        const response = await api.get(`/api/telegram/messages?chat_id=${selectedChat.id}`);
        setMessages(response.data.messages);
        
        // Прокручиваем к последнему сообщению
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      } catch (err) {
        console.error('Не удалось загрузить сообщения', err);
      }
    };
    
    fetchMessages();
    
    // Интервал для обновления сообщений
    const interval = setInterval(fetchMessages, 5000);
    
    return () => clearInterval(interval);
  }, [selectedChat]);

  // Прокрутка к последнему сообщению при его добавлении
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Обработчик отправки сообщения
  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!newMessage.trim() || !selectedChat) return;
    
    try {
      await api.post('/api/telegram/messages', {
        chat_id: selectedChat.id,
        text: newMessage
      });
      
      // Очищаем поле ввода
      setNewMessage('');
      
      // Обновляем сообщения сразу после отправки
      const response = await api.get(`/api/telegram/messages?chat_id=${selectedChat.id}`);
      setMessages(response.data.messages);
    } catch (err) {
      console.error('Не удалось отправить сообщение', err);
    }
  };

  // Форматирование даты сообщения
  const formatMessageDate = (timestamp) => {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Рендер списка чатов
  const renderChatsList = () => {
    if (loading && chats.length === 0) {
      return (
        <div className="chats-loading">
          <div className="spinner-border spinner-border-sm text-primary" role="status">
            <span className="visually-hidden">Загрузка...</span>
          </div>
          <p>Загрузка чатов...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="chats-error">
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        </div>
      );
    }

    if (chats.length === 0) {
      return (
        <div className="no-chats">
          <p>У вас пока нет чатов</p>
        </div>
      );
    }

    return (
      <div className="chats-list">
        {chats.map(chat => (
          <div 
            key={chat.id} 
            className={`chat-item ${selectedChat?.id === chat.id ? 'active' : ''}`}
            onClick={() => setSelectedChat(chat)}
          >
            <div className="chat-avatar">
              {chat.contact?.name?.charAt(0) || 'C'}
            </div>
            <div className="chat-info">
              <div className="chat-name">{chat.contact?.name || 'Неизвестный контакт'}</div>
              <div className="chat-last-message">{chat.last_message || 'Нет сообщений'}</div>
            </div>
            {chat.unread_count > 0 && (
              <div className="chat-unread-badge">{chat.unread_count}</div>
            )}
          </div>
        ))}
      </div>
    );
  };

  // Рендер сообщений чата
  const renderMessages = () => {
    if (!selectedChat) {
      return (
        <div className="no-chat-selected">
          <p>Выберите чат для начала общения</p>
        </div>
      );
    }

    return (
      <div className="messages-container">
        <div className="messages-header">
          <div className="contact-avatar">
            {selectedChat.contact?.name?.charAt(0) || 'C'}
          </div>
          <div className="contact-info">
            <div className="contact-name">{selectedChat.contact?.name || 'Неизвестный контакт'}</div>
            <div className="contact-status">В сети</div>
          </div>
        </div>
        
        <div className="messages-list">
          {messages.length === 0 ? (
            <div className="no-messages">
              <p>Нет сообщений</p>
            </div>
          ) : (
            messages.map(message => (
              <div 
                key={message.id} 
                className={`message ${message.sender_id === account.user_id ? 'message-sent' : 'message-received'}`}
              >
                <div className="message-content">
                  <div className="message-text">{message.text}</div>
                  <div className="message-time">{formatMessageDate(message.timestamp)}</div>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="messages-input">
          <form onSubmit={handleSendMessage}>
            <div className="input-group">
              <input 
                type="text" 
                className="form-control" 
                placeholder="Введите сообщение..." 
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
              />
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={!newMessage.trim()}
              >
                <i data-feather="send"></i>
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="chat-window">
      <div className="chats-sidebar">
        <div className="chats-search">
          <div className="input-group">
            <span className="input-group-text">
              <i data-feather="search"></i>
            </span>
            <input 
              type="text" 
              className="form-control" 
              placeholder="Поиск чатов..." 
            />
          </div>
        </div>
        
        {renderChatsList()}
      </div>
      
      <div className="messages-wrapper">
        {renderMessages()}
      </div>
    </div>
  );
}

export default ChatWindow;
