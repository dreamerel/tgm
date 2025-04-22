import React, { useState } from 'react';
import api from '../api';

function TelegramVerification({ account, onSuccess, onCancel }) {
  const [step, setStep] = useState('sendCode');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState(''); // Для 2FA
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [phoneCodeHash, setPhoneCodeHash] = useState('');
  const [requiresTwoFactor, setRequiresTwoFactor] = useState(false);
  
  // Автоматически отправляем запрос на код при открытии компонента
  React.useEffect(() => {
    if (step === 'sendCode') {
      handleSendCode();
    }
  }, []);
  
  // Отправка запроса на код подтверждения
  const handleSendCode = async () => {
    if (!account || !account.phone || !account.api_id || !account.api_hash) {
      setError('Недостаточно данных для авторизации');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const response = await api.post('/api/telegram/accounts/send-code', {
        phone: account.phone,
        api_id: account.api_id,
        api_hash: account.api_hash
      });
      
      if (response.data.success) {
        setPhoneCodeHash(response.data.phone_code_hash);
        if (response.data.authorized) {
          // Если аккаунт уже авторизован
          onSuccess(response.data);
        } else {
          // Переходим к вводу кода
          setStep('enterCode');
        }
      } else {
        setError(response.data.error || 'Не удалось отправить код подтверждения');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Произошла ошибка при отправке запроса');
      console.error('Ошибка при отправке кода:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Проверка кода подтверждения
  const handleVerifyCode = async (e) => {
    e.preventDefault();
    
    if (!code) {
      setError('Введите код подтверждения');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const data = {
        phone: account.phone,
        code: code,
        phone_code_hash: phoneCodeHash,
        api_id: account.api_id,
        api_hash: account.api_hash
      };
      
      // Если требуется 2FA и пароль указан
      if (requiresTwoFactor && password) {
        data.password = password;
      }
      
      const response = await api.post('/api/telegram/accounts/verify-code', data);
      
      if (response.data.success) {
        onSuccess(response.data);
      } else {
        setError(response.data.error || 'Неверный код подтверждения');
      }
    } catch (err) {
      const responseData = err.response?.data;
      
      if (responseData?.two_factor_required) {
        // Если требуется двухфакторная аутентификация
        setRequiresTwoFactor(true);
        setError('Требуется пароль двухфакторной аутентификации');
      } else {
        setError(responseData?.error || 'Произошла ошибка при проверке кода');
      }
      
      console.error('Ошибка при проверке кода:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Рендер шага отправки кода
  const renderSendCodeStep = () => (
    <div className="telegram-verification-step">
      <h5>Авторизация в Telegram</h5>
      <p>
        Для завершения добавления аккаунта Telegram необходимо пройти авторизацию.
        Нажмите кнопку "Отправить код", чтобы получить код подтверждения.
      </p>
      <div className="d-flex justify-content-between mt-3">
        <button 
          className="btn btn-secondary" 
          onClick={onCancel}
          disabled={loading}
        >
          Отмена
        </button>
        <button 
          className="btn btn-primary" 
          onClick={handleSendCode}
          disabled={loading}
        >
          {loading ? 'Отправка...' : 'Отправить код'}
        </button>
      </div>
    </div>
  );
  
  // Рендер шага ввода кода
  const renderEnterCodeStep = () => (
    <div className="telegram-verification-step">
      <h5>Введите код подтверждения</h5>
      <p>
        На ваш аккаунт Telegram отправлен код подтверждения.
        Проверьте приложение Telegram на вашем устройстве и введите полученный код в поле ниже.
      </p>
      
      <form onSubmit={handleVerifyCode}>
        <div className="mb-3">
          <label htmlFor="verificationCode" className="form-label">Код подтверждения</label>
          <input 
            type="text" 
            className="form-control" 
            id="verificationCode"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="12345"
            required
          />
        </div>
        
        {requiresTwoFactor && (
          <div className="mb-3">
            <label htmlFor="twoFactorPassword" className="form-label">Пароль двухфакторной аутентификации</label>
            <input 
              type="password" 
              className="form-control" 
              id="twoFactorPassword"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Введите пароль 2FA"
              required
            />
            <div className="form-text">
              Для вашего аккаунта настроена двухфакторная аутентификация.
              Введите пароль, который вы установили в настройках безопасности Telegram.
            </div>
          </div>
        )}
        
        <div className="d-flex justify-content-between mt-3">
          <button 
            type="button"
            className="btn btn-secondary" 
            onClick={() => {
              setStep('sendCode');
              handleSendCode(); // Автоматически отправляем новый код
            }}
            disabled={loading}
          >
            Запросить новый код
          </button>
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Проверка...' : 'Подтвердить'}
          </button>
        </div>
      </form>
    </div>
  );
  
  return (
    <div className="card telegram-verification">
      <div className="card-body">
        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}
        
        {loading && step === 'sendCode' && (
          <div className="text-center my-5">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Отправка запроса на код верификации...</span>
            </div>
            <p className="mt-3">Отправка запроса на код верификации в Telegram...</p>
          </div>
        )}
        
        {!loading && step === 'sendCode' && renderSendCodeStep()}
        {step === 'enterCode' && renderEnterCodeStep()}
      </div>
    </div>
  );
}

export default TelegramVerification;