import React from 'react';
import { Toast } from 'react-bootstrap';

interface AlertToastProps {
  show: boolean;
  onClose: () => void;
  message: string;
  variant: 'success' | 'danger' | 'warning' | 'info';
}

const AlertToast: React.FC<AlertToastProps> = ({ show, onClose, message, variant }) => {
  return (
    <Toast 
      show={show} 
      onClose={onClose} 
      className="position-fixed bottom-0 end-0 m-3"
      bg={variant}
    >
      <Toast.Header>
        <i className={`bi bi-${variant === 'success' ? 'check-circle' : variant === 'danger' ? 'exclamation-triangle' : variant === 'warning' ? 'exclamation-circle' : 'info-circle'} me-2`}></i>
        <strong className="me-auto">WWWAnalys</strong>
      </Toast.Header>
      <Toast.Body>{message}</Toast.Body>
    </Toast>
  );
};

export default AlertToast;