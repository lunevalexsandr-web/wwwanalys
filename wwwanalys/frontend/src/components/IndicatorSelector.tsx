/** Компонент выбора показателей из справочника с поиском/фильтрацией */
import React from 'react';
import { Modal, Form, Table, Badge, Alert, Button, Spinner, Row, Col } from 'react-bootstrap';
import type { IndicatorLibrary } from '../types';

interface IndicatorSelectorProps {
  show: boolean;
  onHide: () => void;
  libIndicators: IndicatorLibrary[];
  selectedIds: number[];
  onToggle: (id: number) => void;
  norms: Record<number, { min: number | null; max: number | null }>;
  onNormChange: (id: number, field: 'min' | 'max', value: string) => void;
  onConfirm: () => void;
  // Optional search/filter state
  search?: string;
  filterCategory?: string;
  filterType?: string;
  onSearchChange?: (value: string) => void;
  onFilterCategoryChange?: (value: string) => void;
  onFilterTypeChange?: (value: string) => void;
  isSearching?: boolean;
}

const IndicatorSelector: React.FC<IndicatorSelectorProps> = ({
  show, onHide, libIndicators, selectedIds, onToggle,
  norms, onNormChange, onConfirm,
  search = '', filterCategory = '', filterType = '',
  onSearchChange, onFilterCategoryChange, onFilterTypeChange,
  isSearching = false,
}) => {
  return (
    <Modal show={show} onHide={onHide} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Выбор показателей из справочника</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p className="text-muted mb-3">
          Выберите показатели для добавления в шаблон и задайте для них нормы (min/max).
        </p>

        {/* Search & filters */}
        {(onSearchChange || onFilterCategoryChange || onFilterTypeChange) && (
          <Row className="g-2 mb-3">
            <Col md={5}>
              <div className="input-group input-group-sm">
                <span className="input-group-text"><i className="bi bi-search"></i></span>
                <Form.Control
                  type="text"
                  placeholder="Поиск..."
                  value={search}
                  onChange={(e) => onSearchChange?.(e.target.value)}
                />
              </div>
            </Col>
            <Col md={3}>
              <Form.Select size="sm" value={filterCategory} onChange={(e) => onFilterCategoryChange?.(e.target.value)}>
                <option value="">Все категории</option>
                <option value="quality">Качество</option>
                <option value="safety">Безопасность</option>
                <option value="performance">Производительность</option>
                <option value="chemical">Химический состав</option>
                <option value="physical">Физические свойства</option>
                <option value="microbiology">Микробиология</option>
              </Form.Select>
            </Col>
            <Col md={2}>
              <Form.Select size="sm" value={filterType} onChange={(e) => onFilterTypeChange?.(e.target.value)}>
                <option value="">Все типы</option>
                <option value="number">Число</option>
                <option value="text">Текст</option>
                <option value="select">Выбор</option>
              </Form.Select>
            </Col>
            <Col md={2} className="d-flex align-items-center">
              {isSearching && <Spinner animation="border" size="sm" className="me-2" />}
              <small className="text-muted">{libIndicators.length}</small>
            </Col>
          </Row>
        )}

        {libIndicators.length === 0 ? (
          <Alert variant="warning">
            <i className="bi bi-exclamation-triangle-fill me-2"></i>
            Справочник показателей пуст.
          </Alert>
        ) : (
          <div className="table-responsive" style={{ maxHeight: '400px', overflowY: 'auto' }}>
            <Table striped hover size="sm">
              <thead>
                <tr>
                  <th style={{ width: '40px' }}>#</th>
                  <th>Показатель</th>
                  <th style={{ width: '100px' }}>Тип</th>
                  <th style={{ width: '100px' }}>Норма min</th>
                  <th style={{ width: '100px' }}>Норма max</th>
                </tr>
              </thead>
              <tbody>
                {libIndicators.map((ind) => (
                  <tr key={ind.id} className={selectedIds.includes(ind.id) ? 'table-primary' : ''}>
                    <td>
                      <Form.Check
                        type="checkbox"
                        checked={selectedIds.includes(ind.id)}
                        onChange={() => onToggle(ind.id)}
                      />
                    </td>
                    <td>
                      <strong>{ind.name}</strong>, {ind.unit}
                      {ind.description && <small className="text-muted d-block">{ind.description}</small>}
                      {ind.data_type === 'select' && ind.options && (
                        <small className="text-muted d-block">Варианты: {ind.options.join(', ')}</small>
                      )}
                    </td>
                    <td>
                      <Badge bg="secondary">
                        {ind.data_type === 'number' ? 'Число' : ind.data_type === 'text' ? 'Текст' : 'Выбор'}
                      </Badge>
                    </td>
                    <td>
                      <Form.Control
                        type="number" size="sm"
                        value={norms[ind.id]?.min ?? ''}
                        onChange={(e) => onNormChange(ind.id, 'min', e.target.value)}
                        disabled={!selectedIds.includes(ind.id)}
                        placeholder="min"
                      />
                    </td>
                    <td>
                      <Form.Control
                        type="number" size="sm"
                        value={norms[ind.id]?.max ?? ''}
                        onChange={(e) => onNormChange(ind.id, 'max', e.target.value)}
                        disabled={!selectedIds.includes(ind.id)}
                        placeholder="max"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </div>
        )}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>Отмена</Button>
        <Button variant="primary" onClick={onConfirm} disabled={selectedIds.length === 0}>
          <i className="bi bi-check-circle me-1"></i>
          Добавить выбранные ({selectedIds.length})
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default IndicatorSelector;