/** Компонент конструктора шаблонов анализа */
import React from 'react';
import { Modal, Form, Button, Alert, Badge, Card } from 'react-bootstrap';
import type { Indicator, IndicatorLibrary, LibraryIndicatorRef } from '../types';
import IndicatorPreview from './IndicatorPreview';

interface TemplateBuilderProps {
  show: boolean;
  onHide: () => void;
  onSubmit: (e: React.FormEvent) => void;
  name: string;
  description: string;
  isActive: boolean;
  templateType: 'pure' | 'hybrid';
  isEditing: boolean;
  onChangeName: (value: string) => void;
  onChangeDescription: (value: string) => void;
  onChangeActive: (value: boolean) => void;
  onChangeType: (value: 'pure' | 'hybrid') => void;
  _libIndicators: IndicatorLibrary[];
  templateLibIndicators: LibraryIndicatorRef[];
  onOpenSelectLib: () => void;
  onRemoveLib: (id: number) => void;
  onMoveLib: (id: number, direction: 'up' | 'down') => void;
  templateIndicators: Indicator[];
  onOpenCustom: () => void;
  onEditCustom: (indicator: Indicator) => void;
  onRemoveCustom: (id: number) => void;
  onMoveCustom: (id: number, direction: 'up' | 'down') => void;
  getLibIndicator: (id: number) => IndicatorLibrary | undefined;
  _getCategoryLabel: (category: string | null) => string;
}

const TemplateBuilder: React.FC<TemplateBuilderProps> = ({
  show, onHide, onSubmit,
  name, description, isActive, templateType, isEditing,
  onChangeName, onChangeDescription, onChangeActive, onChangeType,
  templateLibIndicators, onOpenSelectLib, onRemoveLib, onMoveLib,
  templateIndicators, onOpenCustom, onEditCustom, onRemoveCustom, onMoveCustom,
  getLibIndicator,
}) => {
  return (
    <Modal show={show} onHide={onHide} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>{isEditing ? 'Редактирование шаблона' : 'Создание шаблона'}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form onSubmit={onSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>Название шаблона</Form.Label>
            <Form.Control type="text" value={name} onChange={(e) => onChangeName(e.target.value)} required />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Описание</Form.Label>
            <Form.Control as="textarea" rows={3} value={description} onChange={(e) => onChangeDescription(e.target.value)} />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Тип шаблона</Form.Label>
            <Form.Select value={templateType} onChange={(e) => onChangeType(e.target.value as 'pure' | 'hybrid')} disabled={isEditing}>
              <option value="hybrid">Гибридный — справочник + пользовательские</option>
              <option value="pure">Чистый — только справочник</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Check type="switch" label="Активен" checked={isActive} onChange={(e) => onChangeActive(e.target.checked)} />
          </Form.Group>

          {/* Library indicators */}
          <div className="mb-3">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <h5 className="mb-0">Из справочника</h5>
              <Button variant="outline-primary" size="sm" onClick={onOpenSelectLib}>Выбрать</Button>
            </div>
            {templateLibIndicators.length === 0 ? (
              <Alert variant="info" className="py-2"><small>Нет показателей из справочника.</small></Alert>
            ) : (
              templateLibIndicators.map((ref, index) => {
                const libInd = getLibIndicator(ref.indicator_id);
                const isFirst = index === 0;
                const isLast = index === templateLibIndicators.length - 1;
                return (
                  <div key={ref.indicator_id} className="d-flex align-items-center gap-2 mb-2">
                    <div className="d-flex flex-column">
                      <button className="btn btn-sm py-0 px-1 border-0 text-muted" disabled={isFirst}
                        onClick={() => onMoveLib(ref.indicator_id, 'up')} title="Вверх">▲</button>
                      <button className="btn btn-sm py-0 px-1 border-0 text-muted" disabled={isLast}
                        onClick={() => onMoveLib(ref.indicator_id, 'down')} title="Вниз">▼</button>
                    </div>
                    <div className="flex-grow-1">
                      {libInd && <IndicatorPreview indicator={libInd} minValue={ref.min_value} maxValue={ref.max_value} sortOrder={index} />}
                    </div>
                    <Button variant="outline-danger" size="sm" onClick={() => onRemoveLib(ref.indicator_id)}>✕</Button>
                  </div>
                );
              })
            )}
          </div>

          {/* Custom indicators */}
          {templateType === 'hybrid' && (
            <div className="mb-3">
              <div className="d-flex justify-content-between align-items-center mb-2">
                <h5 className="mb-0">Пользовательские</h5>
                <Button variant="outline-secondary" size="sm" onClick={onOpenCustom}>Добавить</Button>
              </div>
              {templateIndicators.length === 0 ? (
                <Alert variant="info" className="py-2"><small>Нет пользовательских показателей.</small></Alert>
              ) : (
                templateIndicators.map((indicator, index) => {
                  const isFirst = index === 0;
                  const isLast = index === templateIndicators.length - 1;
                  return (
                    <Card key={indicator.id} className="mb-2">
                      <Card.Body className="py-2">
                        <div className="d-flex justify-content-between align-items-center">
                          <div className="d-flex align-items-center gap-2">
                            <div className="d-flex flex-column">
                              <button className="btn btn-sm py-0 px-1 border-0 text-muted" disabled={isFirst}
                                onClick={() => onMoveCustom(indicator.id, 'up')} title="Вверх">▲</button>
                              <button className="btn btn-sm py-0 px-1 border-0 text-muted" disabled={isLast}
                                onClick={() => onMoveCustom(indicator.id, 'down')} title="Вниз">▼</button>
                            </div>
                            <div>
                              <strong>{indicator.name}</strong>, {indicator.unit}
                              {indicator.min_value !== null && indicator.max_value !== null && (
                                <small className="text-muted ms-2">Норма: {indicator.min_value} - {indicator.max_value}</small>
                              )}
                              <Badge bg="secondary" className="ms-2">{indicator.data_type}</Badge>
                            </div>
                          </div>
                          <div>
                            <Button variant="outline-primary" size="sm" className="me-1" onClick={() => onEditCustom(indicator)}>Ред.</Button>
                            <Button variant="outline-danger" size="sm" onClick={() => onRemoveCustom(indicator.id)}>Удал.</Button>
                          </div>
                        </div>
                      </Card.Body>
                    </Card>
                  );
                })
              )}
            </div>
          )}
          {templateType === 'pure' && (
            <Alert variant="info">Чистый шаблон — только показатели из справочника.</Alert>
          )}
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>Отмена</Button>
        <Button variant="primary" onClick={onSubmit}>
          {isEditing ? 'Сохранить изменения' : 'Создать шаблон'}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default TemplateBuilder;