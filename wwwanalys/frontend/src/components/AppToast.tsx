/** Application toast notification component */
import React from 'react';
import { Toast } from 'react-bootstrap';
import type { ToastState } from '../types';

interface AppToastProps {
  toast: ToastState;
  onClose: () => void;
}

const AppToast: React.FC<AppToastProps> = ({ toast, onClose }) => {
  const iconMap = {
    success: 'check-circle',
    danger: 'exclamation-triangle',
    warning: 'exclamation-triangle',
    info: 'info-circle'
  };

  return (
    <Toast 
      show={toast.show} 
      onClose={onClose} 
      className="position-fixed bottom-0 end-0 m-3"
      bg={toast.variant}
      delay={5000}
      autohide
    >
      <Toast.Header>
        <i className={`bi bi-${iconMap[toast.variant]} me-2`}></i>
        <strong className="me-auto">WWWAnalys</strong>
      </Toast.Header>
      <Toast.Body className={toast.variant === 'warning' ? 'text-dark' : ''}>
        {toast.message}
      </Toast.Body>
    </Toast>
  );
};

export default AppToast;