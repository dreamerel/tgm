// Конфигурация для API
// Определение базового URL для API
// При разработке используем URL бэкенда на Replit или Render
// Обратите внимание, что логика выбора URL изменена, теперь первым рассматривается window.location.origin
const getApiUrl = () => {
  // В режиме разработки используем window.location.origin
  if (window.location.hostname === "localhost") {
    return "http://localhost:5000";
  }
  
  // Если мы на Replit, используем тот же домен
  if (window.location.hostname.includes("replit")) {
    return window.location.origin;
  }
  
  // Если есть env переменная, используем её
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // Fallback на Render
  return "https://tgm-mthw.onrender.com";
};

const API_URL = getApiUrl();

export default {
  API_URL
};