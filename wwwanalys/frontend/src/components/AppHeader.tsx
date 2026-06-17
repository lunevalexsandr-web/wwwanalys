/** Application header component — Modern SaaS style */
import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from 'react-bootstrap';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, Calendar, Settings, LogOut, User } from 'lucide-react';

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
    <header className="bg-white border-b border-border sticky top-0 z-50 shadow-sm">
      <div className="container-fluid">
        <div className="d-flex justify-content-between align-items-center py-3">
          {/* Logo & Navigation */}
          <div className="d-flex align-items-center gap-4">
            <Link to="/dashboard" className="text-decoration-none d-flex align-items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg d-flex align-items-center justify-center">
                <span className="text-white font-bold text-sm">W</span>
              </div>
              <span className="font-semibold text-lg text-text-primary">WWWAnalys</span>
            </Link>
            
            <nav className="d-flex gap-1">
              {showDashboardLink && (
                <Link 
                  to="/dashboard" 
                  className="text-decoration-none text-text-secondary hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  <LayoutDashboard size={16} className="me-1" />
                  Панель управления
                </Link>
              )}
              <Link 
                to="/plans" 
                className="text-decoration-none text-text-secondary hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                <Calendar size={16} className="me-1" />
                Планирование
              </Link>
              {showAdminLink && user?.is_admin && (
                <Link 
                  to="/admin" 
                  className="text-decoration-none text-text-secondary hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  <Settings size={16} className="me-1" />
                  Админ-панель
                </Link>
              )}
            </nav>
          </div>

          {/* User & Actions */}
          <div className="d-flex align-items-center gap-3">
            <div className="d-flex align-items-center gap-2 px-3 py-2 bg-background-gray rounded-lg">
              <div className="w-8 h-8 bg-primary-100 rounded-full d-flex align-items-center justify-center">
                <User size={16} className="text-primary" />
              </div>
              <div className="d-flex flex-col">
                <span className="text-sm font-medium text-text-primary">{user?.email}</span>
                <span className="text-xs text-text-muted">{user?.is_admin ? 'Администратор' : 'Пользователь'}</span>
              </div>
            </div>
            <Button 
              variant="outline-danger" 
              size="sm"
              onClick={logout}
              className="d-flex align-items-center gap-1"
            >
              <LogOut size={14} />
              Выйти
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default AppHeader;