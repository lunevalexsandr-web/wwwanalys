import React from 'react';
import { Button } from 'react-bootstrap';

interface ActionButtonsProps {
  onSave?: () => void;
  onCancel?: () => void;
  onDelete?: () => void;
  onEdit?: () => void;
  onToggle?: () => void;
  saveText?: string;
  cancelText?: string;
  deleteText?: string;
  editText?: string;
  toggleText?: string;
  toggleActive?: boolean;
  isLoading?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

const ActionButtons: React.FC<ActionButtonsProps> = ({
  onSave,
  onCancel,
  onDelete,
  onEdit,
  onToggle,
  saveText = 'Сохранить',
  cancelText = 'Отмена',
  deleteText = 'Удалить',
  editText = 'Редактировать',
  toggleText,
  toggleActive = false,
  isLoading = false,
  size = 'md',
  className = ''
}) => {
  const buttonSize = size === 'sm' ? 'sm' : undefined;

  return (
    <div className={`d-flex gap-2 ${className}`}>
      {onSave && (
        <Button
          variant="primary"
          size={buttonSize}
          onClick={onSave}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              Сохранение...
            </>
          ) : (
            saveText
          )}
        </Button>
      )}
      
      {onCancel && (
        <Button
          variant="secondary"
          size={buttonSize}
          onClick={onCancel}
        >
          {cancelText}
        </Button>
      )}
      
      {onEdit && (
        <Button
          variant="outline-primary"
          size={buttonSize}
          onClick={onEdit}
        >
          <i className="bi bi-pencil me-1"></i>
          {editText}
        </Button>
      )}
      
      {onToggle && (
        <Button
          variant={toggleActive ? 'warning' : 'success'}
          size={buttonSize}
          onClick={onToggle}
        >
          {toggleText || (toggleActive ? 'Деактивировать' : 'Активировать')}
        </Button>
      )}
      
      {onDelete && (
        <Button
          variant="outline-danger"
          size={buttonSize}
          onClick={onDelete}
        >
          <i className="bi bi-trash me-1"></i>
          {deleteText}
        </Button>
      )}
    </div>
  );
};

export default ActionButtons;