/** Компонент предпросмотра показателя из справочника */
import React from 'react';
import { Card, Badge } from 'react-bootstrap';
import type { IndicatorLibrary } from '../types';

interface IndicatorPreviewProps {
  indicator: IndicatorLibrary;
  minValue?: number | null;
  maxValue?: number | null;
  sortOrder?: number;
}

const typeLabels: Record<string, string> = {
  number: 'Число',
  text: 'Текст',
  select: 'Выбор',
};

const categoryLabels: Record<string, string> = {
  quality: 'Качество',
  safety: 'Безопасность',
  performance: 'Производительность',
  chemical: 'Химический состав',
  physical: 'Физические свойства',
  microbiology: 'Микробиология',
};

const IndicatorPreview: React.FC<IndicatorPreviewProps> = ({ indicator, minValue, maxValue, sortOrder }) => {
  return (
    <Card className="mb-2 bg-light">
      <Card.Body className="py-2">
        <div className="d-flex justify-content-between align-items-start">
          <div className="flex-grow-1">
            <div className="d-flex align-items-center gap-2 flex-wrap">
              {sortOrder !== undefined && (
                <span className="badge bg-secondary">{sortOrder + 1}</span>
              )}
              <strong>{indicator.name}</strong>
              <small className="text-muted">{indicator.unit}</small>
              <Badge bg="secondary">{typeLabels[indicator.data_type] || indicator.data_type}</Badge>
              {indicator.category && (
                <Badge bg="info">{categoryLabels[indicator.category] || indicator.category}</Badge>
              )}
              {indicator.is_required && (
                <Badge bg="danger" pill>Обязательный</Badge>
              )}
            </div>
            {indicator.description && (
              <div className="text-muted small mt-1">{indicator.description}</div>
            )}
            {(minValue !== null || maxValue !== null) && (
              <small className="text-muted d-block mt-1">
                <i className="bi bi-arrows-expand me-1"></i>
                Норма: {minValue ?? '?'} — {maxValue ?? '?'}
              </small>
            )}
            {indicator.default_value && (
              <small className="text-muted d-block">
                <i className="bi bi-check-circle me-1"></i>
                По умолчанию: {indicator.default_value}
              </small>
            )}
            {indicator.data_type === 'select' && indicator.options && indicator.options.length > 0 && (
              <small className="text-muted d-block">
                <i className="bi bi-list-ul me-1"></i>
                Варианты: {indicator.options.join(', ')}
              </small>
            )}
          </div>
        </div>
      </Card.Body>
    </Card>
  );
};

export default IndicatorPreview;