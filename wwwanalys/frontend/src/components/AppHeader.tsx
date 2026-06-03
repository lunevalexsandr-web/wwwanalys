/** Application header component */
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
    <header className="app-header">
      <div className="container-fluid">
        <div className="d-flex justify-content-between align-items-center py-3">
          <div className="d-flex align-items-center">
            <Link to="/dashboard" className="text-decoration-none">
              <h1 className="h4 mb-0 text-primary">WWWAnalys</h1>
            </Link>
            <nav className="ms-4 d-flex gap-3">
              {showDashboardLink && (
                <Link to="/dashboard" className="text-decoration-none text-muted">
                  <i className="bi bi-house-fill me-1"></i>
                  Панель управления
                </Link>
              )}
              {showAdminLink && user?.is_admin && (
                <Link to="/admin" className="text-decoration-none text-muted">
                  <i className="bi bi-gear-fill me-1"></i>
                  Админ-панель
                </Link>
              )}
            </nav>
          </div>
          <div className="d-flex align-items-center gap-3">
            <div className="d-flex align-items-center">
              <i className="bi bi-person-circle me-2 text-primary"></i>
              <span className="text-dark">
                {user?.email} ({user?.is_admin ? 'ADMIN' : 'USER'})
              </span>
            </div>
            <Button variant="outline-danger" onClick={logout}>
              <i className="bi bi-box-arrow-right me-1"></i>
              Выйти
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default AppHeader;