/** Application header component — Modern SaaS style */
import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from 'react-bootstrap';
import { useAuth } from '../context/AuthContext';

interface AppHeaderProps {
  showAdminLink?: boolean;
  showDashboardLink?: boolean;
}

const AppHeader: React.FC<AppHeaderProps> = ({ 
  showAdminLink = false, 
  showDashboardLink = false 
}) => {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white border-b border-default sticky top-0 z-50 shadow-sm">
      <div className="container-fluid">
        <div className="d-flex justify-content-between align-items-center py-3">
          {/* Logo & Navigation */}
          <div className="d-flex align-items-center gap-4">
            <Link to="/dashboard" className="text-decoration-none d-flex align-items-center gap-2">
              <div className="w-8 h-8 bg-brand rounded-lg d-flex align-items-center justify-center">
                <span className="text-invert font-bold text-sm">W</span>
              </div>
              <span className="font-semibold text-lg text-main">WWWAnalys</span>
            </Link>
            
            <nav className="d-flex gap-1">
              {showDashboardLink && (
                <Link 
                  to="/dashboard" 
                  className="text-decoration-none text-sub hover:text-brand px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Панель управления
                </Link>
              )}
              <Link
                to="/plans"
                className="text-decoration-none text-sub hover:text-brand px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Планирование
              </Link>
              <Link
                to="/analytics"
                className="text-decoration-none text-sub hover:text-brand px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Аналитика
              </Link>
              <Link
                to="/agent"
                className="text-decoration-none text-sub hover:text-brand px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                🤖 Агент
              </Link>
              <Link
                to="/digest"
                className="text-decoration-none text-sub hover:text-brand px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                📅 Сводка
              </Link>
              {showAdminLink && user?.is_admin && (
                <Link
                  to="/admin"
                  className="text-decoration-none text-sub hover:text-brand px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  ⚙️ Настройки
                </Link>
              )}
              {user?.is_admin && (
                <Link
                  to="/tech-cards"
                  className="text-decoration-none text-sub hover:text-brand px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  База знаний
                </Link>
              )}
              {user?.is_admin && (
                <Link
                  to="/reference"
                  className="text-decoration-none text-sub hover:text-brand px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Справочники
                </Link>
              )}
            </nav>
          </div>

          {/* User & Actions */}
          <div className="d-flex align-items-center gap-3">
            <div className="d-flex align-items-center gap-2 px-3 py-2 bg-surface-gray rounded-lg">
              <div className="d-flex flex-col">
                <span className="text-sm font-medium text-main">{user?.email}</span>
                <span className="text-xs text-hint">{user?.is_admin ? 'Администратор' : 'Пользователь'}</span>
              </div>
            </div>
            <Button 
              variant="outline-danger" 
              size="sm"
              onClick={logout}
            >
              Выйти
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default AppHeader;