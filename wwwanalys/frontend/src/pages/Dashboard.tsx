import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';

interface Indicator {
  id: number;
  name: string;
  unit: string;
  min_value: number;
  max_value: number;
  type: 'FLOAT' | 'TEXT';
}

interface AnalysisType {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  indicators: Indicator[];
}

interface IndicatorValue {
  indicator_id: number;
  value: string | number;
  is_normal?: boolean;
}

interface Report {
  id: number;
  batch_number: string;
  analysis_type_id: number;
  started_at: string;
  status: string;
  notes?: string;
}

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
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

  useEffect(() => {
    fetchTemplates();
    fetchReports();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await api.get('/api/templates/active');
      setTemplates(response.data);
      if (response.data.length > 0) {
        handleTemplateSelect(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
      alert('Ошибка при загрузке шаблонов');
    }
  };

  const fetchReports = async () => {
    setIsLoadingHistory(true);
    try {
      let url = '/api/reports/filtered/list?';
      if (filterTemplateId) {
        url += `template_id=${filterTemplateId}&`;
      }
      if (filterDateFrom) {
        url += `date_from=${filterDateFrom}&`;
      }
      if (filterDateTo) {
        url += `date_to=${filterDateTo}&`;
      }
      
      const response = await api.get(url);
      setReports(response.data);
    } catch (error) {
      console.error('Error fetching reports:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleTemplateSelect = (template: AnalysisType) => {
    setSelectedTemplate(template);
    setBatchNumber('');
    
    // Initialize indicator values
    const values = template.indicators.map(indicator => ({
      indicator_id: indicator.id,
      value: '',
      is_normal: undefined
    }));
    setIndicatorValues(values);
  };

  const handleIndicatorValueChange = (indicatorId: number, value: string) => {
    const updatedValues = [...indicatorValues];
    const indicatorIndex = updatedValues.findIndex(v => v.indicator_id === indicatorId);
    
    if (indicatorIndex !== -1) {
      updatedValues[indicatorIndex].value = value;
      
      // Check if value is normal (only for FLOAT type)
      const indicator = selectedTemplate?.indicators.find(ind => ind.id === indicatorId);
      if (indicator && indicator.min_value !== undefined && indicator.max_value !== undefined) {
        const numValue = parseFloat(value);
        if (!isNaN(numValue)) {
          updatedValues[indicatorIndex].is_normal = numValue >= indicator.min_value && numValue <= indicator.max_value;
        } else {
          updatedValues[indicatorIndex].is_normal = undefined;
        }
      }
      
      setIndicatorValues(updatedValues);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedTemplate || !batchNumber) {
      alert('Пожалуйста, выберите шаблон и введите номер партии');
      return;
    }
    
    if (indicatorValues.some(v => v.value === '' || v.value === undefined)) {
      alert('Пожалуйста, заполните все значения показателей');
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      const reportData = {
        template_id: selectedTemplate.id,
        batch_number: batchNumber,
        values: indicatorValues.map(v => ({
          indicator_id: v.indicator_id,
          value: typeof v.value === 'string' && !isNaN(parseFloat(v.value)) ? parseFloat(v.value) : v.value,
          is_normal: v.is_normal
        }))
      };
      
      await api.post('/api/reports/', reportData);
      alert('Отчет успешно отправлен!');
      
      // Reset form
      setBatchNumber('');
      setIndicatorValues(selectedTemplate.indicators.map(indicator => ({
        indicator_id: indicator.id,
        value: '',
        is_normal: undefined
      })));
      
      // Refresh history
      fetchReports();
    } catch (error) {
      console.error('Error submitting report:', error);
      alert('Ошибка при отправке отчета');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClearHistory = async () => {
    if (!window.confirm('Вы уверены, что хотите очистить всю историю отчетов? Это действие нельзя отменить.')) {
      return;
    }

    try {
      await api.delete('/api/reports/history/clear');
      alert('История отчетов успешно очищена!');
      setReports([]);
    } catch (error) {
      console.error('Error clearing history:', error);
      alert('Ошибка при очистке истории');
    }
  };

  const handleFilterApply = () => {
    fetchReports();
  };

  const handleFilterReset = () => {
    setFilterTemplateId(null);
    setFilterDateFrom('');
    setFilterDateTo('');
    fetchReports();
  };

  const getTemplateName = (templateId: number) => {
    const template = templates.find(t => t.id === templateId);
    return template ? template.name : `Шаблон #${templateId}`;
  };

  return (
    <div className="min-h-screen bg-light">
      <header className="bg-white shadow-sm">
        <div className="container-fluid">
          <div className="d-flex justify-content-between align-items-center h-16">
            <div className="d-flex">
              <div className="flex-shrink-0 d-flex align-items-center">
                <h1 className="h4 mb-0 text-dark">WWWAnalys</h1>
              </div>
              <nav className="ms-4 d-flex gap-3">
                {user?.is_admin && (
                  <a
                    href="/admin"
                    className="text-decoration-none text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm"
                  >
                    Админ-панель
                  </a>
                )}
              </nav>
            </div>
            <div className="d-flex align-items-center">
              <span className="me-3 text-dark">
                {user?.email} ({user?.is_admin ? 'ADMIN' : 'USER'})
              </span>
              <button
                onClick={logout}
                className="btn btn-danger"
              >
                Выйти
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="container-fluid py-4">
        <div className="p-4 border-4 border-dashed border-secondary rounded">
          {/* Tabs */}
          <div className="mb-4">
            <nav className="nav nav-tabs">
              <button
                onClick={() => setActiveTab('new-report')}
                className={`nav-link ${activeTab === 'new-report' ? 'active' : ''}`}
              >
                Новый отчет
              </button>
              <button
                onClick={() => setActiveTab('history')}
                className={`nav-link ${activeTab === 'history' ? 'active' : ''}`}
              >
                История отчетов
              </button>
            </nav>
          </div>

          {activeTab === 'new-report' && (
            <div>
              <h2 className="h3 mb-3">Панель внесения анализов</h2>
              <p className="text-muted mb-4">
                Выберите шаблон анализа, заполните показатели и отправьте отчет
              </p>

              {/* Template Selection */}
              <div className="mb-4">
                <label className="form-label">Выберите шаблон анализа</label>
                {templates.length === 0 ? (
                  <div className="alert alert-warning">
                    Нет доступных шаблонов. Обратитесь к администратору для создания шаблонов.
                  </div>
                ) : (
                  <div>
                    <select
                      value={selectedTemplate?.id || ''}
                      onChange={(e) => {
                        const template = templates.find(t => t.id === parseInt(e.target.value));
                        if (template) handleTemplateSelect(template);
                      }}
                      className="form-select"
                    >
                      <option value="" disabled>-- Выберите шаблон --</option>
                      {templates.map((template) => (
                        <option key={template.id} value={template.id}>
                          {template.name} ({template.indicators.length} показателей)
                        </option>
                      ))}
                    </select>
                    
                    {selectedTemplate && selectedTemplate.description && (
                      <div className="alert alert-info mt-3">
                        <h4 className="alert-heading">{selectedTemplate.name}</h4>
                        <p className="mb-0">{selectedTemplate.description}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {selectedTemplate && (
                <div>
                  {/* Batch Number */}
                  <div className="mb-4">
                    <label htmlFor="batch-number" className="form-label">
                      Номер партии
                    </label>
                    <input
                      type="text"
                      id="batch-number"
                      className="form-control"
                      value={batchNumber}
                      onChange={(e) => setBatchNumber(e.target.value)}
                      placeholder="Введите номер партии"
                    />
                  </div>

                  {/* Form */}
                  <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                      <h3 className="h5 mb-3">
                        Показатели для анализа: {selectedTemplate.name}
                      </h3>
                      
                      <div className="row g-3">
                        {selectedTemplate.indicators.map((indicator) => {
                          const indicatorValue = indicatorValues.find(v => v.indicator_id === indicator.id);
                          const isOutOfRange = indicatorValue && 
                              indicator.min_value !== undefined && 
                              indicator.max_value !== undefined &&
                              !isNaN(parseFloat(indicatorValue.value as string)) &&
                              (parseFloat(indicatorValue.value as string) < indicator.min_value || 
                               parseFloat(indicatorValue.value as string) > indicator.max_value);
                          
                          return (
                            <div key={indicator.id} className="col-12">
                              <div className="card">
                                <div className="card-body">
                                  <div className="row g-3">
                                    <div className="col-md-4">
                                      <label className="form-label">
                                        {indicator.name}, {indicator.unit}
                                      </label>
                                      {indicator.min_value !== undefined && indicator.max_value !== undefined && (
                                        <small className="text-muted d-block">
                                          Норма: {indicator.min_value} - {indicator.max_value}
                                        </small>
                                      )}
                                    </div>
                                    <div className="col-md-8">
                                      {indicatorValue && (
                                        <input
                                          type={indicator.type === 'FLOAT' ? 'number' : 'text'}
                                          className={`form-control ${isOutOfRange ? 'is-invalid' : ''}`}
                                          value={indicatorValue.value}
                                          onChange={(e) => handleIndicatorValueChange(indicator.id, e.target.value)}
                                          step={indicator.type === 'FLOAT' ? '0.01' : undefined}
                                          placeholder={`Введите значение (${indicator.type})`}
                                        />
                                      )}
                                      {isOutOfRange && (
                                        <div className="invalid-feedback">
                                          Значение вне нормы!
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div className="d-flex justify-content-end">
                      <button
                        type="submit"
                        disabled={isSubmitting}
                        className="btn btn-primary"
                      >
                        {isSubmitting ? 'Отправка...' : 'Отправить отчет'}
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {!templates.length && (
                <div className="text-center py-4">
                  <p className="text-muted">Нет доступных шаблонов анализа</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'history' && (
            <div>
              <h2 className="h3 mb-3">История отчетов</h2>
              
              {/* Filters */}
              <div className="card mb-4">
                <div className="card-body">
                  <h5 className="card-title">Фильтры</h5>
                  <div className="row g-3">
                    <div className="col-md-6">
                      <label className="form-label">Шаблон</label>
                      <select
                        value={filterTemplateId || ''}
                        onChange={(e) => setFilterTemplateId(e.target.value ? parseInt(e.target.value) : null)}
                        className="form-select"
                      >
                        <option value="">Все шаблоны</option>
                        {templates.map((t) => (
                          <option key={t.id} value={t.id}>{t.name}</option>
                        ))}
                      </select>
                    </div>
                    <div className="col-md-3">
                      <label className="form-label">Дата с</label>
                      <input
                        type="date"
                        className="form-control"
                        value={filterDateFrom}
                        onChange={(e) => setFilterDateFrom(e.target.value)}
                      />
                    </div>
                    <div className="col-md-3">
                      <label className="form-label">по</label>
                      <input
                        type="date"
                        className="form-control"
                        value={filterDateTo}
                        onChange={(e) => setFilterDateTo(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="mt-3 d-flex gap-2">
                    <button
                      onClick={handleFilterApply}
                      className="btn btn-primary"
                    >
                      Применить
                    </button>
                    <button
                      onClick={handleFilterReset}
                      className="btn btn-secondary"
                    >
                      Сбросить
                    </button>
                  </div>
                </div>
              </div>

              {/* Reports List */}
              {isLoadingHistory ? (
                <div className="text-center py-4">
                  <p className="text-muted">Загрузка...</p>
                </div>
              ) : reports.length === 0 ? (
                <div className="text-center py-4 card">
                  <p className="text-muted">Нет отчетов для отображения</p>
                </div>
              ) : (
                <div className="accordion" id="reportsAccordion">
                  {reports.map((report, index) => (
                    <div key={report.id} className="accordion-item">
                      <h2 className="accordion-header">
                        <button
                          className="accordion-button"
                          type="button"
                          data-bs-toggle="collapse"
                          data-bs-target={`#collapse${index}`}
                        >
                          <div className="d-flex justify-content-between align-items-center w-100">
                            <div>
                              <h5 className="mb-1">Партия: {report.batch_number}</h5>
                              <p className="mb-0 text-muted">
                                Шаблон: {getTemplateName(report.analysis_type_id)}
                              </p>
                            </div>
                            <span className={`badge ${report.status === 'completed' ? 'bg-success' : 
                                           report.status === 'pending' ? 'bg-warning' : 'bg-secondary'}`}>
                              {report.status === 'completed' ? 'Завершен' : 
                               report.status === 'pending' ? 'В ожидании' : report.status}
                            </span>
                          </div>
                        </button>
                      </h2>
                      <div
                        id={`collapse${index}`}
                        className="accordion-collapse collapse"
                        data-bs-parent="#reportsAccordion"
                      >
                        <div className="accordion-body">
                          <p><strong>Дата:</strong> {new Date(report.started_at).toLocaleString('ru-RU')}</p>
                          <p><strong>Статус:</strong> {report.status}</p>
                          {report.notes && <p><strong>Примечания:</strong> {report.notes}</p>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Clear History Button */}
              {reports.length > 0 && (
                <div className="mt-4 d-flex justify-content-end">
                  <button
                    onClick={handleClearHistory}
                    className="btn btn-danger"
                  >
                    Очистить всю историю
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;