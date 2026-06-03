/** Admin page - template and user management */
import React, { useState, useEffect } from 'react';
import { 
  Card, CardHeader, CardTitle, CardBody, Tabs, Tab, Form, Button, 
  Alert, Badge, Table, Spinner, Modal, Row, Col
} from 'react-bootstrap';
import AppHeader from '../components/AppHeader';
import AppToast from '../components/AppToast';
import { useToast } from '../hooks/useToast';
import api from '../api/axios';
import type { AnalysisType, Indicator, User as UserType } from '../types';

const Admin: React.FC = () => {
  const [activeTab, setActiveTab] = useState('templates');
  const [templates, setTemplates] = useState<AnalysisType[]>([]);
  const [users, setUsers] = useState<UserType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { toast, showToast, hideToast } = useToast();

  // Template form state
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<AnalysisType | null>(null);
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');
  const [templateActive, setTemplateActive] = useState(true);
  const [templateIndicators, setTemplateIndicators] = useState<Indicator[]>([]);

  // Indicator form state
  const [showIndicatorModal, setShowIndicatorModal] = useState(false);
  const [editingIndicator, setEditingIndicator] = useState<Indicator | null>(null);
  const [indicatorName, setIndicatorName] = useState('');
  const [indicatorUnit, setIndicatorUnit] = useState('');
  const [indicatorMin, setIndicatorMin] = useState<number | null>(null);
  const [indicatorMax, setIndicatorMax] = useState<number | null>(null);
  const [indicatorType, setIndicatorType] = useState<'number' | 'text' | 'select'>('number');
  const [indicatorOptions, setIndicatorOptions] = useState('');

  useEffect(() => {
    fetchTemplates();
    fetchUsers();
  }, []);

  const fetchTemplates = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/api/templates/');
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
      showToast('Ошибка при загрузке шаблонов', 'danger');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await api.get('/auth/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      showToast('Ошибка при загрузке пользователей', 'danger');
    }
  };

  const handleTemplateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!templateName.trim()) {
      showToast('Название шаблона обязательно', 'warning');
      return;
    }

    try {
      const templateData = {
        name: templateName,
        description: templateDescription,
        is_active: templateActive,
        indicators: templateIndicators.map(ind => ({
          name: ind.name,
          unit: ind.unit,
          min_value: ind.min_value,
          max_value: ind.max_value,
          data_type: ind.data_type,
          options: ind.options
        }))
      };

      if (editingTemplate) {
        await api.put(`/api/templates/${editingTemplate.id}`, templateData);
        showToast('Шаблон успешно обновлен', 'success');
      } else {
        await api.post('/api/templates/', templateData);
        showToast('Шаблон успешно создан', 'success');
      }

      setShowTemplateModal(false);
      resetTemplateForm();
      fetchTemplates();
    } catch (error) {
      console.error('Error saving template:', error);
      showToast('Ошибка при сохранении шаблона', 'danger');
    }
  };

  const handleDeleteTemplate = async (id: number) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот шаблон?')) {
      return;
    }

    try {
      await api.delete(`/api/templates/${id}`);
      showToast('Шаблон успешно удален', 'success');
      fetchTemplates();
    } catch (error) {
      console.error('Error deleting template:', error);
      showToast('Ошибка при удалении шаблона', 'danger');
    }
  };

  const handleToggleTemplate = async (id: number, isActive: boolean) => {
    try {
      await api.put(`/api/templates/${id}`, { is_active: !isActive });
      showToast(`Шаблон ${!isActive ? 'активирован' : 'деактивирован'}`, 'success');
      fetchTemplates();
    } catch (error) {
      console.error('Error toggling template:', error);
      showToast('Ошибка при изменении статуса шаблона', 'danger');
    }
  };

  const handleClearAllTemplates = async () => {
    if (!window.confirm('Вы уверены, что хотите удалить ВСЕ шаблоны? Это действие необратимо.')) {
      return;
    }

    try {
      await api.delete('/api/templates/clear-all');
      showToast('Все шаблоны успешно удалены', 'success');
      fetchTemplates();
    } catch (error) {
      console.error('Error clearing all templates:', error);
      showToast('Ошибка при очистке шаблонов', 'danger');
    }
  };

  const handleEditTemplate = (template: AnalysisType) => {
    setEditingTemplate(template);
    setTemplateName(template.name);
    setTemplateDescription(template.description);
    setTemplateActive(template.is_active);
    setTemplateIndicators(template.indicators);
    setShowTemplateModal(true);
  };

  const resetTemplateForm = () => {
    setEditingTemplate(null);
    setTemplateName('');
    setTemplateDescription('');
    setTemplateActive(true);
    setTemplateIndicators([]);
  };

  const handleIndicatorSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!indicatorName.trim() || !indicatorUnit.trim()) {
      showToast('Название и единица измерения обязательны', 'warning');
      return;
    }

    const newIndicator: Indicator = {
      id: editingIndicator?.id || Date.now(),
      name: indicatorName,
      unit: indicatorUnit,
      min_value: indicatorMin,
      max_value: indicatorMax,
      data_type: indicatorType,
      options: indicatorType === 'select' ? indicatorOptions.split(',').map(opt => opt.trim()).filter(opt => opt) : undefined
    };

    if (editingIndicator) {
      setTemplateIndicators(prev => prev.map(ind => ind.id === editingIndicator.id ? newIndicator : ind));
    } else {
      setTemplateIndicators(prev => [...prev, newIndicator]);
    }

    setShowIndicatorModal(false);
    resetIndicatorForm();
  };

  const handleDeleteIndicator = (id: number) => {
    setTemplateIndicators(prev => prev.filter(ind => ind.id !== id));
  };

  const handleEditIndicator = (indicator: Indicator) => {
    setEditingIndicator(indicator);
    setIndicatorName(indicator.name);
    setIndicatorUnit(indicator.unit);
    setIndicatorMin(indicator.min_value);
    setIndicatorMax(indicator.max_value);
    setIndicatorType(indicator.data_type);
    setIndicatorOptions(indicator.options?.join(', ') || '');
    setShowIndicatorModal(true);
  };

  const resetIndicatorForm = () => {
    setEditingIndicator(null);
    setIndicatorName('');
    setIndicatorUnit('');
    setIndicatorMin(null);
    setIndicatorMax(null);
    setIndicatorType('number');
    setIndicatorOptions('');
  };

  const handleToggleUser = async (id: number, isActive: boolean) => {
    try {
      await api.put(`/auth/users/${id}`, { is_active: !isActive });
      showToast(`Пользователь ${!isActive ? 'активирован' : 'деактивирован'}`, 'success');
      fetchUsers();
    } catch (error) {
      console.error('Error toggling user:', error);
      showToast('Ошибка при изменении статуса пользователя', 'danger');
    }
  };

  const handleDeleteUser = async (id: number) => {
    if (!window.confirm('Вы уверены, что хотите удалить этого пользователя?')) {
      return;
    }

    try {
      await api.delete(`/auth/users/${id}`);
      showToast('Пользователь успешно удален', 'success');
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      showToast('Ошибка при удалении пользователя', 'danger');
    }
  };

  return (
    <div className="min-vh-100 bg-light">
      <AppHeader showDashboardLink />

      <main className="app-main">
        <div className="container-fluid">
          <div className="page-wrapper">
            <div className="mb-4">
              <h2 className="h3 mb-1">Администрирование</h2>
              <p className="text-muted mb-0">Управление шаблонами анализа и пользователями</p>
            </div>

            <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k || 'templates')} className="mb-4">
              {/* Templates Tab */}
              <Tab eventKey="templates" title={
                <span><i className="bi bi-list-ul me-1"></i>Шаблоны анализа</span>
              }>
                <Card>
                    <CardHeader className="d-flex justify-content-between align-items-center">
                      <CardTitle className="h5 mb-0">
                        <i className="bi bi-file-earmark-text me-2 text-primary"></i>
                        Управление шаблонами анализа
                      </CardTitle>
                      <div>
                        {templates.length > 0 && (
                          <Button 
                            variant="outline-danger" 
                            size="sm" 
                            className="me-2"
                            onClick={handleClearAllTemplates}
                          >
                            <i className="bi bi-trash me-1"></i>
                            Очистить все
                          </Button>
                        )}
                        <Button variant="primary" onClick={() => setShowTemplateModal(true)}>
                          <i className="bi bi-plus-circle me-1"></i>
                          Создать шаблон
                        </Button>
                      </div>
                    </CardHeader>
                  <CardBody>
                    {isLoading ? (
                      <div className="text-center py-4">
                        <Spinner animation="border" />
                        <p className="text-muted mt-2">Загрузка...</p>
                      </div>
                    ) : templates.length === 0 ? (
                      <div className="text-center py-4">
                        <i className="bi bi-inbox display-1 text-muted"></i>
                        <p className="text-muted mt-2">Нет шаблонов анализа</p>
                      </div>
                    ) : (
                      <div className="table-responsive">
                        <Table striped hover>
                          <thead>
                            <tr>
                              <th>Название</th>
                              <th>Описание</th>
                              <th>Показатели</th>
                              <th>Статус</th>
                              <th className="text-end">Действия</th>
                            </tr>
                          </thead>
                          <tbody>
                            {templates.map((template) => (
                              <tr key={template.id}>
                                <td><strong>{template.name}</strong></td>
                                <td>{template.description || '-'}</td>
                                <td>{template.indicators.length}</td>
                                <td>
                                  <Badge bg={template.is_active ? 'success' : 'danger'}>
                                    {template.is_active ? 'Активен' : 'Неактивен'}
                                  </Badge>
                                </td>
                                <td className="text-end">
                                  <Button 
                                    variant="outline-primary" 
                                    size="sm" 
                                    className="me-1"
                                    onClick={() => handleEditTemplate(template)}
                                  >
                                    <i className="bi bi-pencil me-1"></i>
                                    Редактировать
                                  </Button>
                                  <Button 
                                    variant={template.is_active ? 'warning' : 'success'} 
                                    size="sm"
                                    onClick={() => handleToggleTemplate(template.id, template.is_active)}
                                  >
                                    {template.is_active ? 'Деактивировать' : 'Активировать'}
                                  </Button>
                                  <Button 
                                    variant="outline-danger" 
                                    size="sm" 
                                    className="ms-1"
                                    onClick={() => handleDeleteTemplate(template.id)}
                                  >
                                    <i className="bi bi-trash me-1"></i>
                                    Удалить
                                  </Button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </Table>
                      </div>
                    )}
                  </CardBody>
                </Card>
              </Tab>

              {/* Users Tab */}
              <Tab eventKey="users" title={
                <span><i className="bi bi-people-fill me-1"></i>Пользователи</span>
              }>
                <Card>
                  <CardHeader>
                    <CardTitle className="h5 mb-0">
                      <i className="bi bi-person-lines-fill me-2 text-primary"></i>
                      Управление пользователями
                    </CardTitle>
                  </CardHeader>
                  <CardBody>
                    {users.length === 0 ? (
                      <div className="text-center py-4">
                        <i className="bi bi-inbox display-1 text-muted"></i>
                        <p className="text-muted mt-2">Нет пользователей</p>
                      </div>
                    ) : (
                      <div className="table-responsive">
                        <Table striped hover>
                          <thead>
                            <tr>
                              <th>Email</th>
                              <th>Роль</th>
                              <th>Статус</th>
                              <th className="text-end">Действия</th>
                            </tr>
                          </thead>
                          <tbody>
                            {users.map((user) => (
                              <tr key={user.id}>
                                <td><strong>{user.email}</strong></td>
                                <td>
                                  <Badge bg={user.is_admin ? 'primary' : 'secondary'}>
                                    {user.is_admin ? 'ADMIN' : 'USER'}
                                  </Badge>
                                </td>
                                <td>
                                  <Badge bg={user.is_active ? 'success' : 'danger'}>
                                    {user.is_active ? 'Активен' : 'Неактивен'}
                                  </Badge>
                                </td>
                                <td className="text-end">
                                  <Button 
                                    variant={user.is_active ? 'warning' : 'success'} 
                                    size="sm"
                                    onClick={() => handleToggleUser(user.id, user.is_active)}
                                  >
                                    {user.is_active ? 'Деактивировать' : 'Активировать'}
                                  </Button>
                                  <Button 
                                    variant="outline-danger" 
                                    size="sm" 
                                    className="ms-1"
                                    onClick={() => handleDeleteUser(user.id)}
                                  >
                                    <i className="bi bi-trash me-1"></i>
                                    Удалить
                                  </Button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </Table>
                      </div>
                    )}
                  </CardBody>
                </Card>
              </Tab>
            </Tabs>
          </div>
        </div>
      </main>

      {/* Template Modal */}
      <Modal show={showTemplateModal} onHide={() => setShowTemplateModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            {editingTemplate ? 'Редактирование шаблона' : 'Создание шаблона'}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleTemplateSubmit}>
            <Form.Group className="mb-3">
              <Form.Label>Название шаблона</Form.Label>
              <Form.Control
                type="text"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                required
              />
            </Form.Group>
            
            <Form.Group className="mb-3">
              <Form.Label>Описание</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                value={templateDescription}
                onChange={(e) => setTemplateDescription(e.target.value)}
              />
            </Form.Group>
            
            <Form.Group className="mb-3">
              <Form.Check
                type="switch"
                label="Активен"
                checked={templateActive}
                onChange={(e) => setTemplateActive(e.target.checked)}
              />
            </Form.Group>

            <div className="mb-3">
              <div className="d-flex justify-content-between align-items-center mb-2">
                <h5>Показатели</h5>
                <Button variant="outline-primary" size="sm" onClick={() => setShowIndicatorModal(true)}>
                  <i className="bi bi-plus-circle me-1"></i>
                  Добавить показатель
                </Button>
              </div>
              
              {templateIndicators.length === 0 ? (
                <Alert variant="info">
                  <i className="bi bi-info-circle-fill me-2"></i>
                  Нет показателей. Добавьте хотя бы один показатель для шаблона.
                </Alert>
              ) : (
                <div>
                  {templateIndicators.map((indicator) => (
                    <Card key={indicator.id} className="mb-2">
                      <CardBody>
                        <div className="d-flex justify-content-between align-items-start">
                          <div>
                            <strong>{indicator.name}</strong>, {indicator.unit}
                            {indicator.min_value !== null && indicator.max_value !== null && (
                              <small className="text-muted ms-2">
                                Норма: {indicator.min_value} - {indicator.max_value}
                              </small>
                            )}
                            <Badge bg="secondary" className="ms-2">{indicator.data_type}</Badge>
                          </div>
                          <div>
                            <Button 
                              variant="outline-primary" 
                              size="sm" 
                              className="me-1"
                              onClick={() => handleEditIndicator(indicator)}
                            >
                              <i className="bi bi-pencil"></i>
                            </Button>
                            <Button 
                              variant="outline-danger" 
                              size="sm"
                              onClick={() => handleDeleteIndicator(indicator.id)}
                            >
                              <i className="bi bi-trash"></i>
                            </Button>
                          </div>
                        </div>
                      </CardBody>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowTemplateModal(false)}>
            Отмена
          </Button>
          <Button variant="primary" onClick={handleTemplateSubmit}>
            {editingTemplate ? 'Сохранить изменения' : 'Создать шаблон'}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Indicator Modal */}
      <Modal show={showIndicatorModal} onHide={() => setShowIndicatorModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>
            {editingIndicator ? 'Редактирование показателя' : 'Добавление показателя'}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleIndicatorSubmit}>
            <Form.Group className="mb-3">
              <Form.Label>Название показателя</Form.Label>
              <Form.Control
                type="text"
                value={indicatorName}
                onChange={(e) => setIndicatorName(e.target.value)}
                required
              />
            </Form.Group>
            
            <Form.Group className="mb-3">
              <Form.Label>Единица измерения</Form.Label>
              <Form.Control
                type="text"
                value={indicatorUnit}
                onChange={(e) => setIndicatorUnit(e.target.value)}
                required
              />
            </Form.Group>
            
            <Form.Group className="mb-3">
              <Form.Label>Тип</Form.Label>
              <Form.Select
                value={indicatorType}
                onChange={(e) => setIndicatorType(e.target.value as 'number' | 'text' | 'select')}
              >
                <option value="number">Число с плавающей точкой</option>
                <option value="text">Текст</option>
                <option value="select">Выбор из списка</option>
              </Form.Select>
            </Form.Group>
            
            {indicatorType === 'number' && (
              <Row>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label>Минимальное значение</Form.Label>
                    <Form.Control
                      type="number"
                      value={indicatorMin || ''}
                      onChange={(e) => setIndicatorMin(e.target.value ? parseFloat(e.target.value) : null)}
                    />
                  </Form.Group>
                </Col>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label>Максимальное значение</Form.Label>
                    <Form.Control
                      type="number"
                      value={indicatorMax || ''}
                      onChange={(e) => setIndicatorMax(e.target.value ? parseFloat(e.target.value) : null)}
                    />
                  </Form.Group>
                </Col>
              </Row>
            )}
            
            {indicatorType === 'select' && (
              <Form.Group className="mb-3">
                <Form.Label>Варианты выбора (через запятую)</Form.Label>
                <Form.Control
                  type="text"
                  value={indicatorOptions}
                  onChange={(e) => setIndicatorOptions(e.target.value)}
                  placeholder="Вариант 1, Вариант 2, Вариант 3"
                />
              </Form.Group>
            )}
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowIndicatorModal(false)}>
            Отмена
          </Button>
          <Button variant="primary" onClick={handleIndicatorSubmit}>
            {editingIndicator ? 'Сохранить изменения' : 'Добавить показатель'}
          </Button>
        </Modal.Footer>
      </Modal>

      <AppToast toast={toast} onClose={hideToast} />
    </div>
  );
};

export default Admin;