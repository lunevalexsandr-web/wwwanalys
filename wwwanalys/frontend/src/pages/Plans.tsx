/** Plans page - analysis planning for lab technicians */
import React, { useState, useEffect } from 'react';
import { 
  Card, CardHeader, CardTitle, CardBody, Tabs, Tab, Form, Button, 
  Alert, Badge, Table, Spinner, Modal
} from 'react-bootstrap';
import AppHeader from '../components/AppHeader';
import AppToast from '../components/AppToast';
import { useToast } from '../hooks/useToast';
import api from '../api/axios';
import type { AnalysisPlan, AnalysisType, PlanItem } from '../types';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Plans: React.FC = () => {
  const [activeTab, setActiveTab] = useState('today');
  const [plans, setPlans] = useState<AnalysisPlan[]>([]);
  const [templates, setTemplates] = useState<AnalysisType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { toast, showToast, hideToast } = useToast();
  
  const today = new Date().toISOString().split('T')[0];
  const [selectedDate, setSelectedDate] = useState(today);
  
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [planName, setPlanName] = useState('');
  const [planDescription, setPlanDescription] = useState('');
  const [planDate, setPlanDate] = useState(today);
  const [selectedPlanItems, setSelectedPlanItems] = useState<number[]>([]);
  const [planItemBatchNumbers, setPlanItemBatchNumbers] = useState<Record<number, string>>({});
  
  const [showViewModal, setShowViewModal] = useState(false);
  const [viewPlan, setViewPlan] = useState<AnalysisPlan | null>(null);

  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.is_admin ?? false;

  useEffect(() => {
    fetchTemplates();
    fetchPlansForDate(today);
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await api.get('/api/templates/active');
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
      showToast('Ошибка при загрузке шаблонов', 'danger');
    }
  };

  const fetchPlansForDate = async (date: string) => {
    setIsLoading(true);
    try {
      const response = await api.get(`/api/plans/by-date?plan_date=${date}`);
      setPlans(response.data);
    } catch (error) {
      console.error('Error fetching plans:', error);
      showToast('Ошибка при загрузке планов', 'danger');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDateChange = (date: string) => {
    setSelectedDate(date);
    fetchPlansForDate(date);
  };

  // Обновление номера партии в состоянии plans (иммутабельно)
  const updatePlanItemBatchNumber = (planId: number, itemId: number, batchNumber: string) => {
    setPlans(prevPlans => prevPlans.map(p => {
      if (p.id !== planId) return p;
      return {
        ...p,
        plan_items: p.plan_items?.map((i: PlanItem) =>
          i.id === itemId ? { ...i, batch_number: batchNumber } : i
        ),
      };
    }));
  };

  // Переход к созданию отчета из элемента плана
  const handleCreateReportFromPlanItem = (item: PlanItem) => {
    const batchNumber = item.batch_number || '';
    
    if (item?.template) {
      // Передаём данные напрямую через navigate state
      navigate('/dashboard', { 
        state: { 
          activeTab: 'new-report', 
          autoCreate: true,
          planData: {
            template_id: item.template_id,
            batch_number: batchNumber,
            template: item.template,
            plan_item_id: item.id,
          }
        } 
      });
    } else {
      // Fallback: загружаем шаблон и используем localStorage
      handleCreateReportFromPlanItemAsync(item);
    }
  };

  // Асинхронная версия (fallback если шаблон не загружен)
  const handleCreateReportFromPlanItemAsync = async (item: PlanItem) => {
    try {
      const templateResponse = await api.get(`/api/templates/${item.template_id}`);
      const template = templateResponse.data;
      
      localStorage.setItem('planItemToReport', JSON.stringify({
        template_id: item.template_id,
        batch_number: item.batch_number || '',
        template: template,
        plan_item_id: item.id,
      }));
      navigate('/dashboard', { state: { activeTab: 'new-report', autoCreate: true } });
    } catch (error) {
      console.error('Error creating report from plan item:', error);
      showToast('Ошибка при переходе к созданию отчета', 'danger');
    }
  };

  const handleEditReportFromPlanItem = async (item: PlanItem) => {
    if (!item.completed_report_id) return;
    
    try {
      const reportResponse = await api.get(`/api/reports/${item.completed_report_id}`);
      const report = reportResponse.data;
      
      const templateResponse = await api.get(`/api/templates/${item.template_id}`);
      const template = templateResponse.data;
      
      // Передаём данные напрямую через navigate state
      navigate('/dashboard', { 
        state: { 
          activeTab: 'new-report', 
          autoCreate: true,
          planData: {
            template_id: item.template_id,
            batch_number: report.batch_number || item.batch_number || '',
            template: template,
            report_id: item.completed_report_id,
            report: report,
            is_editing: true,
            plan_item_id: item.id,
          }
        } 
      });
    } catch (error) {
      console.error('Error editing report from plan item:', error);
      showToast('Ошибка при загрузке отчета для редактирования', 'danger');
    }
  };

  // Переключение статуса выполнения элемента плана
  const handleTogglePlanItem = async (itemId: number, completed: boolean) => {
    try {
      await api.patch(`/api/plans/items/${itemId}`, { is_completed: !completed });
      fetchPlansForDate(selectedDate);
    } catch (error) {
      console.error('Error updating plan item:', error);
      showToast('Ошибка при обновлении элемента плана', 'danger');
    }
  };

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isAdmin) {
      showToast('У вас нет прав на создание плана. Обратитесь к администратору.', 'warning');
      return;
    }
    
    if (!planName.trim()) {
      showToast('Введите название плана', 'warning');
      return;
    }
    
    if (selectedPlanItems.length === 0) {
      showToast('Выберите хотя бы один шаблон для плана', 'warning');
      return;
    }

    try {
      const planData = {
        name: planName,
        description: planDescription,
        plan_date: planDate,
        plan_items: selectedPlanItems.map((templateId, index) => ({
          template_id: templateId,
          batch_number: planItemBatchNumbers[templateId] || '',
          sort_order: index,
        })),
      };

      await api.post('/api/plans/', planData);
      showToast('План успешно создан!', 'success');
      setShowCreateModal(false);
      resetPlanForm();
      fetchPlansForDate(planDate);
    } catch (error: any) {
      console.error('Error creating plan:', error);
      showToast(error.response?.data?.detail || 'Ошибка при создании плана', 'danger');
    }
  };

  const resetPlanForm = () => {
    setPlanName('');
    setPlanDescription('');
    setPlanDate(today);
    setSelectedPlanItems([]);
    setPlanItemBatchNumbers({});
  };

  const handleToggleTemplateSelection = (templateId: number) => {
    setSelectedPlanItems(prev => {
      if (prev.includes(templateId)) {
        const newBatchNumbers = { ...planItemBatchNumbers };
        delete newBatchNumbers[templateId];
        setPlanItemBatchNumbers(newBatchNumbers);
        return prev.filter(id => id !== templateId);
      }
      return [...prev, templateId];
    });
  };

  const handleBatchNumberChange = (templateId: number, value: string) => {
    setPlanItemBatchNumbers(prev => ({ ...prev, [templateId]: value }));
  };

  const handleViewPlan = (plan: AnalysisPlan) => {
    setViewPlan(plan);
    setShowViewModal(true);
  };

  const handleDeletePlan = async (planId: number) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот план?')) {
      return;
    }

    try {
      await api.delete(`/api/plans/${planId}`);
      showToast('План успешно удален', 'success');
      fetchPlansForDate(selectedDate);
    } catch (error: any) {
      console.error('Error deleting plan:', error);
      if (error.response?.status === 403) {
        showToast('У вас нет прав на удаление плана. Обратитесь к администратору.', 'warning');
      } else {
        showToast('Ошибка при удалении плана', 'danger');
      }
    }
  };

  const getProgress = (plan: AnalysisPlan): { completed: number; total: number } => {
    const total = plan.plan_items?.length || 0;
    const completed = plan.plan_items?.filter((item: PlanItem) => item.is_completed)?.length || 0;
    return { completed, total };
  };

  const getTemplateName = (templateId: number): string => {
    const template = templates.find(t => t.id === templateId);
    return template ? template.name : `Шаблон #${templateId}`;
  };

  return (
    <div className="min-vh-100 bg-light">
      <AppHeader showAdminLink />

      <main className="app-main">
        <div className="container-fluid">
          <div className="page-wrapper">
            <div className="mb-4 d-flex justify-content-between align-items-start">
              <div>
                <h2 className="h3 mb-1">Планирование анализов</h2>
                <p className="text-muted mb-0">Создавайте планы на день для лаборантов, отмечайте выполненные задачи</p>
              </div>
              <div className="d-flex gap-2 align-items-center">
                <Form.Control
                  type="date"
                  value={selectedDate}
                  onChange={(e) => handleDateChange(e.target.value)}
                  style={{ width: '200px' }}
                />
                {isAdmin && (
                  <Button variant="primary" onClick={() => { resetPlanForm(); setPlanDate(selectedDate); setShowCreateModal(true); }}>
                    <i className="bi bi-plus-circle-fill me-1"></i>
                    Новый план
                  </Button>
                )}
              </div>
            </div>

            <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k || 'today')} className="mb-4">
              <Tab eventKey="today" title={
                <span><i className="bi bi-calendar-day me-1"></i>Планы на {new Date(selectedDate).toLocaleDateString('ru-RU')}</span>
              }>
                {isLoading ? (
                  <div className="text-center py-4">
                    <Spinner animation="border" />
                    <p className="text-muted mt-2">Загрузка...</p>
                  </div>
                ) : plans.length === 0 ? (
                  <div className="text-center py-4">
                    <i className="bi bi-calendar-x display-1 text-muted"></i>
                    <p className="text-muted mt-2">Нет планов на выбранную дату</p>
                    {isAdmin && (
                      <Button variant="primary" onClick={() => { resetPlanForm(); setPlanDate(selectedDate); setShowCreateModal(true); }}>
                        Создать план на этот день
                      </Button>
                    )}
                  </div>
                ) : (
                  <div className="row g-3">
                    {plans.map((plan) => {
                      const progress = getProgress(plan);
                      const isComplete = progress.completed === progress.total;
                      
                      return (
                        <div key={plan.id} className="col-12">
                          <Card>
                            <CardHeader className="d-flex justify-content-between align-items-center">
                              <CardTitle className="h5 mb-0">
                                <i className="bi bi-clipboard2-fill me-2 text-primary"></i>
                                {plan.name}
                              </CardTitle>
                              <Badge bg={isComplete ? 'success' : 'warning'}>
                                {isComplete ? 'Завершен' : `Выполнено: ${progress.completed}/${progress.total}`}
                              </Badge>
                            </CardHeader>
                            <CardBody>
                              {plan.description && (
                                <p className="text-muted mb-3">{plan.description}</p>
                              )}
                              
                              <div className="table-responsive">
                                <Table striped size="sm">
                                  <thead>
                                    <tr>
                                      <th>Статус</th>
                                      <th>Шаблон</th>
                                      <th>Номер партии</th>
                                      <th>Отчет</th>
                                      <th>Действия</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {(plan.plan_items || []).map((item: PlanItem) => (
                                      <tr key={item.id}>
                                        <td>
                                          <Form.Check
                                            type="checkbox"
                                            checked={item.is_completed}
                                            onChange={() => handleTogglePlanItem(item.id, item.is_completed)}
                                          />
                                        </td>
                                        <td>
                                          <strong>{item.template?.name || getTemplateName(item.template_id)}</strong>
                                          <small className="text-muted d-block">
                                            {item.template?.template_indicators?.length || 0} показателей
                                          </small>
                                        </td>
                                        <td>
                                          <Form.Control
                                            type="text"
                                            size="sm"
                                            value={item.batch_number || ''}
                                            onChange={(e) => updatePlanItemBatchNumber(plan.id, item.id, e.target.value)}
                                            placeholder="Введите номер партии"
                                            disabled={item.is_completed}
                                          />
                                        </td>
                                        <td>
                                          {item.completed_report_id ? (
                                            <Badge bg="info">
                                              <i className="bi bi-file-earmark-text me-1"></i>
                                              Отчет #{item.completed_report_id}
                                            </Badge>
                                          ) : (
                                            <span className="text-muted">—</span>
                                          )}
                                        </td>
                                        <td>
                                          {!item.is_completed ? (
                                            <Button 
                                                variant="primary" 
                                                size="sm"
                                                onClick={() => handleCreateReportFromPlanItem(item)}
                                              >
                                                <i className="bi bi-plus-circle me-1"></i>
                                                Создать отчет
                                              </Button>
                                          ) : (
                                            item.completed_report_id && (
                                              <Button 
                                                  variant="outline-primary" 
                                                  size="sm"
                                                  onClick={() => handleEditReportFromPlanItem(item)}
                                                >
                                                  <i className="bi bi-pencil me-1"></i>
                                                  Редактировать
                                                </Button>
                                            )
                                          )}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </Table>
                              </div>
                              
                              <div className="d-flex gap-2 justify-content-end mt-3">
                                <Button variant="outline-primary" size="sm" onClick={() => handleViewPlan(plan)}>
                                  <i className="bi bi-eye me-1"></i>
                                  Подробно
                                </Button>
                                {isAdmin && (
                                  <Button variant="outline-danger" size="sm" onClick={() => handleDeletePlan(plan.id)}>
                                    <i className="bi bi-trash me-1"></i>
                                    Удалить
                                  </Button>
                                )}
                              </div>
                            </CardBody>
                          </Card>
                        </div>
                      );
                    })}
                  </div>
                )}
              </Tab>
            </Tabs>
          </div>
        </div>
      </main>

      {/* Create Plan Modal */}
      <Modal show={showCreateModal} onHide={() => setShowCreateModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Создание плана анализов</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleCreatePlan}>
            <Form.Group className="mb-3">
              <Form.Label>Название плана</Form.Label>
              <Form.Control
                type="text"
                value={planName}
                onChange={(e) => setPlanName(e.target.value)}
                placeholder="Введите название плана (например: План на смену 1)"
                required
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Описание (необязательно)</Form.Label>
              <Form.Control
                as="textarea"
                rows={2}
                value={planDescription}
                onChange={(e) => setPlanDescription(e.target.value)}
                placeholder="Описание плана"
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Дата выполнения</Form.Label>
              <Form.Control
                type="date"
                value={planDate}
                onChange={(e) => setPlanDate(e.target.value)}
                required
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Шаблоны для анализа</Form.Label>
              {templates.length === 0 ? (
                <Alert variant="warning">Нет доступных шаблонов</Alert>
              ) : (
                <div className="row g-2" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                  {templates.map((template) => (
                    <div key={template.id} className="col-12">
                      <Card className={`cursor-pointer ${selectedPlanItems.includes(template.id) ? 'border-primary' : ''}`}>
                        <CardBody className="py-2">
                          <Form.Check
                            type="checkbox"
                            id={`template-${template.id}`}
                            checked={selectedPlanItems.includes(template.id)}
                            onChange={() => handleToggleTemplateSelection(template.id)}
                            label={
                              <div>
                                <strong>{template.name}</strong>
                                <small className="text-muted d-block">{template.description}</small>
                                 <small className="text-muted">{template.template_indicators?.length || 0} показателей</small>
                              </div>
                            }
                          />
                          {selectedPlanItems.includes(template.id) && (
                            <Form.Control
                              type="text"
                              size="sm"
                              placeholder="Номер партии (по желанию)"
                              value={planItemBatchNumbers[template.id] || ''}
                              onChange={(e) => handleBatchNumberChange(template.id, e.target.value)}
                              className="mt-2"
                            />
                          )}
                        </CardBody>
                      </Card>
                    </div>
                  ))}
                </div>
              )}
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowCreateModal(false)}>
            Отмена
          </Button>
          <Button variant="primary" onClick={handleCreatePlan}>
            Создать план
          </Button>
        </Modal.Footer>
      </Modal>

      {/* View Plan Modal */}
      <Modal show={showViewModal} onHide={() => setShowViewModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            {viewPlan?.name}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {viewPlan?.description && (
            <p className="text-muted">{viewPlan.description}</p>
          )}
          
          <Table striped size="sm">
            <thead>
              <tr>
                <th>Шаблон</th>
                <th>Номер партии</th>
                <th>Показатели</th>
                <th>Статус</th>
                <th>Отчет</th>
              </tr>
            </thead>
            <tbody>
              {(viewPlan?.plan_items || []).map((item: PlanItem) => (
                <tr key={item.id}>
                  <td>{item.template?.name || getTemplateName(item.template_id)}</td>
                  <td>{item.batch_number || '-'}</td>
                  <td>{item.template?.template_indicators?.length || 0}</td>
                  <td>
                    <Badge bg={item.is_completed ? 'success' : 'warning'}>
                      {item.is_completed ? 'Выполнено' : 'В ожидании'}
                    </Badge>
                  </td>
                  <td>
                    {item.completed_report_id ? (
                      <Badge bg="info">
                        Отчет #{item.completed_report_id}
                      </Badge>
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowViewModal(false)}>
            Закрыть
          </Button>
        </Modal.Footer>
      </Modal>

      <AppToast toast={toast} onClose={hideToast} />
    </div>
  );
};

export default Plans;