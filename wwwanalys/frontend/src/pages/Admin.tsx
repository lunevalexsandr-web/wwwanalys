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
      <div className="min-h-screen d-flex align-items-center justify-content-center bg-light">
        <div className="max-w-md w-full bg-white p-8 rounded-lg shadow">
          <h2 className="h3 text-danger mb-4">Доступ запрещен</h2>
          <p className="text-muted">У вас нет прав администратора для доступа к этой странице.</p>
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
    <div className="min-h-screen bg-light">
      <header className="bg-white shadow-sm">
        <div className="container-fluid">
          <div className="d-flex justify-content-between align-items-center h-16">
            <div className="flex-shrink-0 d-flex align-items-center">
              <h1 className="h4 mb-0 text-dark">WWWAnalys - Админ панель</h1>
            </div>
            <div className="d-flex align-items-center">
              <span className="me-3 text-dark">
                {user?.email} (ADMIN)
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
          <div className="mb-4">
            <nav className="nav nav-tabs">
              <button
                onClick={() => { setActiveTab('constructor'); handleCancelEdit(); }}
                className={`nav-link ${activeTab === 'constructor' ? 'active' : ''}`}
              >
                {editingTemplate ? 'Редактирование шаблона' : 'Конструктор'}
              </button>
              <button
                onClick={() => { setActiveTab('templates'); handleCancelEdit(); }}
                className={`nav-link ${activeTab === 'templates' ? 'active' : ''}`}
              >
                Управление шаблонами
              </button>
              <button
                onClick={() => { setActiveTab('users'); handleCancelEdit(); }}
                className={`nav-link ${activeTab === 'users' ? 'active' : ''}`}
              >
                Пользователи
              </button>
            </nav>
          </div>

          {activeTab === 'constructor' && (
            <div>
              <h2 className="h3 mb-3">
                {editingTemplate ? 'Редактирование шаблона' : 'Конструктор шаблонов'}
              </h2>
              
              <div className="mb-4">
                <label htmlFor="template-name" className="form-label">
                  Название шаблона
                </label>
                <input
                  type="text"
                  id="template-name"
                  className="form-control"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  placeholder="Введите название шаблона"
                />
              </div>

              <div className="mb-4">
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <h3 className="h5 mb-0">Показатели</h3>
                  <button
                    onClick={handleAddIndicator}
                    className="btn btn-success"
                  >
                    Добавить показатель
                  </button>
                </div>

                {indicators.map((indicator, index) => (
                  <div key={index} className="card mb-3">
                    <div className="card-body">
                      <div className="row g-3">
                        <div className="col-md-4">
                          <label className="form-label">Название</label>
                          <input
                            type="text"
                            className="form-control"
                            value={indicator.name}
                            onChange={(e) => handleIndicatorChange(index, 'name', e.target.value)}
                            placeholder="Название показателя"
                          />
                        </div>
                        <div className="col-md-2">
                          <label className="form-label">Тип</label>
                          <select
                            className="form-select"
                            value={indicator.data_type}
                            onChange={(e) => handleIndicatorChange(index, 'data_type', e.target.value as 'number' | 'text' | 'select')}
                          >
                            <option value="number">Число</option>
                            <option value="text">Текст</option>
                            <option value="select">Список</option>
                          </select>
                        </div>
                        <div className="col-md-2">
                          <label className="form-label">Ед. изм.</label>
                          <input
                            type="text"
                            className="form-control"
                            value={indicator.unit}
                            onChange={(e) => handleIndicatorChange(index, 'unit', e.target.value)}
                            placeholder="Единицы измерения"
                          />
                        </div>
                        <div className="col-md-2">
                          <label className="form-label">Мин. значение</label>
                          <input
                            type="number"
                            className="form-control"
                            value={indicator.min_value}
                            onChange={(e) => handleIndicatorChange(index, 'min_value', e.target.value)}
                            placeholder="Мин"
                            step="0.01"
                          />
                        </div>
                        <div className="col-md-2">
                          <label className="form-label">Макс. значение</label>
                          <input
                            type="number"
                            className="form-control"
                            value={indicator.max_value}
                            onChange={(e) => handleIndicatorChange(index, 'max_value', e.target.value)}
                            placeholder="Макс"
                            step="0.01"
                          />
                        </div>
                      </div>
                      
                      {indicator.data_type === 'select' && (
                        <div className="row mt-3">
                          <div className="col-12">
                            <label className="form-label">Варианты (через запятую)</label>
                            <input
                              type="text"
                              className="form-control"
                              value={indicator.options}
                              onChange={(e) => handleIndicatorChange(index, 'options', e.target.value)}
                              placeholder="Вариант 1, Вариант 2, Вариант 3"
                            />
                          </div>
                        </div>
                      )}
                      
                      <div className="mt-3 d-flex justify-content-end">
                        <button
                          onClick={() => handleRemoveIndicator(index)}
                          className="btn btn-sm btn-danger"
                        >
                          Удалить
                        </button>
                      </div>
                    </div>
                  </div>
                ))}

                <div className="d-flex gap-2">
                  {editingTemplate ? (
                    <>
                      <button
                        onClick={handleUpdateTemplate}
                        className="btn btn-primary"
                      >
                        Сохранить изменения
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        className="btn btn-secondary"
                      >
                        Отмена
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={handleCreateTemplate}
                      className="btn btn-primary"
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
              <h2 className="h3 mb-3">Управление шаблонами</h2>
              <p className="text-muted mb-3">
                Список всех шаблонов анализов с возможностью редактирования и удаления
              </p>
              
              {templates.length === 0 ? (
                <div className="card">
                  <div className="card-body">
                    <p className="text-muted">Нет созданных шаблонов</p>
                  </div>
                </div>
              ) : (
                <div className="accordion" id="templatesAccordion">
                  {templates.map((template) => (
                    <div key={template.id} className="accordion-item">
                      <h2 className="accordion-header">
                        <button
                          className="accordion-button"
                          type="button"
                          data-bs-toggle="collapse"
                          data-bs-target={`#template${template.id}`}
                        >
                          <div className="d-flex justify-content-between align-items-center w-100">
                            <div>
                              <h5 className="mb-1">{template.name}</h5>
                              <p className="mb-0 text-muted">
                                Показателей: {template.indicators.length} | Создан: {new Date(template.created_at).toLocaleDateString('ru-RU')}
                              </p>
                            </div>
                            <div className="d-flex align-items-center gap-2">
                              <span className={`badge ${template.is_active ? 'bg-success' : 'bg-danger'}`}>
                                {template.is_active ? 'Активен' : 'Неактивен'}
                              </span>
                            </div>
                          </div>
                        </button>
                      </h2>
                      <div
                        id={`template${template.id}`}
                        className="accordion-collapse collapse"
                        data-bs-parent="#templatesAccordion"
                      >
                        <div className="accordion-body">
                          <div className="d-flex gap-2 mb-3">
                            <button
                              onClick={() => handleToggleActive(template)}
                              className={`btn btn-sm ${template.is_active ? 'btn-warning' : 'btn-success'}`}
                            >
                              {template.is_active ? 'Деактивировать' : 'Активировать'}
                            </button>
                            <button
                              onClick={() => handleEditTemplate(template)}
                              className="btn btn-sm btn-primary"
                            >
                              Редактировать
                            </button>
                            <button
                              onClick={() => handleDeleteTemplate(template.id)}
                              className="btn btn-sm btn-danger"
                            >
                              Удалить
                            </button>
                          </div>
                          
                          {template.indicators.length > 0 && (
                            <div>
                              <h6 className="mb-2">Показатели:</h6>
                              <div className="row g-2">
                                {template.indicators.map((ind) => (
                                  <div key={ind.id} className="col-md-4 col-lg-3">
                                    <div className="badge bg-light text-dark p-2 d-flex justify-content-between align-items-center">
                                      <span>{ind.name}</span>
                                      <small className="text-muted">({ind.unit})</small>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'users' && (
            <div>
              <h2 className="h3 mb-3">Управление пользователями</h2>
              <p className="text-muted mb-3">
                Список всех пользователей системы
              </p>
              
              {/* Add User Form */}
              <div className="card mb-4">
                <div className="card-body">
                  <h3 className="h5 mb-3">
                    {editingUser ? 'Редактирование пользователя' : 'Добавить нового пользователя'}
                  </h3>
                  <div className="row g-3">
                    <div className="col-md-4">
                      <label className="form-label">Имя пользователя *</label>
                      <input
                        type="text"
                        className="form-control"
                        value={userForm.username}
                        onChange={(e) => setUserForm({...userForm, username: e.target.value})}
                        placeholder="Введите имя"
                      />
                    </div>
                    <div className="col-md-4">
                      <label className="form-label">Email *</label>
                      <input
                        type="email"
                        className="form-control"
                        value={userForm.email}
                        onChange={(e) => setUserForm({...userForm, email: e.target.value})}
                        placeholder="Введите email"
                      />
                    </div>
                    <div className="col-md-4">
                      <label className="form-label">
                        Пароль {editingUser ? '(оставьте пустым, чтобы не менять)' : '*'}
                      </label>
                      <input
                        type="password"
                        className="form-control"
                        value={userForm.password}
                        onChange={(e) => setUserForm({...userForm, password: e.target.value})}
                        placeholder="Введите пароль"
                      />
                    </div>
                  </div>
                  <div className="row mt-3">
                    <div className="col-md-6">
                      <div className="form-check">
                        <input
                          className="form-check-input"
                          type="checkbox"
                          checked={userForm.is_admin}
                          onChange={(e) => setUserForm({...userForm, is_admin: e.target.checked})}
                        />
                        <label className="form-check-label">
                          Администратор
                        </label>
                      </div>
                    </div>
                    <div className="col-md-6">
                      <div className="form-check">
                        <input
                          className="form-check-input"
                          type="checkbox"
                          checked={userForm.is_active}
                          onChange={(e) => setUserForm({...userForm, is_active: e.target.checked})}
                        />
                        <label className="form-check-label">
                          Активен
                        </label>
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 d-flex gap-2">
                    <button
                      onClick={handleSaveUser}
                      className="btn btn-primary"
                    >
                      {editingUser ? 'Сохранить изменения' : 'Создать пользователя'}
                    </button>
                    {editingUser && (
                      <button
                        onClick={handleCloseUserModal}
                        className="btn btn-secondary"
                      >
                        Отмена
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Users List */}
              {users.length === 0 ? (
                <div className="card">
                  <div className="card-body">
                    <p className="text-muted">Нет пользователей</p>
                  </div>
                </div>
              ) : (
                <div className="card">
                  <div className="card-body">
                    <div className="table-responsive">
                      <table className="table table-hover">
                        <thead>
                          <tr>
                            <th>Пользователь</th>
                            <th>Email</th>
                            <th>Роль</th>
                            <th>Статус</th>
                            <th className="text-end">Действия</th>
                          </tr>
                        </thead>
                        <tbody>
                          {users.map((userItem) => (
                            <tr key={userItem.id}>
                              <td>
                                <div className="fw-bold">{userItem.username}</div>
                              </td>
                              <td>{userItem.email}</td>
                              <td>
                                <span className={`badge ${userItem.is_admin ? 'bg-purple' : 'bg-secondary'}`}>
                                  {userItem.is_admin ? 'Админ' : 'Пользователь'}
                                </span>
                              </td>
                              <td>
                                <span className={`badge ${userItem.is_active ? 'bg-success' : 'bg-danger'}`}>
                                  {userItem.is_active ? 'Активен' : 'Неактивен'}
                                </span>
                              </td>
                              <td className="text-end">
                                <button
                                  onClick={() => handleOpenUserModal(userItem)}
                                  className="btn btn-sm btn-outline-primary me-1"
                                >
                                  Редактировать
                                </button>
                                <button
                                  onClick={() => handleToggleUserActive(userItem)}
                                  className={`btn btn-sm me-1 ${userItem.is_active ? 'btn-warning' : 'btn-success'}`}
                                >
                                  {userItem.is_active ? 'Деактивировать' : 'Активировать'}
                                </button>
                                <button
                                  onClick={() => handleDeleteUser(userItem.id)}
                                  className="btn btn-sm btn-outline-danger"
                                >
                                  Удалить
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Admin;