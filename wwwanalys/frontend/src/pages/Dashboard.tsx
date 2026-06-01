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

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [templates, setTemplates] = useState<AnalysisType[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<AnalysisType | null>(null);
  const [batchNumber, setBatchNumber] = useState('');
  const [indicatorValues, setIndicatorValues] = useState<IndicatorValue[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchTemplates();
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
    } catch (error) {
      console.error('Error submitting report:', error);
      alert('Ошибка при отправке отчета');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-gray-900">WWWAnalys</h1>
              </div>
              <nav className="ml-10 flex space-x-8">
                {user?.is_admin && (
                  <a
                    href="/admin"
                    className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Админ-панель
                  </a>
                )}
              </nav>
            </div>
            <div className="flex items-center">
              <span className="mr-4 text-gray-700">
                {user?.email} ({user?.is_admin ? 'ADMIN' : 'USER'})
              </span>
              <button
                onClick={logout}
                className="ml-4 px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
              >
                Выйти
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-4 border-dashed border-gray-200 rounded-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Панель внесения анализов</h2>
            <p className="text-gray-600 mb-6">
              Выберите шаблон анализа, заполните показатели и отправьте отчет
            </p>

            {/* Template Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Выберите шаблон анализа
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {templates.map((template) => (
                  <button
                    key={template.id}
                    onClick={() => handleTemplateSelect(template)}
                    className={`p-4 rounded-lg border-2 text-left transition-colors ${
                      selectedTemplate?.id === template.id
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <h3 className="font-medium text-gray-900">{template.name}</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {template.indicators.length} показателей
                    </p>
                  </button>
                ))}
              </div>
            </div>

            {selectedTemplate && (
              <div>
                {/* Batch Number */}
                <div className="mb-6">
                  <label htmlFor="batch-number" className="block text-sm font-medium text-gray-700 mb-2">
                    Номер партии
                  </label>
                  <input
                    type="text"
                    id="batch-number"
                    value={batchNumber}
                    onChange={(e) => setBatchNumber(e.target.value)}
                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border"
                    placeholder="Введите номер партии"
                  />
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit}>
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">
                      Показатели для анализа: {selectedTemplate.name}
                    </h3>
                    
                    <div className="space-y-4">
                      {selectedTemplate.indicators.map((indicator) => {
                        const indicatorValue = indicatorValues.find(v => v.indicator_id === indicator.id);
                        const isOutOfRange = indicatorValue && 
                            indicator.min_value !== undefined && 
                            indicator.max_value !== undefined &&
                            !isNaN(parseFloat(indicatorValue.value as string)) &&
                            (parseFloat(indicatorValue.value as string) < indicator.min_value || 
                             parseFloat(indicatorValue.value as string) > indicator.max_value);
                        
                        return (
                          <div key={indicator.id} className="bg-white p-4 rounded-lg shadow">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                              <div className="md:col-span-1">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                  {indicator.name}
                                </label>
                                <p className="text-sm text-gray-500">{indicator.unit}</p>
                                {indicator.min_value !== undefined && indicator.max_value !== undefined && (
                                  <p className="text-xs text-gray-500 mt-1">
                                    Норма: {indicator.min_value} - {indicator.max_value}
                                  </p>
                                )}
                              </div>
                              <div className="md:col-span-2">
                                {indicatorValue && (
                                  <input
                                    type={indicator.type === 'FLOAT' ? 'number' : 'text'}
                                    value={indicatorValue.value}
                                    onChange={(e) => handleIndicatorValueChange(indicator.id, e.target.value)}
                                    step={indicator.type === 'FLOAT' ? '0.01' : undefined}
                                    className={`shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border rounded-md p-2 ${
                                      isOutOfRange 
                                        ? 'border-red-300 bg-red-50' 
                                        : 'border-gray-300'
                                    }`}
                                    placeholder={`Введите значение (${indicator.type})`}
                                  />
                                )}
                                {isOutOfRange && (
                                  <p className="text-xs text-red-600 mt-1">
                                    Значение вне нормы!
                                  </p>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="bg-indigo-600 text-white py-2 px-6 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                      {isSubmitting ? 'Отправка...' : 'Отправить отчет'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {!templates.length && (
              <div className="text-center py-8">
                <p className="text-gray-600">Нет доступных шаблонов анализа</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;