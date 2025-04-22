// Конфигурация для API
// В процессе сборки REACT_APP_API_URL берется из переменных окружения Vercel
// При разработке используем URL бэкенда на Render или локальный
const API_URL = process.env.REACT_APP_API_URL || 
                "https://tgm-backend.onrender.com" || 
                "http://localhost:5000";

export default {
  API_URL
};