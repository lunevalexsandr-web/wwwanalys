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
    <div className="min-h-screen d-flex align-items-center justify-content-center bg-light">
      <div className="w-100 max-w-md">
        <div className="card shadow">
          <div className="card-body p-5">
            <div className="text-center mb-4">
              <h2 className="card-title h3">Вход в систему</h2>
              <p className="text-muted">Пожалуйста, войдите в ваш аккаунт</p>
            </div>
            
            <form onSubmit={handleSubmit}>
              {error && (
                <div className="alert alert-danger" role="alert">
                  {error}
                </div>
              )}
              
              <div className="mb-3">
                <label htmlFor="username" className="form-label">
                  Имя пользователя
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  className="form-control"
                  placeholder="Введите имя"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
              
              <div className="mb-4">
                <label htmlFor="password" className="form-label">
                  Пароль
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  className="form-control"
                  placeholder="Введите пароль"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>

              <div className="d-grid">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="btn btn-primary"
                >
                  {isLoading ? 'Вход...' : 'Войти'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;