import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';

interface Indicator {
  id: number;
  name: string;
  unit: string;
  min_value: number;
  max_value: number;
}

interface IndicatorFormData {
  name: string;
  unit: string;
  min_value: string;
  max_value: string;
  type: 'FLOAT' | 'TEXT';
}

const Admin: React.FC = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('constructor');
  const [indicators, setIndicators] = useState<IndicatorFormData[]>([]);
  const [templateName, setTemplateName] = useState('');
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);

  if (!user?.is_admin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white p-8 rounded-lg shadow">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Доступ запрещен</h2>
          <p className="text-gray-600">У вас нет прав администратора для доступа к этой странице.</p>
        </div>
      </div>
    );
  }

  const handleAddIndicator = () => {
    setIndicators([...indicators, {
      name: '',
      unit: '',
      min_value: '',
      max_value: '',
      type: 'FLOAT'
    }]);
  };

  const handleIndicatorChange = (index: number, field: keyof IndicatorFormData, value: string) => {
    const updatedIndicators = [...indicators];
    updatedIndicators[index] = { ...updatedIndicators[index], [field]: value };
    setIndicators(updatedIndicators);
  };

  const handleRemoveIndicator = (index: number) => {
    const updatedIndicators = [...indicators];
    updatedIndicators.splice(index, 1);
    setIndicators(updatedIndicators);
  };

  const handleCreateTemplate = async () => {
    if (!templateName || indicators.length === 0) {
      alert('Пожалуйста, введите название шаблона и добавьте хотя бы один показатель');
      return;
    }

    try {
      const templateData = {
        name: templateName,
        description: '',
        is_active: true,
        indicators: indicators.map(ind => ({
          name: ind.name,
          unit: ind.unit,
          min_value: parseFloat(ind.min_value),
          max_value: parseFloat(ind.max_value)
        }))
      };

      await api.post('/api/templates/', templateData);
      alert('Шаблон успешно создан!');
      setTemplateName('');
      setIndicators([]);
    } catch (error) {
      console.error('Error creating template:', error);
      alert('Ошибка при создании шаблона');
    }
  };

  const getTemplates = async () => {
    try {
      const response = await api.get('/api/templates/active');
      if (response.data.length > 0) {
        setSelectedTemplateId(response.data[0].id);
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  React.useEffect(() => {
    getTemplates();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-gray-900">WWWAnalys - Админ панель</h1>
              </div>
            </div>
            <div className="flex items-center">
              <span className="mr-4 text-gray-700">
                {user?.email} (ADMIN)
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
            <div className="mb-6">
              <div className="border-b border-gray-200">
                <nav className="-mb-px flex space-x-8">
                  <button
                    onClick={() => setActiveTab('constructor')}
                    className={`${activeTab === 'constructor' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
                  >
                    Конструктор
                  </button>
                  <button
                    onClick={() => setActiveTab('templates')}
                    className={`${activeTab === 'templates' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
                  >
                    Управление шаблонами
                  </button>
                  <button
                    onClick={() => setActiveTab('users')}
                    className={`${activeTab === 'users' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
                  >
                    Пользователи
                  </button>
                </nav>
              </div>
            </div>

            {activeTab === 'constructor' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Конструктор шаблонов</h2>
                
                <div className="mb-6">
                  <label htmlFor="template-name" className="block text-sm font-medium text-gray-700 mb-1">
                    Название шаблона
                  </label>
                  <input
                    type="text"
                    id="template-name"
                    value={templateName}
                    onChange={(e) => setTemplateName(e.target.value)}
                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border"
                    placeholder="Введите название шаблона"
                  />
                </div>

                <div className="mb-6">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-medium text-gray-900">Показатели</h3>
                    <button
                      onClick={handleAddIndicator}
                      className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                    >
                      Добавить показатель
                    </button>
                  </div>

                  {indicators.map((indicator, index) => (
                    <div key={index} className="bg-white p-4 rounded-lg shadow mb-4">
                      <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
                        <div className="md:col-span-2">
                          <label className="block text-sm font-medium text-gray-700 mb-1">Название</label>
                          <input
                            type="text"
                            value={indicator.name}
                            onChange={(e) => handleIndicatorChange(index, 'name', e.target.value)}
                            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border"
                            placeholder="Название показателя"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Тип</label>
                          <select
                            value={indicator.type}
                            onChange={(e) => handleIndicatorChange(index, 'type', e.target.value as 'FLOAT' | 'TEXT')}
                            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border"
                          >
                            <option value="FLOAT">FLOAT</option>
                            <option value="TEXT">TEXT</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Ед. изм.</label>
                          <input
                            type="text"
                            value={indicator.unit}
                            onChange={(e) => handleIndicatorChange(index, 'unit', e.target.value)}
                            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border"
                            placeholder="Единицы измерения"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Мин. значение</label>
                          <input
                            type="number"
                            value={indicator.min_value}
                            onChange={(e) => handleIndicatorChange(index, 'min_value', e.target.value)}
                            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border"
                            placeholder="Мин"
                            step="0.01"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Макс. значение</label>
                          <input
                            type="number"
                            value={indicator.max_value}
                            onChange={(e) => handleIndicatorChange(index, 'max_value', e.target.value)}
                            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border"
                            placeholder="Макс"
                            step="0.01"
                          />
                        </div>
                      </div>
                      <div className="mt-2 flex justify-end">
                        <button
                          onClick={() => handleRemoveIndicator(index)}
                          className="text-red-600 hover:text-red-800 text-sm"
                        >
                          Удалить
                        </button>
                      </div>
                    </div>
                  ))}

                  <button
                    onClick={handleCreateTemplate}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Создать шаблон
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'templates' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Управление шаблонами</h2>
                <p className="text-gray-600 mb-4">
                  Управление шаблонами анализов, создание и редактирование
                </p>
                <div className="bg-white p-6 rounded-lg shadow">
                  <p className="text-gray-600">Функционал управления шаблонами будет реализован в следующей версии</p>
                </div>
              </div>
            )}

            {activeTab === 'users' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Управление пользователями</h2>
                <p className="text-gray-600 mb-4">
                  Добавление и управление пользователями системы
                </p>
                <div className="bg-white p-6 rounded-lg shadow">
                  <p className="text-gray-600">Функционал управления пользователями будет реализован в следующей версии</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Admin;