import React, { useState, useEffect } from 'react';
import api from '../api';

function Statistics({ account }) {
  const [statistics, setStatistics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [period, setPeriod] = useState(7); // По умолчанию 7 дней

  // Загрузка статистики при изменении аккаунта
  useEffect(() => {
    const fetchStatistics = async () => {
      if (!account) return;
      
      try {
        setLoading(true);
        const response = await api.get(`/api/telegram/statistics?account_id=${account.id}&days=${period}`);
        setStatistics(response.data.statistics);
      } catch (err) {
        setError('Не удалось загрузить статистику');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchStatistics();
  }, [account, period]);

  // Форматирование даты для отображения
  const formatDate = (dateString) => {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU');
  };

  // Вычисление общего количества сообщений
  const calculateTotals = () => {
    let totalSent = 0;
    let totalReceived = 0;
    
    statistics.forEach(stat => {
      totalSent += stat.sent_messages || 0;
      totalReceived += stat.received_messages || 0;
    });
    
    return { totalSent, totalReceived };
  };

  // Рендер карточек с общей статистикой
  const renderStatCards = () => {
    const { totalSent, totalReceived } = calculateTotals();
    
    return (
      <div className="stat-cards">
        <div className="row">
          <div className="col-md-4">
            <div className="card stat-card">
              <div className="card-body">
                <h5 className="card-title">Отправлено</h5>
                <div className="stat-value">{totalSent}</div>
                <div className="stat-icon sent-icon">
                  <i data-feather="send"></i>
                </div>
              </div>
            </div>
          </div>
          
          <div className="col-md-4">
            <div className="card stat-card">
              <div className="card-body">
                <h5 className="card-title">Получено</h5>
                <div className="stat-value">{totalReceived}</div>
                <div className="stat-icon received-icon">
                  <i data-feather="message-circle"></i>
                </div>
              </div>
            </div>
          </div>
          
          <div className="col-md-4">
            <div className="card stat-card">
              <div className="card-body">
                <h5 className="card-title">Всего</h5>
                <div className="stat-value">{totalSent + totalReceived}</div>
                <div className="stat-icon total-icon">
                  <i data-feather="bar-chart-2"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Рендер таблицы со статистикой по дням
  const renderStatisticsTable = () => {
    if (loading && statistics.length === 0) {
      return (
        <div className="statistics-loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Загрузка...</span>
          </div>
          <p>Загрузка статистики...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="statistics-error">
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        </div>
      );
    }

    if (statistics.length === 0) {
      return (
        <div className="no-statistics">
          <p>Нет данных о сообщениях за выбранный период</p>
        </div>
      );
    }

    return (
      <div className="statistics-table-wrapper">
        <table className="table table-hover">
          <thead>
            <tr>
              <th scope="col">Дата</th>
              <th scope="col">Отправлено</th>
              <th scope="col">Получено</th>
              <th scope="col">Всего</th>
            </tr>
          </thead>
          <tbody>
            {statistics.map(stat => (
              <tr key={stat.id}>
                <td>{formatDate(stat.date)}</td>
                <td>{stat.sent_messages || 0}</td>
                <td>{stat.received_messages || 0}</td>
                <td>{(stat.sent_messages || 0) + (stat.received_messages || 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="statistics">
      <div className="statistics-header">
        <h2>Статистика сообщений</h2>
        
        <div className="period-selector">
          <label htmlFor="period" className="form-label me-2">Период:</label>
          <select 
            id="period" 
            className="form-select"
            value={period}
            onChange={(e) => setPeriod(parseInt(e.target.value))}
          >
            <option value="7">7 дней</option>
            <option value="14">14 дней</option>
            <option value="30">30 дней</option>
          </select>
        </div>
      </div>
      
      {renderStatCards()}
      
      <div className="statistics-chart mt-4">
        <h4>График активности</h4>
        <div className="chart-placeholder">
          <p className="text-center">График будет доступен в следующей версии</p>
        </div>
      </div>
      
      <div className="statistics-table mt-4">
        <h4>Данные по дням</h4>
        {renderStatisticsTable()}
      </div>
    </div>
  );
}

export default Statistics;
