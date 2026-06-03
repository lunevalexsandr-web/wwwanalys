import React from 'react';
import { Form } from 'react-bootstrap';

interface Indicator {
  id: number;
  name: string;
  unit: string;
  min_value: number | null;
  max_value: number | null;
  type: 'FLOAT' | 'TEXT' | 'SELECT';
  options?: string[];
}

interface IndicatorInputProps {
  indicator: Indicator;
  value: string | number;
  onChange: (value: string) => void;
  isOutOfRange?: boolean;
}

const IndicatorInput: React.FC<IndicatorInputProps> = ({ 
  indicator, 
  value, 
  onChange, 
  isOutOfRange = false 
}) => {
  const renderInput = () => {
    switch (indicator.type) {
      case 'FLOAT':
        return (
          <Form.Control
            type="number"
            value={value}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => onChange(e.target.value)}
            step="0.01"
            placeholder={`Введите значение (${indicator.unit})`}
            className={isOutOfRange ? 'is-invalid' : ''}
            required
          />
        );
      case 'TEXT':
        return (
          <Form.Control
            type="text"
            value={value}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => onChange(e.target.value)}
            placeholder={`Введите значение (${indicator.unit})`}
            required
          />
        );
      case 'SELECT':
        return (
          <Form.Select
            value={value}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => onChange(e.target.value)}
            required
          >
            <option value="">-- Выберите значение --</option>
            {indicator.options?.map((option, index) => (
              <option key={index} value={option}>
                {option}
              </option>
            ))}
          </Form.Select>
        );
      default:
        return null;
    }
  };

  return (
    <div className="mb-3">
      <div className="d-flex justify-content-between align-items-start mb-2">
        <Form.Label className="mb-0">
          {indicator.name}, {indicator.unit}
        </Form.Label>
        {indicator.min_value !== null && indicator.max_value !== null && (
          <small className="text-muted">
            Норма: {indicator.min_value} - {indicator.max_value}
          </small>
        )}
      </div>
      
      {renderInput()}
      
      {isOutOfRange && (
        <div className="invalid-feedback">
          <i className="bi bi-exclamation-circle-fill me-1"></i>
          Значение вне нормы!
        </div>
      )}
    </div>
  );
};

export default IndicatorInput;