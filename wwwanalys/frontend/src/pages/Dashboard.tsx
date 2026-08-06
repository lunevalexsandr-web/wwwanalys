/** Dashboard page - report creation and history */
import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Card, CardHeader, CardTitle, CardBody, Tabs, Tab, Form, Button, 
  Alert, Badge, Table, Spinner
} from 'react-bootstrap';
import AppHeader from '../components/AppHeader';
import AppToast from '../components/AppToast';
import { useToast } from '../hooks/useToast';
import api from '../api/axios';
import type { AnalysisType, IndicatorValue, Report } from '../types';

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('new-report');
  const [templates, setTemplates] = useState<AnalysisType[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<AnalysisType | null>(null);
  const [batchNumber, setBatchNumber] = useState('');
  const [variety, setVariety] = useState('');
  const [indicatorValues, setIndicatorValues] = useState<IndicatorValue[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingReportId, setEditingReportId] = useState<number | null>(null);
  const [planItemId, setPlanItemId] = useState<number | null>(null);
  
  // History state
  const [reports, setReports] = useState<Report[]>([]);
  const [filterTemplateId, setFilterTemplateId] = useState<number | null>(null);
  const [filterDateFrom, setFilterDateFrom] = useState('');
  const [filterDateTo, setFilterDateTo] = useState('');
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  
  // View report state
  const [showViewModal, setShowViewModal] = useState(false);
  const [viewReport, setViewReport] = useState<Report | null>(null);
  const [viewReportIndicators, setViewReportIndicators] = useState<any[]>([]);

  // AI-разбор отклонений (эксперт-пивовар) — дополнительный модуль
  const [aiEnabled, setAiEnabled] = useState(false);
  const [aiResult, setAiResult] = useState<any | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  const { toast, showToast, hideToast } = useToast();
  const location = useLocation();
  const navigate = useNavigate();

  // Разовая проверка доступности модуля Агента. Любая ошибка = модуль скрыт,
  // основной интерфейс от этого не зависит.
  useEffect(() => {
    api.get('/api/ai/status')
      .then((r) => setAiEnabled(!!r.data?.enabled))
      .catch(() => setAiEnabled(false));
  }, []);

  /**
   * Получить все показатели шабона (только из справочника).
   */
  const getAllIndicators = (template: AnalysisType): (any)[] => {
    const libInds = (template.template_indicators || []).map(ti => ({
      id: ti.indicator_id,
      name: ti.name,
      unit: ti.unit,
      min_value: ti.min_value,
      max_value: ti.max_value,
      data_type: ti.data_type,
      options: ti.options,
      is_library: true
    }));
    
    return libInds;
  };

  useEffect(() => {
    fetchTemplates();
    fetchReports();
  }, []);

  // Функция для обработки данных из Plans
  const processPlanItemToReport = () => {
    const storedData = localStorage.getItem('planItemToReport');
    if (!storedData) return false;
    
    try {
      const planData = JSON.parse(storedData);
      // Сохраняем plan_item_id заранее
      if (planData.plan_item_id) {
        setPlanItemId(planData.plan_item_id);
      }
      
      // Проверяем, это режим редактирования существующего отчета
      if (planData.is_editing && planData.report && planData.report_id) {
        const template = planData.template as AnalysisType;
        const report = planData.report;
        
        setSelectedTemplate(template);
        setBatchNumber(report.batch_number || planData.batch_number || '');
        setVariety(report.variety || planData.variety || '');
        setIsEditing(true);
        setEditingReportId(planData.report_id);
        
        // Заполняем значения показателей из существующего отчета
        const allIndicators = getAllIndicators(template);
        const values = allIndicators.map(indicator => {
          const existingValue = report.indicator_values?.find(
            (v: any) => v.indicator_id === indicator.id
          );
          return {
            indicator_id: indicator.id,
            value: existingValue?.value?.toString() || existingValue?.text_value || '',
            is_normal: existingValue?.is_normal
          };
        });
        setIndicatorValues(values);
        localStorage.removeItem('planItemToReport');
        return true;
      }
      // Используем переданный шаблон напрямую (он уже содержит template_indicators)
      else if (planData.template && planData.template.template_indicators) {
        const template = planData.template as AnalysisType;
        setSelectedTemplate(template);
        setBatchNumber(planData.batch_number || '');
        setIsEditing(false);
        setEditingReportId(null);
        const allIndicators = getAllIndicators(template);
        const values = allIndicators.map(indicator => ({
          indicator_id: indicator.id,
          value: '',
          is_normal: undefined
        }));
        setIndicatorValues(values);
        localStorage.removeItem('planItemToReport');
        return true;
      } else if (planData.template_id) {
        const template = templates.find(t => t.id === planData.template_id);
        if (template) {
          setSelectedTemplate(template);
          setBatchNumber(planData.batch_number || '');
          setIsEditing(false);
          setEditingReportId(null);
          const allIndicators = getAllIndicators(template);
          const values = allIndicators.map(indicator => ({
            indicator_id: indicator.id,
            value: '',
            is_normal: undefined
          }));
          setIndicatorValues(values);
          localStorage.removeItem('planItemToReport');
          return true;
        }
      }
    } catch (e) {
      console.error('Error parsing planItemToReport:', e);
      localStorage.removeItem('planItemToReport');
    }
    return false;
  };

  // Обработка данных из Plans через navigate state
  const processPlanData = (planData: any) => {
    if (!planData) return false;
    
    try {
      // Сохраняем plan_item_id заранее
      if (planData.plan_item_id) {
        setPlanItemId(planData.plan_item_id);
      }

      // Проверяем, это режим редактирования существующего отчета
      if (planData.is_editing && planData.report && planData.report_id) {
        const template = planData.template as AnalysisType;
        const report = planData.report;
        
        setSelectedTemplate(template);
        setBatchNumber(report.batch_number || planData.batch_number || '');
        setVariety(report.variety || planData.variety || '');
        setIsEditing(true);
        setEditingReportId(planData.report_id);
        
        const allIndicators = getAllIndicators(template);
        const values = allIndicators.map(indicator => {
          const existingValue = report.indicator_values?.find(
            (v: any) => v.indicator_id === indicator.id
          );
          return {
            indicator_id: indicator.id,
            value: existingValue?.value?.toString() || existingValue?.text_value || '',
            is_normal: existingValue?.is_normal
          };
        });
        setIndicatorValues(values);
        return true;
      }
      // Используем переданный шаблон напрямую
      else if (planData.template && planData.template.template_indicators) {
        const template = planData.template as AnalysisType;
        setSelectedTemplate(template);
        setBatchNumber(planData.batch_number || '');
        setIsEditing(false);
        setEditingReportId(null);
        const allIndicators = getAllIndicators(template);
        const values = allIndicators.map(indicator => ({
          indicator_id: indicator.id,
          value: '',
          is_normal: undefined
        }));
        setIndicatorValues(values);
        return true;
      } else if (planData.template_id) {
        const template = templates.find(t => t.id === planData.template_id);
        if (template) {
          setSelectedTemplate(template);
          setBatchNumber(planData.batch_number || '');
          setIsEditing(false);
          setEditingReportId(null);
          const allIndicators = getAllIndicators(template);
          const values = allIndicators.map(indicator => ({
            indicator_id: indicator.id,
            value: '',
            is_normal: undefined
          }));
          setIndicatorValues(values);
          return true;
        }
      }
    } catch (e) {
      console.error('Error processing planData:', e);
    }
    return false;
  };

  // Флаг для предотвращения двойной обработки
  const processedPlanDataRef = useRef<string | null>(null);

  // Обработка перехода из Plans с данными для создания отчета
  useEffect(() => {
    const state = location.state as any;
    if (state?.activeTab === 'new-report' && state?.autoCreate) {
      // Создаём уникальный ключ для этих данных
      const dataKey = state.planData 
        ? `${state.planData.plan_item_id}-${state.planData.batch_number}-${state.planData.template_id}`
        : 'localStorage';
      
      // Проверяем, не обрабатывали ли мы уже эти данные
      if (processedPlanDataRef.current === dataKey) {
        return;
      }
      processedPlanDataRef.current = dataKey;
      
      setActiveTab('new-report');
      
      // Сначала пробуем данные из navigate state
      if (state.planData) {
        processPlanData(state.planData);
      } else {
        // Fallback на localStorage
        processPlanItemToReport();
      }
    }
  }, [location.state]);

  // Обработка localStorage после загрузки шаблонов
  useEffect(() => {
    if (templates.length > 0) {
      processPlanItemToReport();
    }
  }, [templates]);

  const fetchReports = async () => {
    setIsLoadingHistory(true);
    try {
      const params = new URLSearchParams();
      if (filterTemplateId) params.append('template_id', filterTemplateId.toString());
      if (filterDateFrom) params.append('date_from', filterDateFrom);
      if (filterDateTo) params.append('date_to', filterDateTo);
      
      const response = await api.get(`/api/reports/filtered/list?${params.toString()}`);
      setReports(response.data);
    } catch (error) {
      console.error('Error fetching reports:', error);
      showToast('Ошибка при загрузке отчетов', 'danger');
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await api.get('/api/templates/active');
      setTemplates(response.data);
      // Проверяем, есть ли данные из Plans в localStorage
      const storedData = localStorage.getItem('planItemToReport');
      const state = location.state as any;
      const hasNavigateData = state?.activeTab === 'new-report' && state?.autoCreate && state?.planData;
      if (!storedData && !hasNavigateData && response.data.length > 0) {
        handleTemplateSelect(response.data[0]);
      } else if (storedData) {
        // Данные из Plans будут обработаны отдельным useEffect
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
      showToast('Ошибка при загрузке шаблонов', 'danger');
    }
  };

  const handleTemplateSelect = (template: AnalysisType) => {
    setSelectedTemplate(template);
    setBatchNumber('');
    setVariety('');
    setIsEditing(false);
    setEditingReportId(null);
    const allIndicators = getAllIndicators(template);
    const values = allIndicators.map(indicator => ({
      indicator_id: indicator.id,
      value: '',
      is_normal: undefined
    }));
    setIndicatorValues(values);
  };

  const handleIndicatorValueChange = (indicatorId: number, value: string) => {
    setIndicatorValues(prev => {
      const updated = [...prev];
      const index = updated.findIndex(v => v.indicator_id === indicatorId);
      
      if (index !== -1) {
        updated[index] = { ...updated[index], value };
        
        const allIndicators = selectedTemplate ? getAllIndicators(selectedTemplate) : [];
        const indicator = allIndicators.find(ind => ind.id === indicatorId);
        if (indicator && indicator.min_value !== null && indicator.max_value !== null) {
          const numValue = parseFloat(value);
          if (!isNaN(numValue)) {
            updated[index].is_normal = numValue >= indicator.min_value && 
                                       numValue <= indicator.max_value;
          }
        }
      }
      return updated;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedTemplate || !batchNumber) {
      showToast('Пожалуйста, выберите шаблон и введите номер партии', 'warning');
      return;
    }
    
    if (indicatorValues.some(v => v.value === '' || v.value === undefined)) {
      showToast('Пожалуйста, заполните все значения показателей', 'warning');
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      const reportData: any = {
        template_id: selectedTemplate.id,
        batch_number: batchNumber,
        variety: variety || null,
        values: indicatorValues.map(v => ({
          indicator_id: v.indicator_id,
          value: typeof v.value === 'string' && !isNaN(parseFloat(v.value)) 
            ? parseFloat(v.value) 
            : v.value,
          is_normal: v.is_normal
        }))
      };

      if (!isEditing && planItemId) {
        reportData.plan_item_id = planItemId;
      }

      if (isEditing && editingReportId) {
        await api.put(`/api/reports/${editingReportId}`, reportData);
        showToast('Отчет успешно обновлен!', 'success');
        setIsEditing(false);
        setEditingReportId(null);
      } else {
        const response = await api.post('/api/reports/', reportData);
        showToast('Отчет успешно отправлен!', 'success');
        
        if (planItemId) {
          const reportId = response.data?.id || 'создан';
          showToast(`Отчет #${reportId} создан и привязан к плану!`, 'success');
          
          // Обновляем план: помечаем элемент как выполненный и сохраняем batch_number
          try {
            console.log('Updating plan item:', planItemId, 'batch_number:', batchNumber);
            const patchResponse = await api.patch(`/api/plans/items/${planItemId}`, { 
              is_completed: true,
              batch_number: batchNumber,
            });
            console.log('Plan item updated successfully:', patchResponse.data);
          } catch (planError: any) {
            console.error('Error updating plan item:', planError);
            showToast('Отчет создан, но ошибка при обновлении плана', 'warning');
          }
          
          // Возвращаемся на страницу планирования
          navigate('/plans');
          return;
        }
      }
      
      setBatchNumber('');
    setVariety('');
      setPlanItemId(null);
      if (selectedTemplate) {
        const allIndicators = getAllIndicators(selectedTemplate);
        setIndicatorValues(allIndicators.map(indicator => ({
          indicator_id: indicator.id,
          value: '',
          is_normal: undefined
        })));
      }
      
      fetchReports();
    } catch (error: any) {
      console.error('Error submitting report:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Неизвестная ошибка';
      showToast(`Ошибка при отправке отчета: ${errorMsg}`, 'danger');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleViewReport = async (reportId: number) => {
    try {
      const response = await api.get(`/api/reports/${reportId}`);
      const reportData = response.data;
      setViewReport(reportData);
      
      // API теперь возвращает все данные о показателях, включая названия и единицы измерения
      console.log('Report data:', reportData);
      
      // Просто используем значения, которые вернул API
      setViewReportIndicators(reportData.values || []);
      // сброс предыдущего AI-разбора
      setAiResult(null);
      setAiError(null);
      setAiLoading(false);
      setShowViewModal(true);
    } catch (error) {
      console.error('Error fetching report:', error);
      showToast('Ошибка при загрузке отчета', 'danger');
    }
  };

  const handleAiAnalyze = async () => {
    if (!viewReport) return;
    setAiLoading(true);
    setAiError(null);
    setAiResult(null);
    try {
      const response = await api.post(`/api/ai/reports/${viewReport.id}/analyze`);
      setAiResult(response.data);
    } catch (error: any) {
      const detail = error?.response?.data?.detail || 'Не удалось выполнить AI-разбор';
      setAiError(detail);
    } finally {
      setAiLoading(false);
    }
  };

  const severityColor = (s: string) =>
    s === 'high' ? 'danger' : s === 'medium' ? 'warning' : 'secondary';
  const severityText = (s: string) =>
    s === 'high' ? 'Высокая' : s === 'medium' ? 'Средняя' : 'Низкая';

  const handleEditReport = async (reportId: number) => {
    try {
      const response = await api.get(`/api/reports/${reportId}`);
      const report = response.data;
      
      const templateResponse = await api.get(`/api/templates/${report.analysis_type_id}`);
      const template = templateResponse.data;
      
      setSelectedTemplate(template);
      setBatchNumber(report.batch_number || '');
      setVariety(report.variety || '');
      setIsEditing(true);
      setEditingReportId(reportId);
      
      const allIndicators = getAllIndicators(template);
      const values = allIndicators.map(indicator => {
        const existingValue = report.indicator_values?.find(
          (v: any) => v.indicator_id === indicator.id
        );
        return {
          indicator_id: indicator.id,
          value: existingValue?.value?.toString() || existingValue?.text_value || '',
          is_normal: existingValue?.is_normal
        };
      });
      setIndicatorValues(values);
      
      setActiveTab('new-report');
    } catch (error) {
      console.error('Error loading report for editing:', error);
      showToast('Ошибка при загрузке отчета для редактирования', 'danger');
    }
  };

  const handleClearHistory = async () => {
    if (!window.confirm('Вы уверены, что хотите очистить всю историю отчетов? Это действие нельзя отменить.')) {
      return;
    }

    try {
      const response = await api.delete('/api/reports/history/clear');
      console.log('Clear history response:', response.data);
      showToast(response.data?.message || 'История отчетов успешно очищена!', 'success');
      setReports([]);
      // Перезагружаем список отчетов с сервера для подтверждения
      await fetchReports();
    } catch (error: any) {
      console.error('Error clearing history:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при очистке истории';
      showToast(errorMessage, 'danger');
    }
  };

  const handleFilterApply = () => fetchReports();
  
  const handleFilterReset = () => {
    setFilterTemplateId(null);
    setFilterDateFrom('');
    setFilterDateTo('');
    setTimeout(fetchReports, 0);
  };

  const getTemplateName = (templateId: number) => {
    const template = templates.find(t => t.id === templateId);
    return template ? template.name : `Шаблон #${templateId}`;
  };

  const getStatusBadge = (status: string): 'success' | 'warning' | 'danger' | 'secondary' => {
    const statusMap: Record<string, 'success' | 'warning' | 'danger' | 'secondary'> = {
      completed: 'success',
      pending: 'warning',
      error: 'danger'
    };
    return statusMap[status] || 'secondary';
  };

  const getStatusText = (status: string) => {
    const textMap: Record<string, string> = {
      completed: 'Завершен',
      pending: 'В ожидании',
      error: 'Ошибка'
    };
    return textMap[status] || status;
  };

  const getTotalIndicators = (template: AnalysisType): number => {
    return (template.template_indicators?.length || 0);
  };

  return (
    <div className="min-vh-100 bg-light">
      <AppHeader showAdminLink />

      <main className="app-main">
        <div className="container-fluid">
          <div className="page-wrapper">
            <div className="mb-4">
              <h2 className="h3 mb-1">Панель управления</h2>
              <p className="text-muted mb-0">Внесение данных и просмотр истории анализов</p>
            </div>

            <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k || 'new-report')} className="mb-4">
              <Tab eventKey="new-report" title={
                <span>Новый отчет</span>
              }>
                <Card>
                  <CardHeader>
                    <CardTitle className="h5 mb-0">
                      {isEditing ? 'Редактирование отчета' : 'Внесение данных анализа'}
                      {isEditing && editingReportId && (
                        <Badge bg="warning" className="ms-2">Отчет #{editingReportId}</Badge>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardBody>
                    {isEditing && (
                      <Alert variant="info">
                        Вы редактируете существующий отчет. Внесите изменения и нажмите "Сохранить изменения".
                      </Alert>
                    )}
                    <p className="text-muted mb-4">
                      {isEditing 
                        ? 'Измените значения показателей и сохраните отчет'
                        : 'Выберите шаблон анализа, заполните показатели и отправьте отчет'
                      }
                    </p>

                    {/* Template Selection */}
                    <Form.Group className="mb-4">
                      <Form.Label>Выберите шаблон анализа</Form.Label>
                      {templates.length === 0 ? (
                        <Alert variant="warning">
                          Нет доступных шаблонов. Обратитесь к администратору для создания шаблонов.
                        </Alert>
                      ) : (
                        <div>
                          <Form.Select
                            value={selectedTemplate?.id || ''}
                            onChange={(e) => {
                              const template = templates.find(t => t.id === parseInt(e.target.value));
                              if (template) handleTemplateSelect(template);
                            }}
                            disabled={isEditing}
                          >
                            <option value="" disabled>-- Выберите шаблон --</option>
                            {templates.map((template) => (
                              <option key={template.id} value={template.id}>
                                {template.name} ({getTotalIndicators(template)} показателей)
                              </option>
                            ))}
                          </Form.Select>
                          
                          {selectedTemplate?.description && (
                            <Alert variant="info" className="mt-3">
                              <Alert.Heading>{selectedTemplate.name}</Alert.Heading>
                              <p className="mb-0">{selectedTemplate.description}</p>
                            </Alert>
                          )}
                        </div>
                      )}
                    </Form.Group>

                    {selectedTemplate && (
                      <Form onSubmit={handleSubmit}>
                        {/* Batch Number */}
                        <Form.Group className="mb-4">
                          <Form.Label>Номер партии</Form.Label>
                          <Form.Control
                            type="text"
                            value={batchNumber}
                            onChange={(e) => setBatchNumber(e.target.value)}
                            placeholder="Введите номер партии"
                            required
                          />
                        </Form.Group>

                        {/* Сорт (для подбора техкарты AI-экспертом) */}
                        <Form.Group className="mb-4">
                          <Form.Label>Сорт</Form.Label>
                          <Form.Control
                            type="text"
                            value={variety}
                            onChange={(e) => setVariety(e.target.value)}
                            placeholder="Например: Жигулёвское (необязательно)"
                          />
                          <Form.Text className="text-muted">
                            Используется для подбора технологической карты при разборе отклонений.
                          </Form.Text>
                        </Form.Group>

                        {/* Indicators */}
                        <div className="mb-4">
                          <h5 className="mb-3">
                            Показатели для анализа: {selectedTemplate.name}
                          </h5>
                          
                          <div className="row g-3">
                            {(() => {
                              const allIndicators = getAllIndicators(selectedTemplate);
                              return allIndicators.map((indicator: any) => {
                                const indicatorValue = indicatorValues.find(v => v.indicator_id === indicator.id);
                                const isOutOfRange = indicatorValue && 
                                    indicator.min_value !== null && 
                                    indicator.max_value !== null &&
                                    !isNaN(parseFloat(indicatorValue.value as string)) &&
                                    (parseFloat(indicatorValue.value as string) < indicator.min_value || 
                                     parseFloat(indicatorValue.value as string) > indicator.max_value);
                                
                                return (
                                  <div key={indicator.id} className="col-12">
                                    <Card>
                                      <CardBody>
                                        <div className="row g-3">
                                            <div className="col-md-4">
                                            <Form.Label>
                                              {indicator.name}, {indicator.unit}
                                              {indicator.is_library && (
                                                <Badge bg="info" className="ms-1" pill>Справочник</Badge>
                                              )}
                                            </Form.Label>
                                            {(indicator.min_value !== null || indicator.max_value !== null) && (
                                              <small className="text-muted d-block">
                                                Норма: {indicator.min_value !== null ? `от ${indicator.min_value}` : ''} {indicator.max_value !== null ? `до ${indicator.max_value}` : ''}
                                              </small>
                                            )}
                                          </div>
                                          <div className="col-md-8">
                                            {indicator.data_type === 'select' ? (
                                              <Form.Select
                                                className={isOutOfRange ? 'is-invalid' : ''}
                                                value={indicatorValue?.value || ''}
                                                onChange={(e) => handleIndicatorValueChange(indicator.id, e.target.value)}
                                                required
                                              >
                                                <option value="">-- Выберите --</option>
                                                {(indicator.options || []).map((opt: string, i: number) => (
                                                  <option key={i} value={opt}>{opt}</option>
                                                ))}
                                              </Form.Select>
                                            ) : (
                                              <Form.Control
                                                type={indicator.data_type === 'number' ? 'number' : 'text'}
                                                className={isOutOfRange ? 'is-invalid' : ''}
                                                value={indicatorValue?.value || ''}
                                                onChange={(e) => handleIndicatorValueChange(indicator.id, e.target.value)}
                                                step={indicator.data_type === 'number' ? '0.01' : undefined}
                                                placeholder={`Введите значение (${indicator.data_type})`}
                                                required
                                              />
                                            )}
                                            
                                            {indicatorValue?.value && indicator.data_type === 'select' && indicator.options && (
                                              <small className="text-muted d-block mt-1">
                                                Варианты: {indicator.options.join(', ')}
                                              </small>
                                            )}
                                            
                                            {isOutOfRange && (
                                              <div className="invalid-feedback d-block">
                                                Значение вне нормы!
                                              </div>
                                            )}
                                          </div>
                                        </div>
                                      </CardBody>
                                    </Card>
                                  </div>
                                );
                              });
                            })()}
                          </div>
                        </div>

                        <div className="d-flex justify-content-end gap-2">
                          {isEditing && (
                            <Button 
                              variant="secondary" 
                              onClick={() => {
                                setIsEditing(false);
                                setEditingReportId(null);
                                setBatchNumber('');
    setVariety('');
                                if (selectedTemplate) {
                                  const allIndicators = getAllIndicators(selectedTemplate);
                                  setIndicatorValues(allIndicators.map(indicator => ({
                                    indicator_id: indicator.id,
                                    value: '',
                                    is_normal: undefined
                                  })));
                                }
                              }}
                            >
                              Отменить редактирование
                            </Button>
                          )}
                          <Button type="submit" variant="primary" disabled={isSubmitting}>
                            {isSubmitting ? (
                              <>
                                <Spinner as="span" animation="border" size="sm" className="me-2" />
                                Отправка...
                              </>
                            ) : (
                              <>
                                {isEditing ? 'Сохранить изменения' : 'Отправить отчет'}
                              </>
                            )}
                          </Button>
                        </div>
                      </Form>
                    )}
                  </CardBody>
                </Card>
              </Tab>

              <Tab eventKey="history" title={
                <span>История отчетов</span>
              }>
                <Card>
                  <CardHeader>
                    <CardTitle className="h5 mb-0">
                      История отчетов
                    </CardTitle>
                  </CardHeader>
                  <CardBody>
                    {/* Filters */}
                    <Card className="mb-4">
                      <CardHeader className="bg-light">
                        <CardTitle className="h6 mb-0">
                          Фильтры
                        </CardTitle>
                      </CardHeader>
                      <CardBody>
                        <div className="row g-3">
                          <div className="col-md-4">
                            <Form.Label>Шаблон</Form.Label>
                            <Form.Select
                              value={filterTemplateId || ''}
                              onChange={(e) => setFilterTemplateId(e.target.value ? parseInt(e.target.value) : null)}
                            >
                              <option value="">Все шаблоны</option>
                              {templates.map((t) => (
                                <option key={t.id} value={t.id}>{t.name}</option>
                              ))}
                            </Form.Select>
                          </div>
                          <div className="col-md-3">
                            <Form.Label>Дата с</Form.Label>
                            <Form.Control
                              type="date"
                              value={filterDateFrom}
                              onChange={(e) => setFilterDateFrom(e.target.value)}
                            />
                          </div>
                          <div className="col-md-3">
                            <Form.Label>по</Form.Label>
                            <Form.Control
                              type="date"
                              value={filterDateTo}
                              onChange={(e) => setFilterDateTo(e.target.value)}
                            />
                          </div>
                        </div>
                        <div className="mt-3 d-flex gap-2">
                          <Button variant="primary" onClick={handleFilterApply}>
                            Применить
                          </Button>
                          <Button variant="secondary" onClick={handleFilterReset}>
                            Сбросить
                          </Button>
                        </div>
                      </CardBody>
                    </Card>

                    {/* Reports List */}
                    {isLoadingHistory ? (
                      <div className="text-center py-4">
                        <Spinner animation="border" />
                        <p className="text-muted mt-2">Загрузка...</p>
                      </div>
                    ) : reports.length === 0 ? (
                      <div className="text-center py-4">
                        <p className="text-muted mt-2">Нет отчетов для отображения</p>
                      </div>
                    ) : (
                      <div>
                        <div className="table-responsive">
                          <Table striped hover>
                            <thead>
                              <tr>
                                <th>Номер партии</th>
                                <th>Шаблон</th>
                                <th>Дата</th>
                                <th>Статус</th>
                                <th className="text-end">Действия</th>
                              </tr>
                            </thead>
                            <tbody>
                              {reports.map((report) => (
                                <tr key={report.id}>
                                  <td><strong>{report.batch_number}</strong></td>
                                  <td>{getTemplateName(report.analysis_type_id)}</td>
                                  <td>{new Date(report.started_at).toLocaleString('ru-RU')}</td>
                                  <td>
                                    <Badge bg={getStatusBadge(report.status)}>
                                      {getStatusText(report.status)}
                                    </Badge>
                                  </td>
                                  <td className="text-end">
                                    <Button variant="outline-primary" size="sm" onClick={() => handleViewReport(report.id)}>
                                      Просмотр
                                    </Button>
                                    <Button variant="outline-warning" size="sm" className="ms-2" onClick={() => handleEditReport(report.id)}>
                                      Редактировать
                                    </Button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </Table>
                        </div>

                        {reports.length > 0 && (
                          <div className="mt-4 d-flex justify-content-end">
                            <Button variant="danger" onClick={handleClearHistory}>
                              Очистить всю историю
                            </Button>
                          </div>
                        )}
                      </div>
                    )}
                  </CardBody>
                </Card>
              </Tab>
            </Tabs>
          </div>
        </div>
      </main>

      {/* View Report Modal */}
      {showViewModal && viewReport && (
        <div className="modal d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  Отчет #{viewReport.id} — {viewReport.batch_number}
                </h5>
                <button type="button" className="btn-close" onClick={() => setShowViewModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className="mb-3">
                  <strong>Шаблон:</strong> {getTemplateName(viewReport.analysis_type_id)}
                </div>
                {(viewReport as any).variety && (
                  <div className="mb-3">
                    <strong>Сорт:</strong> {(viewReport as any).variety}
                  </div>
                )}
                <div className="mb-3">
                  <strong>Дата:</strong> {new Date(viewReport.started_at).toLocaleString('ru-RU')}
                </div>
                <div className="mb-3">
                  <strong>Статус:</strong>{' '}
                  <Badge bg={getStatusBadge(viewReport.status)}>
                    {getStatusText(viewReport.status)}
                  </Badge>
                </div>
                
                <hr />
                <h6>Значения показателей:</h6>
                {viewReportIndicators.length === 0 ? (
                  <Alert variant="info">Нет данных по показателям</Alert>
                ) : (
                  <Table striped size="sm">
                    <thead>
                      <tr>
                        <th>Показатель</th>
                        <th>Значение</th>
                        <th>Норма</th>
                        <th>Статус</th>
                      </tr>
                    </thead>
                    <tbody>
                      {viewReportIndicators.map((v, i) => (
                        <tr key={i}>
                          <td>{v.name}, {v.unit}</td>
                          <td><strong>{v.value || v.text_value || '-'}</strong></td>
                          <td>
                            {(v.min_value !== null || v.max_value !== null)
                              ? `от ${v.min_value ?? '?'} до ${v.max_value ?? '?'}`
                              : 'Не задана'}
                          </td>
                          <td>
                            <Badge bg={v.is_normal ? 'success' : 'danger'}>
                              {v.is_normal ? 'В норме' : 'Отклонение'}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                )}

                {aiEnabled && (
                <>
                <hr />
                <div className="d-flex align-items-center justify-content-between mb-2">
                  <h6 className="mb-0">🍺 Разбор ИИ-эксперта</h6>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleAiAnalyze}
                    disabled={aiLoading}
                  >
                    {aiLoading ? (
                      <><Spinner animation="border" size="sm" className="me-2" />Анализирую…</>
                    ) : (
                      'Разобрать отклонения'
                    )}
                  </Button>
                </div>

                {aiError && <Alert variant="danger">{aiError}</Alert>}

                {aiResult && (
                  <div>
                    <Alert variant={aiResult.deviations_count === 0 ? 'success' : 'info'}>
                      {aiResult.summary}
                      {aiResult.knowledge_used > 0 && (
                        <div className="small text-muted mt-1">
                          📄 Учтена техкарта: фрагментов — {aiResult.knowledge_used}
                        </div>
                      )}
                    </Alert>
                    {(aiResult.deviations || []).map((d: any, i: number) => (
                      <Card key={i} className="mb-2">
                        <CardBody>
                          <div className="d-flex align-items-center justify-content-between mb-1">
                            <strong>{d.indicator}</strong>
                            <Badge bg={severityColor(d.severity)}>
                              {severityText(d.severity)}
                            </Badge>
                          </div>
                          {(d.value !== undefined) && (
                            <div className="text-muted small mb-2">
                              Значение: {d.value}{d.unit ? ` ${d.unit}` : ''}
                              {d.norm ? ` · норма: ${d.norm}` : ''}
                              {d.direction ? ` · ${d.direction === 'below' ? 'ниже нормы' : 'выше нормы'}` : ''}
                              {d.deviation_pct != null ? ` (${d.deviation_pct}%)` : ''}
                            </div>
                          )}
                          <div className="mb-2">{d.interpretation}</div>
                          {d.likely_causes?.length > 0 && (
                            <div className="mb-2">
                              <div className="fw-semibold small text-muted">Вероятные причины:</div>
                              <ul className="mb-0">
                                {d.likely_causes.map((c: string, j: number) => <li key={j}>{c}</li>)}
                              </ul>
                            </div>
                          )}
                          {d.actions?.length > 0 && (
                            <div>
                              <div className="fw-semibold small text-muted">Что сделать:</div>
                              <ul className="mb-0">
                                {d.actions.map((a: string, j: number) => <li key={j}>{a}</li>)}
                              </ul>
                            </div>
                          )}
                        </CardBody>
                      </Card>
                    ))}
                  </div>
                )}
                </>
                )}
              </div>
              <div className="modal-footer">
                <Button variant="secondary" onClick={() => setShowViewModal(false)}>
                  Закрыть
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      <AppToast toast={toast} onClose={hideToast} />
    </div>
  );
};

export default Dashboard;