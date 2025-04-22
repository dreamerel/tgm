import React, { useState } from 'react';
import api from '../api';

const ApiTester = () => {
  const [testUrl, setTestUrl] = useState('/api/health');
  const [testMethod, setTestMethod] = useState('GET');
  const [testData, setTestData] = useState('{}');
  const [responseData, setResponseData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleTest = async () => {
    setIsLoading(true);
    setError(null);
    setResponseData(null);

    try {
      let response;
      const data = testData ? JSON.parse(testData) : {};

      switch (testMethod) {
        case 'GET':
          response = await api.get(testUrl);
          break;
        case 'POST':
          response = await api.post(testUrl, data);
          break;
        case 'PUT':
          response = await api.put(testUrl, data);
          break;
        case 'DELETE':
          response = await api.delete(testUrl);
          break;
        default:
          response = await api.get(testUrl);
      }

      setResponseData({
        data: response.data,
        status: response.status,
        headers: response.headers,
      });
    } catch (err) {
      setError({
        message: err.message,
        response: err.response ? {
          data: err.response.data,
          status: err.response.status,
          headers: err.response.headers,
        } : null,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="api-tester card">
      <div className="card-header">
        <h4>API Тестер</h4>
      </div>
      <div className="card-body">
        <div className="mb-3">
          <label htmlFor="testUrl" className="form-label">URL</label>
          <input
            type="text"
            className="form-control"
            id="testUrl"
            value={testUrl}
            onChange={(e) => setTestUrl(e.target.value)}
          />
        </div>
        <div className="mb-3">
          <label htmlFor="testMethod" className="form-label">Метод</label>
          <select
            className="form-select"
            id="testMethod"
            value={testMethod}
            onChange={(e) => setTestMethod(e.target.value)}
          >
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="DELETE">DELETE</option>
          </select>
        </div>
        {(testMethod === 'POST' || testMethod === 'PUT') && (
          <div className="mb-3">
            <label htmlFor="testData" className="form-label">Данные (JSON)</label>
            <textarea
              className="form-control"
              id="testData"
              rows="4"
              value={testData}
              onChange={(e) => setTestData(e.target.value)}
            ></textarea>
          </div>
        )}
        <button
          className="btn btn-primary"
          onClick={handleTest}
          disabled={isLoading}
        >
          {isLoading ? 'Выполняется...' : 'Выполнить запрос'}
        </button>
      </div>

      {responseData && (
        <div className="card-footer">
          <h5>Ответ</h5>
          <div className="mb-2">
            <strong>Статус:</strong> {responseData.status}
          </div>
          <div className="mb-2">
            <strong>Заголовки:</strong>
            <pre>{JSON.stringify(responseData.headers, null, 2)}</pre>
          </div>
          <div>
            <strong>Данные:</strong>
            <pre>{JSON.stringify(responseData.data, null, 2)}</pre>
          </div>
        </div>
      )}

      {error && (
        <div className="card-footer text-danger">
          <h5>Ошибка</h5>
          <div className="mb-2">
            <strong>Сообщение:</strong> {error.message}
          </div>
          {error.response && (
            <>
              <div className="mb-2">
                <strong>Статус:</strong> {error.response.status}
              </div>
              <div className="mb-2">
                <strong>Заголовки:</strong>
                <pre>{JSON.stringify(error.response.headers, null, 2)}</pre>
              </div>
              <div>
                <strong>Данные:</strong>
                <pre>{JSON.stringify(error.response.data, null, 2)}</pre>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default ApiTester;