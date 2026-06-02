import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';

interface Indicator {
  id: number;
  name: string;
  unit: string;
  min_value: number | null;
  max_value: number | null;
  data_type: 'number' | 'text' | 'select';
  options: string[] | null;
}

interface IndicatorFormData {
  name: string;
  unit: string;
  min_value: string;
  max_value: string;
  data_type: 'number' | 'text' | 'select';
  options: string;  // JSON строка с вариантами для select
}

interface Template {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  indicators: Indicator[];
  created_at: string;
}

interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
}

const Admin: React.FC = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('constructor');
  const [indicators, setIndicators] = useState<IndicatorFormData[]>([]);
  const [templateName, setTemplateName] = useState('');
  const [templates, setTemplates] = useState<Template[]>([]);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  
  // Users state
  const [users, setUsers] = useState<User[]>([]);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [userForm, setUserForm] = useState({
    username: '',
    email: '',
    password: '',
    is_active: true,
    is_admin: false
  });

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

  useEffect(() => {
    fetchTemplates();
    fetchUsers();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await api.get('/api/templates/');
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await api.get('/auth/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const handleAddIndicator = () => {
    setIndicators([...indicators, {
      name: '',
      unit: '',
      min_value: '',
      max_value: '',
      data_type: 'number',
      options: ''
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
        indicators: indicators.map(ind => {
          const indicator: any = {
            name: ind.name,
            unit: ind.unit,
            data_type: ind.data_type
          };
          
          // Добавляем min/max только для числового типа
          if (ind.data_type === 'number') {
            indicator.min_value = ind.min_value ? parseFloat(ind.min_value) : null;
            indicator.max_value = ind.max_value ? parseFloat(ind.max_value) : null;
          }
          
          // Добавляем options для select типа
          if (ind.data_type === 'select' && ind.options) {
            indicator.options = ind.options.split(',').map((o: string) => o.trim()).filter((o: string) => o);
          }
          
          return indicator;
        })
      };

      await api.post('/api/templates/', templateData);
      alert('Шаблон успешно создан!');
      setTemplateName('');
      setIndicators([]);
      fetchTemplates();
    } catch (error) {
      console.error('Error creating template:', error);
      alert('Ошибка при создании шаблона');
    }
  };

  const handleEditTemplate = (template: Template) => {
    setEditingTemplate(template);
    setTemplateName(template.name);
    setIndicators(template.indicators.map(ind => ({
      name: ind.name,
      unit: ind.unit,
      min_value: ind.min_value?.toString() || '',
      max_value: ind.max_value?.toString() || '',
      data_type: ind.data_type,
      options: ind.options?.join(', ') || ''
    })));
    setActiveTab('constructor');
  };

  const handleUpdateTemplate = async () => {
    if (!editingTemplate || !templateName) {
      alert('Пожалуйста, заполните все поля');
      return;
    }

    try {
      const templateData: any = {
        name: templateName,
        description: editingTemplate.description,
        is_active: editingTemplate.is_active
      };
      
      if (indicators.length > 0) {
        templateData.indicators = indicators.map(ind => {
          const indicator: any = {
            name: ind.name,
            unit: ind.unit,
            data_type: ind.data_type
          };
          
          // Добавляем min/max только для числового типа
          if (ind.data_type === 'number') {
            indicator.min_value = ind.min_value ? parseFloat(ind.min_value) : null;
            indicator.max_value = ind.max_value ? parseFloat(ind.max_value) : null;
          }
          
          // Добавляем options для select типа
          if (ind.data_type === 'select' && ind.options) {
            indicator.options = ind.options.split(',').map((o: string) => o.trim()).filter((o: string) => o);
          }
          
          return indicator;
        });
      }

      await api.put(`/api/templates/${editingTemplate.id}`, templateData);
      alert('Шаблон успешно обновлен!');
      setEditingTemplate(null);
      setTemplateName('');
      setIndicators([]);
      fetchTemplates();
      setActiveTab('templates');
    } catch (error) {
      console.error('Error updating template:', error);
      alert('Ошибка при обновлении шаблона');
    }
  };

  const handleDeleteTemplate = async (templateId: number) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот шаблон?')) {
      return;
    }

    try {
      await api.delete(`/api/templates/${templateId}`);
      alert('Шаблон успешно удален!');
      fetchTemplates();
    } catch (error) {
      console.error('Error deleting template:', error);
      alert('Ошибка при удалении шаблона');
    }
  };

  const handleToggleActive = async (template: Template) => {
    try {
      await api.put(`/api/templates/${template.id}`, {
        name: template.name,
        description: template.description,
        is_active: !template.is_active
      });
      fetchTemplates();
    } catch (error) {
      console.error('Error toggling template status:', error);
      alert('Ошибка при изменении статуса шаблона');
    }
  };

  const handleCancelEdit = () => {
    setEditingTemplate(null);
    setTemplateName('');
    setIndicators([]);
  };

  // User management functions
  const handleOpenUserModal = (userToEdit?: User) => {
    if (userToEdit) {
      setEditingUser(userToEdit);
      setUserForm({
        username: userToEdit.username,
        email: userToEdit.email,
        password: '',
        is_active: userToEdit.is_active,
        is_admin: userToEdit.is_admin
      });
    } else {
      setEditingUser(null);
      setUserForm({
        username: '',
        email: '',
        password: '',
        is_active: true,
        is_admin: false
      });
    }
  };

  const handleCloseUserModal = () => {
    setEditingUser(null);
    setUserForm({
      username: '',
      email: '',
      password: '',
      is_active: true,
      is_admin: false
    });
  };

  const handleSaveUser = async () => {
    if (!userForm.username || !userForm.email) {
      alert('Пожалуйста, заполните все обязательные поля');
      return;
    }

    if (!editingUser && !userForm.password) {
      alert('Пожалуйста, введите пароль для нового пользователя');
      return;
    }

    try {
      if (editingUser) {
        const updateData: any = {
          username: userForm.username,
          email: userForm.email,
          is_active: userForm.is_active,
          is_admin: userForm.is_admin
        };
        if (userForm.password) {
          updateData.password = userForm.password;
        }
        await api.put(`/auth/users/${editingUser.id}`, updateData);
        alert('Пользователь успешно обновлен!');
      } else {
        await api.post('/auth/register', {
          username: userForm.username,
          email: userForm.email,
          password: userForm.password,
          is_active: userForm.is_active,
          is_admin: userForm.is_admin
        });
        alert('Пользователь успешно создан!');
      }
      handleCloseUserModal();
      fetchUsers();
    } catch (error) {
      console.error('Error saving user:', error);
      alert('Ошибка при сохранении пользователя');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!window.confirm('Вы уверены, что хотите удалить этого пользователя?')) {
      return;
    }

    try {
      await api.delete(`/auth/users/${userId}`);
      alert('Пользователь успешно удален!');
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      alert('Ошибка при удалении пользователя');
    }
  };

  const handleToggleUserActive = async (userToToggle: User) => {
    try {
      await api.put(`/auth/users/${userToToggle.id}`, {
        is_active: !userToToggle.is_active
      });
      fetchUsers();
    } catch (error) {
      console.error('Error toggling user status:', error);
      alert('Ошибка при изменении статуса пользователя');
    }
  };

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
                    onClick={() => { setActiveTab('constructor'); handleCancelEdit(); }}
                    className={`${activeTab === 'constructor' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
                  >
                    {editingTemplate ? 'Редактирование шаблона' : 'Конструктор'}
                  </button>
                  <button
                    onClick={() => { setActiveTab('templates'); handleCancelEdit(); }}
                    className={`${activeTab === 'templates' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
                  >
                    Управление шаблонами
                  </button>
                  <button
                    onClick={() => { setActiveTab('users'); handleCancelEdit(); }}
                    className={`${activeTab === 'users' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
                  >
                    Пользователи
                  </button>
                </nav>
              </div>
            </div>

            {activeTab === 'constructor' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  {editingTemplate ? 'Редактирование шаблона' : 'Конструктор шаблонов'}
                </h2>
                
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
                            value={indicator.data_type}
                            onChange={(e) => handleIndicatorChange(index, 'data_type', e.target.value as 'number' | 'text' | 'select')}
                            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border"
                          >
                            <option value="number">Число</option>
                            <option value="text">Текст</option>
                            <option value="select">Список</option>
                          </select>
                        </div>
                        {indicator.data_type === 'select' && (
                          <div className="md:col-span-6">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Варианты (через запятую)</label>
                            <input
                              type="text"
                              value={indicator.options}
                              onChange={(e) => handleIndicatorChange(index, 'options', e.target.value)}
                              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border"
                              placeholder="Вариант 1, Вариант 2, Вариант 3"
                            />
                          </div>
                        )}
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

                  <div className="flex gap-4">
                    {editingTemplate ? (
                      <>
                        <button
                          onClick={handleUpdateTemplate}
                          className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                          Сохранить изменения
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                        >
                          Отмена
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={handleCreateTemplate}
                        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        Создать шаблон
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'templates' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Управление шаблонами</h2>
                <p className="text-gray-600 mb-4">
                  Список всех шаблонов анализов с возможностью редактирования и удаления
                </p>
                
                {templates.length === 0 ? (
                  <div className="bg-white p-6 rounded-lg shadow">
                    <p className="text-gray-600">Нет созданных шаблонов</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {templates.map((template) => (
                      <div key={template.id} className="bg-white p-6 rounded-lg shadow">
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="flex items-center gap-2">
                              <h3 className="text-lg font-medium text-gray-900">{template.name}</h3>
                              <span className={`px-2 py-1 text-xs rounded-full ${template.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                {template.is_active ? 'Активен' : 'Неактивен'}
                              </span>
                            </div>
                            <p className="text-sm text-gray-500 mt-1">
                              Показателей: {template.indicators.length}
                            </p>
                            <p className="text-sm text-gray-500">
                              Создан: {new Date(template.created_at).toLocaleDateString('ru-RU')}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleToggleActive(template)}
                              className={`px-3 py-1 text-sm rounded-md ${template.is_active ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200' : 'bg-green-100 text-green-800 hover:bg-green-200'}`}
                            >
                              {template.is_active ? 'Деактивировать' : 'Активировать'}
                            </button>
                            <button
                              onClick={() => handleEditTemplate(template)}
                              className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-md hover:bg-blue-200"
                            >
                              Редактировать
                            </button>
                            <button
                              onClick={() => handleDeleteTemplate(template.id)}
                              className="px-3 py-1 text-sm bg-red-100 text-red-800 rounded-md hover:bg-red-200"
                            >
                              Удалить
                            </button>
                          </div>
                        </div>
                        
                        {template.indicators.length > 0 && (
                          <div className="mt-4 border-t pt-4">
                            <h4 className="text-sm font-medium text-gray-700 mb-2">Показатели:</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                              {template.indicators.map((ind) => (
                                <div key={ind.id} className="text-sm bg-gray-50 p-2 rounded">
                                  <span className="font-medium">{ind.name}</span>
                                  <span className="text-gray-500"> ({ind.unit})</span>
                                  <span className="text-gray-400 text-xs ml-1">
                                    [{ind.min_value} - {ind.max_value}]
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'users' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Управление пользователями</h2>
                <p className="text-gray-600 mb-4">
                  Список всех пользователей системы
                </p>
                
                {/* Add User Form */}
                <div className="bg-white p-6 rounded-lg shadow mb-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">
                    {editingUser ? 'Редактирование пользователя' : 'Добавить нового пользователя'}
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Имя пользователя *
                      </label>
                      <input
                        type="text"
                        value={userForm.username}
                        onChange={(e) => setUserForm({...userForm, username: e.target.value})}
                        className="w-full border border-gray-300 rounded-md p-3 text-base focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="Введите имя"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Email *
                      </label>
                      <input
                        type="email"
                        value={userForm.email}
                        onChange={(e) => setUserForm({...userForm, email: e.target.value})}
                        className="w-full border border-gray-300 rounded-md p-3 text-base focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="Введите email"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Пароль {editingUser ? '(оставьте пустым, чтобы не менять)' : '*'}
                      </label>
                      <input
                        type="password"
                        value={userForm.password}
                        onChange={(e) => setUserForm({...userForm, password: e.target.value})}
                        className="w-full border border-gray-300 rounded-md p-3 text-base focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="Введите пароль"
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-6 mt-4">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={userForm.is_admin}
                        onChange={(e) => setUserForm({...userForm, is_admin: e.target.checked})}
                        className="h-5 w-5 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700">Администратор</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={userForm.is_active}
                        onChange={(e) => setUserForm({...userForm, is_active: e.target.checked})}
                        className="h-5 w-5 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700">Активен</span>
                    </label>
                  </div>
                  <div className="mt-4 flex gap-2">
                    <button
                      onClick={handleSaveUser}
                      className="px-6 py-3 bg-indigo-600 text-white rounded-md text-base font-medium hover:bg-indigo-700"
                    >
                      {editingUser ? 'Сохранить изменения' : 'Создать пользователя'}
                    </button>
                    {editingUser && (
                      <button
                        onClick={handleCloseUserModal}
                        className="px-6 py-3 bg-gray-200 text-gray-700 rounded-md text-base font-medium hover:bg-gray-300"
                      >
                        Отмена
                      </button>
                    )}
                  </div>
                </div>

                {/* Users List */}
                {users.length === 0 ? (
                  <div className="bg-white p-6 rounded-lg shadow">
                    <p className="text-gray-600">Нет пользователей</p>
                  </div>
                ) : (
                  <div className="bg-white rounded-lg shadow overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Пользователь
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Email
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Роль
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Статус
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Действия
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {users.map((userItem) => (
                          <tr key={userItem.id}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">{userItem.username}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-500">{userItem.email}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 text-xs rounded-full ${userItem.is_admin ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'}`}>
                                {userItem.is_admin ? 'Админ' : 'Пользователь'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 text-xs rounded-full ${userItem.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                {userItem.is_active ? 'Активен' : 'Неактивен'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <button
                                onClick={() => handleOpenUserModal(userItem)}
                                className="text-indigo-600 hover:text-indigo-900 mr-3"
                              >
                                Редактировать
                              </button>
                              <button
                                onClick={() => handleToggleUserActive(userItem)}
                                className={`${userItem.is_active ? 'text-yellow-600 hover:text-yellow-900' : 'text-green-600 hover:text-green-900'} mr-3`}
                              >
                                {userItem.is_active ? 'Деактивировать' : 'Активировать'}
                              </button>
                              <button
                                onClick={() => handleDeleteUser(userItem.id)}
                                className="text-red-600 hover:text-red-900"
                              >
                                Удалить
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Admin;