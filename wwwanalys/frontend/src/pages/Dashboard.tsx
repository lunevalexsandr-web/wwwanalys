/** Dashboard page - report creation and history */
import React, { useState, useEffect } from 'react';
import { 
  Card, CardHeader, CardTitle, CardBody, Tabs, Tab, Form, Button, 
  Alert, Badge, Table, Spinner
} from 'react-bootstrap';
import AppHeader from '../components/AppHeader';
import AppToast from '../components/AppToast';
import { useToast } from '../hooks/useToast';
import api from '../api/axios';
import type { AnalysisType, IndicatorValue, Report, ToastState, TemplateIndicator } from '../types';

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('new-report');
  const [templates, setTemplates] = useState<AnalysisType[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<AnalysisType | null>(null);
  const [batchNumber, setBatchNumber] = useState('');
  const [indicatorValues, setIndicatorValues] = useState<IndicatorValue[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
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
  
  const { toast, showToast, hideToast } = useToast();

  useEffect(() => {
    fetchTemplates();
    fetchReports();
  }, []);

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
      if (response.data.length > 0) {
        handleTemplateSelect(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
      showToast('Ошибка при загрузке шаблонов', 'danger');
    }
  };

  /**
   * Получить все показатели шаблона (объединяет обычные + из справочника).
   */
  const getAllIndicators = (template: AnalysisType): (any)[] => {
    // Из справочника (template_indicators)
    const libInds = (template.template_indicators || []).map(ti => ({
      id: ti.indicator_id,  // используем indicator_id как id для matching
      name: ti.name,
      unit: ti.unit,
      min_value: ti.min_value,
      max_value: ti.max_value,
      data_type: ti.data_type,
      options: ti.options,
      is_library: true
    }));
    
    // Обычные
    const regularInds = (template.indicators || []).map(ind => ({
      ...ind,
      is_library: false
    }));
    
    return [...libInds, ...regularInds];
  };

  const handleTemplateSelect = (template: AnalysisType) => {
    setSelectedTemplate(template);
    setBatchNumber('');
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
      const reportData = {
        template_id: selectedTemplate.id,
        batch_number: batchNumber,
        values: indicatorValues.map(v => ({
          indicator_id: v.indicator_id,
          value: typeof v.value === 'string' && !isNaN(parseFloat(v.value)) 
            ? parseFloat(v.value) 
            : v.value,
          is_normal: v.is_normal
        }))
      };
      
      await api.post('/api/reports/', reportData);
      showToast('Отчет успешно отправлен!', 'success');
      
      // Reset form
      setBatchNumber('');
      if (selectedTemplate) {
        const allIndicators = getAllIndicators(selectedTemplate);
        setIndicatorValues(allIndicators.map(indicator => ({
          indicator_id: indicator.id,
          value: '',
          is_normal: undefined
        })));
      }
      
      fetchReports();
    } catch (error) {
      console.error('Error submitting report:', error);
      showToast('Ошибка при отправке отчета', 'danger');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleViewReport = async (reportId: number) => {
    try {
      const response = await api.get(`/api/reports/${reportId}`);
      const reportData = response.data;
      setViewReport(reportData);
      
      // Find the template to get indicator names
      const template = templates.find(t => t.id === reportData.analysis_type_id);
      const allIndicators = template ? getAllIndicators(template) : [];
      
      // Map indicator values with names
      const enrichedValues = (reportData.values || []).map((v: any) => {
        const indicator = allIndicators.find((ind: any) => ind.id === v.indicator_id);
        return {
          ...v,
          indicator_name: indicator?.name || `#${v.indicator_id}`,
          indicator_unit: indicator?.unit || '',
          indicator_min: indicator?.min_value,
          indicator_max: indicator?.max_value
        };
      });
      setViewReportIndicators(enrichedValues);
      setShowViewModal(true);
    } catch (error) {
      console.error('Error fetching report:', error);
      showToast('Ошибка при загрузке отчета', 'danger');
    }
  };

  const handleClearHistory = async () => {
    if (!window.confirm('Вы уверены, что хотите очистить всю историю отчетов? Это действие нельзя отменить.')) {
      return;
    }

    try {
      await api.delete('/api/reports/history/clear');
      showToast('История отчетов успешно очищена!', 'success');
      setReports([]);
    } catch (error) {
      console.error('Error clearing history:', error);
      showToast('Ошибка при очистке истории', 'danger');
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
    return (template.indicators?.length || 0) + (template.template_indicators?.length || 0);
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
                <span><i className="bi bi-plus-circle-fill me-1"></i>Новый отчет</span>
              }>
                <Card>
                  <CardHeader>
                    <CardTitle className="h5 mb-0">
                      <i className="bi bi-file-earmark-text me-2 text-primary"></i>
                      Внесение данных анализа
                    </CardTitle>
                  </CardHeader>
                  <CardBody>
                    <p className="text-muted mb-4">
                      Выберите шаблон анализа, заполните показатели и отправьте отчет
                    </p>

                    {/* Template Selection */}
                    <Form.Group className="mb-4">
                      <Form.Label><i className="bi bi-list-ul me-1"></i>Выберите шаблон анализа</Form.Label>
                      {templates.length === 0 ? (
                        <Alert variant="warning">
                          <i className="bi bi-exclamation-triangle-fill me-2"></i>
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
                          <Form.Label><i className="bi bi-barcode me-1"></i>Номер партии</Form.Label>
                          <Form.Control
                            type="text"
                            value={batchNumber}
                            onChange={(e) => setBatchNumber(e.target.value)}
                            placeholder="Введите номер партии"
                            required
                          />
                        </Form.Group>

                        {/* Indicators */}
                        <div className="mb-4">
                          <h5 className="mb-3">
                            <i className="bi bi-speedometer2 me-2 text-primary"></i>
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
                                            {indicator.min_value !== null && indicator.max_value !== null && (
                                              <small className="text-muted d-block">
                                                Норма: {indicator.min_value} - {indicator.max_value}
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
                                                <i className="bi bi-exclamation-circle-fill me-1"></i>
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

                        <div className="d-flex justify-content-end">
                          <Button type="submit" variant="primary" disabled={isSubmitting}>
                            {isSubmitting ? (
                              <>
                                <Spinner as="span" animation="border" size="sm" className="me-2" />
                                Отправка...
                              </>
                            ) : (
                              <>
                                <i className="bi bi-send-fill me-2"></i>
                                Отправить отчет
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
                <span><i className="bi bi-clock-history me-1"></i>История отчетов</span>
              }>
                <Card>
                  <CardHeader>
                    <CardTitle className="h5 mb-0">
                      <i className="bi bi-journal-text me-2 text-primary"></i>
                      История отчетов
                    </CardTitle>
                  </CardHeader>
                  <CardBody>
                    {/* Filters */}
                    <Card className="mb-4">
                      <CardHeader className="bg-light">
                        <CardTitle className="h6 mb-0">
                          <i className="bi bi-funnel me-1"></i>Фильтры
                        </CardTitle>
                      </CardHeader>
                      <CardBody>
                        <div className="row g-3">
                          <div className="col-md-4">
                            <Form.Label><i className="bi bi-list-ul me-1"></i>Шаблон</Form.Label>
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
                            <Form.Label><i className="bi bi-calendar-range me-1"></i>Дата с</Form.Label>
                            <Form.Control
                              type="date"
                              value={filterDateFrom}
                              onChange={(e) => setFilterDateFrom(e.target.value)}
                            />
                          </div>
                          <div className="col-md-3">
                            <Form.Label><i className="bi bi-calendar-check me-1"></i>по</Form.Label>
                            <Form.Control
                              type="date"
                              value={filterDateTo}
                              onChange={(e) => setFilterDateTo(e.target.value)}
                            />
                          </div>
                        </div>
                        <div className="mt-3 d-flex gap-2">
                          <Button variant="primary" onClick={handleFilterApply}>
                            <i className="bi bi-check-circle me-1"></i>Применить
                          </Button>
                          <Button variant="secondary" onClick={handleFilterReset}>
                            <i className="bi bi-arrow-counterclockwise me-1"></i>Сбросить
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
                        <i className="bi bi-inbox display-1 text-muted"></i>
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
                                      <i className="bi bi-eye me-1"></i>Просмотр
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
                              <i className="bi bi-trash me-1"></i>
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
                  <i className="bi bi-file-earmark-text me-2 text-primary"></i>
                  Отчет #{viewReport.id} — {viewReport.batch_number}
                </h5>
                <button type="button" className="btn-close" onClick={() => setShowViewModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className="mb-3">
                  <strong>Шаблон:</strong> {getTemplateName(viewReport.analysis_type_id)}
                </div>
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
                          <td>{v.indicator_name}, {v.indicator_unit}</td>
                          <td><strong>{v.value || v.text_value || '-'}</strong></td>
                          <td>
                            {v.indicator_min !== null && v.indicator_max !== null
                              ? `${v.indicator_min} — ${v.indicator_max}`
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