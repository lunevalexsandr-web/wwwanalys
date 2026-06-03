import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Неверное имя пользователя или пароль');
    }
  };

  return (
    <div className="login-container">
      <div className="w-100 max-w-md">
        <div className="card login-card">
          <div className="card-body p-5">
            <div className="text-center mb-4">
              <div className="mb-3">
                <i className="bi bi-shield-lock display-4 text-primary"></i>
              </div>
              <h2 className="card-title h4 mb-2">Вход в систему</h2>
              <p className="text-muted mb-4">Пожалуйста, войдите в ваш аккаунт</p>
            </div>
            
            <form onSubmit={handleSubmit}>
              {error && (
                <div className="alert alert-danger alert-dismissible fade show" role="alert">
                  <i className="bi bi-exclamation-triangle-fill me-2"></i>
                  {error}
                  <button type="button" className="btn-close" aria-label="Close" onClick={() => setError('')}></button>
                </div>
              )}
              
              <div className="mb-4">
                <label htmlFor="username" className="form-label">
                  <i className="bi bi-person-fill me-1"></i>
                  Имя пользователя
                </label>
                <div className="input-group">
                  <span className="input-group-text bg-light border-end-0">
                    <i className="bi bi-person text-muted"></i>
                  </span>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    autoComplete="username"
                    required
                    className="form-control border-start-0"
                    placeholder="Введите имя пользователя"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                  />
                </div>
              </div>
              
              <div className="mb-4">
                <label htmlFor="password" className="form-label">
                  <i className="bi bi-lock-fill me-1"></i>
                  Пароль
                </label>
                <div className="input-group">
                  <span className="input-group-text bg-light border-end-0">
                    <i className="bi bi-lock text-muted"></i>
                  </span>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required
                    className="form-control border-start-0"
                    placeholder="Введите пароль"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <button 
                    className="btn btn-outline-secondary border-start-0" 
                    type="button"
                    onClick={() => setPassword('')}
                  >
                    <i className="bi bi-x-lg"></i>
                  </button>
                </div>
              </div>

              <div className="d-grid gap-2 mt-4">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="btn btn-primary btn-lg"
                >
                  {isLoading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      Вход...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-box-arrow-in-right me-2"></i>
                      Войти
                    </>
                  )}
                </button>
              </div>
            </form>

            <div className="text-center mt-4">
              <small className="text-muted">
                <i className="bi bi-info-circle me-1"></i>
                Забыли пароль? Обратитесь к администратору
              </small>
            </div>
          </div>
        </div>
        
        <div className="text-center mt-4">
          <small className="text-light opacity-75">
            © 2024 WWWAnalys. Все права защищены.
          </small>
        </div>
      </div>
    </div>
  );
};

export default Login;