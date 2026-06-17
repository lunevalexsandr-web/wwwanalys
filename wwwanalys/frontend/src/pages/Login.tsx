import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import AuthModal from '../components/AuthModal';
import '../components/AuthModal.css';

const Login: React.FC = () => {
  const [showModal, setShowModal] = useState(true);
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleSuccess = () => {
    navigate('/dashboard');
  };

  // Если пользователь уже авторизован, показываем информацию
  if (user) {
    return (
      <div className="min-vh-100 d-flex align-items-center justify-content-center"
           style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <div className="text-center text-white">
          <h2>Вы уже авторизованы</h2>
          <p className="mt-2">Перенаправление на панель управления...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-vh-100 d-flex align-items-center justify-content-center"
         style={{
           background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
           padding: '16px'
         }}>
      {/* Background decoration */}
      <div className="position-absolute overflow-hidden w-100 h-100" style={{ zIndex: 0 }}>
        <div className="position-absolute rounded-circle"
             style={{
               width: '400px',
               height: '400px',
               background: 'rgba(255,255,255,0.1)',
               top: '-100px',
               right: '-100px',
               filter: 'blur(80px)'
             }} />
        <div className="position-absolute rounded-circle"
             style={{
               width: '300px',
               height: '300px',
               background: 'rgba(255,255,255,0.08)',
               bottom: '-50px',
               left: '-50px',
               filter: 'blur(60px)'
             }} />
      </div>

      <AuthModal
        show={showModal}
        onHide={() => setShowModal(false)}
        onSuccess={handleSuccess}
      />

      {/* Footer */}
      <div className="position-absolute text-center"
           style={{ bottom: '24px', left: 0, right: 0, zIndex: 1 }}>
        <small className="text-white opacity-75">
          © 2024 WWWAnalys. Все права защищены.
        </small>
      </div>
    </div>
  );
};

export default Login;