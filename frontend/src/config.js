// Конфигурация для API
// Определение базового URL для API
// При разработке используем URL бэкенда на Replit или Render
// Обратите внимание, что логика выбора URL теперь исправлена для корректной работы на разных хостингах

const getApiUrl = () => {
  // Для локальной разработки
  if (window.location.hostname === "localhost") {
    return "http://localhost:5000";
  }
  
  // Если мы на Replit, используем тот же домен для API
  if (window.location.hostname.endsWith(".replit.app") || 
      window.location.hostname.includes("replit.dev") || 
      window.location.hostname.includes(".id.repl.co")) {
    console.log("Обнаружен хостинг Replit, используем локальный API");
    return window.location.origin;
  }
  
  // Если есть env переменная, используем её
  if (process.env.REACT_APP_API_URL) {
    console.log("Используем API из переменной окружения:", process.env.REACT_APP_API_URL);
    return process.env.REACT_APP_API_URL;
  }
  
  // На Vercel используем бэкенд Render
  if (window.location.hostname.includes("vercel.app")) {
    console.log("Обнаружен хостинг Vercel, используем API на Render");
    return "https://tgm-mthw.onrender.com";
  }
  
  // Fallback на Render для любых других хостингов
  console.log("Используем API на Render (fallback)");
  return "https://tgm-mthw.onrender.com";
};

const API_URL = getApiUrl();

export default {
  API_URL
};