import React from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter as Router } from 'react-router-dom';
import App from './App';
import { AuthProvider } from './context/AuthContext';
import './styles/main.css';
import './styles/telegram-style.css'; // Подключаем новый стиль в стиле Telegram

// Используем createRoot для React 18+ или render для более старых версий
const root = document.getElementById('root');
if (ReactDOM.createRoot) {
  // React 18+
  const rootElement = ReactDOM.createRoot(root);
  rootElement.render(
    <React.StrictMode>
      <Router>
        <AuthProvider>
          <App />
        </AuthProvider>
      </Router>
    </React.StrictMode>
  );
} else {
  // React < 18
  ReactDOM.render(
    <React.StrictMode>
      <Router>
        <AuthProvider>
          <App />
        </AuthProvider>
      </Router>
    </React.StrictMode>,
    root
  );
}
