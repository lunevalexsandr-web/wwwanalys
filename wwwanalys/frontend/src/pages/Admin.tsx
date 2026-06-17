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
import type { AnalysisType, User as UserType, IndicatorLibrary, LibraryIndicatorRef, PresetListItem, Preset } from '../types';

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
  const [templateLibIndicators, setTemplateLibIndicators] = useState<LibraryIndicatorRef[]>([]);

  // Preview template state
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewTemplate, setPreviewTemplate] = useState<AnalysisType | null>(null);

  // Copy template state
  const [showCopyModal, setShowCopyModal] = useState(false);
  const [copyTemplateId, setCopyTemplateId] = useState<number | null>(null);
  const [copyTemplateName, setCopyTemplateName] = useState('');

  // Create from preset state
  const [showCreateFromPresetModal, setShowCreateFromPresetModal] = useState(false);
  const [newTemplateName, setNewTemplateName] = useState('');

  // Library state
  const [libIndicators, setLibIndicators] = useState<IndicatorLibrary[]>([]);
  const [showLibModal, setShowLibModal] = useState(false);
  const [editingLibIndicator, setEditingLibIndicator] = useState<IndicatorLibrary | null>(null);
  const [libIndicatorName, setLibIndicatorName] = useState('');
  const [libIndicatorUnit, setLibIndicatorUnit] = useState('');
  const [libIndicatorType, setLibIndicatorType] = useState<'number' | 'text' | 'select'>('number');
  const [libIndicatorOptions, setLibIndicatorOptions] = useState('');
  const [libIndicatorDescription, setLibIndicatorDescription] = useState('');
  const [libIndicatorCategory, setLibIndicatorCategory] = useState('');
  const [libIndicatorRequired, setLibIndicatorRequired] = useState(false);
  const [libIndicatorDefaultValue, setLibIndicatorDefaultValue] = useState('');

  // Select from library state
  const [showSelectLibModal, setShowSelectLibModal] = useState(false);
  const [selectedLibIndicators, setSelectedLibIndicators] = useState<number[]>([]);
  const [libIndicatorNorms, setLibIndicatorNorms] = useState<Record<number, { min: number | null; max: number | null }>>({});

  // Library search & filter state
  const [libSearch, setLibSearch] = useState('');
  const [libFilterCategory, setLibFilterCategory] = useState('');
  const [libFilterType, setLibFilterType] = useState('');
  const [libIsSearching, setLibIsSearching] = useState(false);
  const [libDebounceTimer, setLibDebounceTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  // Presets state
  const [presets, setPresets] = useState<PresetListItem[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<number | null>(null);
  const [presetDetail, setPresetDetail] = useState<Preset | null>(null);

  // 1C Integration state
  const [show1CModal, setShow1CModal] = useState(false);
  const [is1CConnecting, setIs1CConnecting] = useState(false);
  const [is1CImporting, setIs1CImporting] = useState(false);
  const [connection1CStatus, setConnection1CStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [connection1CMessage, setConnection1CMessage] = useState('');
  const [import1CResult, setImport1CResult] = useState<any>(null);
  const [c1CBaseUrl, setC1CBaseUrl] = useState('');
  const [c1CApiKey, setC1CApiKey] = useState('');
  const [c1CUsername, setC1CUsername] = useState('');
  const [c1CPassword, setC1CPassword] = useState('');

  // User modal state
  const [showUserModal, setShowUserModal] = useState(false);
  const [editingUser, setEditingUser] = useState<UserType | null>(null);
  const [userUsername, setUserUsername] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [userPassword, setUserPassword] = useState('');
  const [userConfirmPassword, setUserConfirmPassword] = useState('');
  const [userIsAdmin, setUserIsAdmin] = useState(false);
  const [userIsActive, setUserIsActive] = useState(true);
  const [userFormErrors, setUserFormErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchTemplates();
    fetchUsers();
    fetchLibraryIndicators();
    fetchPresets();
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

  const fetchLibraryIndicators = async (search?: string, category?: string, dataType?: string) => {
    setLibIsSearching(true);
    try {
      const params: any = {};
      if (search) params.search = search;
      if (category) params.category = category;
      if (dataType) params.data_type = dataType;
      const response = await api.get('/api/indicators/library', { params });
      setLibIndicators(response.data);
    } catch (error) {
      console.error('Error fetching library indicators:', error);
      showToast('Ошибка при загрузке справочника показателей', 'danger');
    } finally {
      setLibIsSearching(false);
    }
  };

  // Debounced search for library
  const handleLibSearchChange = (value: string) => {
    setLibSearch(value);
    if (libDebounceTimer) clearTimeout(libDebounceTimer);
    const timer = setTimeout(() => {
      fetchLibraryIndicators(value || undefined, libFilterCategory || undefined, libFilterType || undefined);
    }, 300);
    setLibDebounceTimer(timer);
  };

  const handleLibFilterChange = (field: 'category' | 'type', value: string) => {
    if (field === 'category') setLibFilterCategory(value);
    else setLibFilterType(value);
    fetchLibraryIndicators(libSearch || undefined, field === 'category' ? (value || undefined) : (libFilterCategory || undefined), field === 'type' ? (value || undefined) : (libFilterType || undefined));
  };

  const fetchPresets = async () => {
    try {
      const response = await api.get('/api/presets/');
      setPresets(response.data);
    } catch (error) {
      console.error('Error fetching presets:', error);
    }
  };

  const handleTemplateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!templateName.trim()) {
      showToast('Название шаблона обязательно', 'warning');
      return;
    }

    try {
      const templateData: any = {
        name: templateName,
        description: templateDescription,
        is_active: templateActive,
      };

      // Добавляем показатели из библиотеки
      if (templateLibIndicators && templateLibIndicators.length > 0) {
        templateData.library_indicators = templateLibIndicators.map(ref => ({
          indicator_id: ref.indicator_id,
          min_value: ref.min_value,
          max_value: ref.max_value,
          sort_order: ref.sort_order
        }));
      }

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

  const handleCopyTemplate = async () => {
    if (!copyTemplateId || !copyTemplateName.trim()) {
      showToast('Введите название для копии', 'warning');
      return;
    }

    try {
      await api.post(`/api/templates/${copyTemplateId}/copy`, {
        new_name: copyTemplateName,
      });
      showToast('Шаблон скопирован успешно', 'success');
      setShowCopyModal(false);
      setCopyTemplateName('');
      fetchTemplates();
    } catch (error) {
      console.error('Error copying template:', error);
      showToast('Ошибка при копировании шаблона', 'danger');
    }
  };

  const handleCreateFromPreset = async () => {
    if (!selectedPresetId || !newTemplateName.trim()) {
      showToast('Выберите пресет и введите название', 'warning');
      return;
    }

    try {
      await api.post('/api/templates/from-preset', {
        preset_id: selectedPresetId,
        template_name: newTemplateName,
      });
      showToast('Шаблон создан из пресета', 'success');
      setShowCreateFromPresetModal(false);
      setNewTemplateName('');
      setSelectedPresetId(null);
      setPresetDetail(null);
      fetchTemplates();
    } catch (error) {
      console.error('Error creating from preset:', error);
      showToast('Ошибка при создании шаблона из пресета', 'danger');
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
    
    // Конвертируем template_indicators в LibraryIndicatorRef
    const libRefs: LibraryIndicatorRef[] = (template.template_indicators || []).map(ti => ({
      indicator_id: ti.indicator_id,
      min_value: ti.min_value,
      max_value: ti.max_value,
      sort_order: ti.sort_order
    }));
    setTemplateLibIndicators(libRefs);
    
    setShowTemplateModal(true);
  };

  const resetTemplateForm = () => {
    setEditingTemplate(null);
    setTemplateName('');
    setTemplateDescription('');
    setTemplateActive(true);
    setTemplateLibIndicators([]);
  };

  const handleOpenPreview = (template: AnalysisType) => {
    setPreviewTemplate(template);
    setShowPreviewModal(true);
  };

  const handleOpenCopyModal = (template: AnalysisType) => {
    setCopyTemplateId(template.id);
    setCopyTemplateName(`${template.name} (копия)`);
    setShowCopyModal(true);
  };

  const handleOpenCreateFromPresetModal = async (presetId: number) => {
    setSelectedPresetId(presetId);
    try {
      const response = await api.get(`/api/presets/${presetId}`);
      setPresetDetail(response.data);
      setNewTemplateName(response.data.name);
    } catch (error) {
      console.error('Error fetching preset detail:', error);
    }
    setShowCreateFromPresetModal(true);
  };

  // ---- Справочник показателей ----

  const handleEditLibIndicator = (indicator: IndicatorLibrary) => {
    setEditingLibIndicator(indicator);
    setLibIndicatorName(indicator.name);
    setLibIndicatorUnit(indicator.unit || '');
    setLibIndicatorType(indicator.data_type);
    setLibIndicatorOptions(indicator.options?.join(', ') || '');
    setLibIndicatorDescription(indicator.description || '');
    setLibIndicatorCategory(indicator.category || '');
    setLibIndicatorRequired(indicator.is_required || false);
    setLibIndicatorDefaultValue(indicator.default_value || '');
    setShowLibModal(true);
  };

  const resetLibIndicatorForm = () => {
    setEditingLibIndicator(null);
    setLibIndicatorName('');
    setLibIndicatorUnit('');
    setLibIndicatorType('number');
    setLibIndicatorOptions('');
    setLibIndicatorDescription('');
    setLibIndicatorCategory('');
    setLibIndicatorRequired(false);
    setLibIndicatorDefaultValue('');
  };

  const handleLibIndicatorSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!libIndicatorName.trim()) {
      showToast('Название показателя обязательно', 'warning');
      return;
    }

    try {
      const data: any = {
        name: libIndicatorName,
        unit: libIndicatorUnit,
        data_type: libIndicatorType,
        description: libIndicatorDescription || null,
        category: libIndicatorCategory || null,
        is_required: libIndicatorRequired,
        default_value: libIndicatorDefaultValue || null,
      };

      if (libIndicatorType === 'select') {
        data.options = libIndicatorOptions.split(',').map(opt => opt.trim()).filter(opt => opt);
      }

      if (editingLibIndicator) {
        await api.put(`/api/indicators/library/${editingLibIndicator.id}`, data);
        showToast('Показатель обновлен', 'success');
      } else {
        await api.post('/api/indicators/library', data);
        showToast('Показатель создан', 'success');
      }

      setShowLibModal(false);
      resetLibIndicatorForm();
      fetchLibraryIndicators();
    } catch (error) {
      console.error('Error saving library indicator:', error);
      showToast('Ошибка при сохранении показателя', 'danger');
    }
  };

  const handleDeleteLibIndicator = async (id: number) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот показатель из справочника?')) {
      return;
    }

    try {
      await api.delete(`/api/indicators/library/${id}`);
      showToast('Показатель удален из справочника', 'success');
      fetchLibraryIndicators();
    } catch (error) {
      console.error('Error deleting library indicator:', error);
      showToast('Ошибка при удалении показателя', 'danger');
    }
  };

  // ---- Выбор показателей из библиотеки в шаблон ----

  const handleOpenSelectLibModal = () => {
    // Инициализируем нормы из уже выбранных показателей
    const norms: Record<number, { min: number | null; max: number | null }> = {};
    templateLibIndicators.forEach(ref => {
      norms[ref.indicator_id] = { min: ref.min_value, max: ref.max_value };
    });
    setLibIndicatorNorms(norms);
    setSelectedLibIndicators(templateLibIndicators.map(ref => ref.indicator_id));
    setShowSelectLibModal(true);
  };

  const handleToggleLibSelection = (indicatorId: number) => {
    setSelectedLibIndicators(prev => {
      if (prev.includes(indicatorId)) {
        return prev.filter(id => id !== indicatorId);
      }
      return [...prev, indicatorId];
    });
  };

  const handleLibNormChange = (indicatorId: number, field: 'min' | 'max', value: string) => {
    setLibIndicatorNorms(prev => ({
      ...prev,
      [indicatorId]: {
        ...prev[indicatorId],
        [field]: value ? parseFloat(value) : null
      }
    }));
  };

  const handleConfirmLibSelection = () => {
    const refs: LibraryIndicatorRef[] = selectedLibIndicators.map((indicatorId, index) => {
      const norm = libIndicatorNorms[indicatorId] || { min: null, max: null };
      return {
        indicator_id: indicatorId,
        min_value: norm.min,
        max_value: norm.max,
        sort_order: index
      };
    });
    setTemplateLibIndicators(refs);
    setShowSelectLibModal(false);
  };

  const handleUpdateLibNorm = (indicatorId: number, field: 'min' | 'max', value: string) => {
    setTemplateLibIndicators(prev => prev.map(ref => 
      ref.indicator_id === indicatorId 
        ? { ...ref, [field === 'min' ? 'min_value' : 'max_value']: value ? parseFloat(value) : null }
        : ref
    ));
  };

  const handleRemoveLibIndicator = (indicatorId: number) => {
    setTemplateLibIndicators(prev => prev.filter(ref => ref.indicator_id !== indicatorId));
  };

  // ---- Reorder indicators ----

  const handleMoveLibIndicator = (indicatorId: number, direction: 'up' | 'down') => {
    setTemplateLibIndicators(prev => {
      const idx = prev.findIndex(ref => ref.indicator_id === indicatorId);
      if (idx === -1) return prev;
      if (direction === 'up' && idx === 0) return prev;
      if (direction === 'down' && idx === prev.length - 1) return prev;
      
      const next = [...prev];
      const swapIdx = direction === 'up' ? idx - 1 : idx + 1;
      [next[idx], next[swapIdx]] = [next[swapIdx], next[idx]];
      // Обновляем sort_order
      return next.map((ref, i) => ({ ...ref, sort_order: i }));
    });
  };

  // ---- Import / Export справочника ----

  const handleExport = async (format: 'csv' | 'excel') => {
    try {
      const response = await api.get(`/api/indicators/library/export/${format}`, {
        responseType: 'blob',
      });
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `indicator_library.${format === 'excel' ? 'xlsx' : 'csv'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      showToast(`Справочник экспортирован в ${format.toUpperCase()}`, 'success');
    } catch (error) {
      console.error('Error exporting:', error);
      showToast('Ошибка при экспорте справочника', 'danger');
    }
  };

  const handleImportFile = async (e: React.ChangeEvent<HTMLInputElement>, format: 'csv' | 'json') => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append('file', file);

      const endpoint = format === 'csv' ? '/api/indicators/library/import/csv' : '/api/indicators/library/import/json';
      const response = await api.post(endpoint, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const { created, errors } = response.data;
      if (created?.length > 0) {
        showToast(`Импортировано показателей: ${created.length}`, 'success');
      }
      if (errors?.length > 0) {
        console.warn('Import errors:', errors);
        showToast(`Импорт завершён с ${errors.length} ошибками`, errors.length > created?.length ? 'danger' : 'warning');
      }
      fetchLibraryIndicators();
    } catch (error) {
      console.error('Error importing:', error);
      showToast('Ошибка при импорте справочника', 'danger');
    }

    // Сбросим input
    e.target.value = '';
  };

  const getLibIndicator = (indicatorId: number): IndicatorLibrary | undefined => {
    return libIndicators.find(i => i.id === indicatorId);
  };

  // ---- 1C Integration ----

  const handleTest1CConnection = async () => {
    if (!c1CBaseUrl.trim()) {
      showToast('Введите URL сервера 1С', 'warning');
      return;
    }

    setIs1CConnecting(true);
    setConnection1CStatus('idle');
    setConnection1CMessage('');

    try {
      const response = await api.post('/api/external/1c/test-connection', {
        connection: {
          base_url: c1CBaseUrl,
          api_key: c1CApiKey || undefined,
          username: c1CUsername || undefined,
          password: c1CPassword || undefined,
        }
      });

      if (response.data.status === 'ok') {
        setConnection1CStatus('success');
        setConnection1CMessage(response.data.message);
        showToast('Подключение к 1С успешно!', 'success');
      } else {
        setConnection1CStatus('error');
        setConnection1CMessage(response.data.message);
        showToast(response.data.message, 'warning');
      }
    } catch (error: any) {
      setConnection1CStatus('error');
      setConnection1CMessage(error.response?.data?.detail || 'Ошибка подключения');
      showToast('Ошибка подключения к 1С', 'danger');
    } finally {
      setIs1CConnecting(false);
    }
  };

  const handleImportFrom1C = async () => {
    if (!c1CBaseUrl.trim()) {
      showToast('Введите URL сервера 1С', 'warning');
      return;
    }

    setIs1CImporting(true);
    setImport1CResult(null);

    try {
      const response = await api.post('/api/external/1c/import-indicators', {
        connection: {
          base_url: c1CBaseUrl,
          api_key: c1CApiKey || undefined,
          username: c1CUsername || undefined,
          password: c1CPassword || undefined,
        },
        skip_duplicates: true,
      });

      setImport1CResult(response.data);
      
      if (response.data.status === 'success') {
        showToast(
          `Импорт завершён: создано ${response.data.created}, пропущено ${response.data.skipped}`,
          'success'
        );
        fetchLibraryIndicators();
      } else {
        showToast(
          `Импорт завершён с ошибками: создано ${response.data.created}, ошибок ${response.data.errors.length}`,
          'warning'
        );
        fetchLibraryIndicators();
      }
    } catch (error: any) {
      showToast(
        error.response?.data?.detail || 'Ошибка импорта из 1С',
        'danger'
      );
    } finally {
      setIs1CImporting(false);
    }
  };

  const reset1CForm = () => {
    setC1CBaseUrl('');
    setC1CApiKey('');
    setC1CUsername('');
    setC1CPassword('');
    setConnection1CStatus('idle');
    setConnection1CMessage('');
    setImport1CResult(null);
  };

  // ---- Пользователи ----

  const validateUserForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!userUsername.trim()) {
      errors.username = 'Имя пользователя обязательно';
    } else if (userUsername.length < 3) {
      errors.username = 'Минимум 3 символа';
    }

    if (!userEmail.trim()) {
      errors.email = 'Email обязателен';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(userEmail)) {
      errors.email = 'Некорректный формат email';
    }

    // Пароль обязателен только при создании
    if (!editingUser) {
      if (!userPassword.trim()) {
        errors.password = 'Пароль обязателен';
      } else if (userPassword.length < 6) {
        errors.password = 'Минимум 6 символов';
      }
    } else {
      // При редактировании пароль опционален, но если заполнен - валидируем
      if (userPassword && userPassword.length < 6) {
        errors.password = 'Минимум 6 символов';
      }
    }

    // Подтверждение пароля
    if (userPassword && userPassword !== userConfirmPassword) {
      errors.confirmPassword = 'Пароли не совпадают';
    }

    setUserFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleUserSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateUserForm()) {
      return;
    }

    try {
      if (editingUser) {
        // Режим редактирования
        const updateData: any = {
          username: userUsername,
          email: userEmail,
          is_admin: userIsAdmin,
          is_active: userIsActive,
        };

        // Пароль отправляем только если заполнен
        if (userPassword) {
          updateData.password = userPassword;
        }

        await api.put(`/auth/users/${editingUser.id}`, updateData);
        showToast('Пользователь успешно обновлен', 'success');
      } else {
        // Режим создания
        await api.post('/auth/register', {
          username: userUsername,
          email: userEmail,
          password: userPassword,
          is_admin: userIsAdmin,
        });
        showToast('Пользователь успешно создан', 'success');
      }

      setShowUserModal(false);
      resetUserForm();
      fetchUsers();
    } catch (error: any) {
      console.error('Error saving user:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при сохранении пользователя';
      showToast(errorMessage, 'danger');
    }
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

  const handleEditUser = (user: UserType) => {
    setEditingUser(user);
    setUserUsername(user.username || '');
    setUserEmail(user.email);
    setUserPassword('');
    setUserConfirmPassword('');
    setUserIsAdmin(user.is_admin);
    setUserIsActive(user.is_active);
    setUserFormErrors({});
    setShowUserModal(true);
  };

  const handleCreateUser = () => {
    resetUserForm();
    setShowUserModal(true);
  };

  const resetUserForm = () => {
    setEditingUser(null);
    setUserUsername('');
    setUserEmail('');
    setUserPassword('');
    setUserConfirmPassword('');
    setUserIsAdmin(false);
    setUserIsActive(true);
    setUserFormErrors({});
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

  // ---- Count total indicators in template ----
  const getTotalIndicators = (template: AnalysisType): number => {
    return (template.template_indicators?.length || 0);
  };

  const getCategoryLabel = (category: string | null): string => {
    const labels: Record<string, string> = {
      quality: 'Качество',
      safety: 'Безопасность',
      performance: 'Производительность',
      chemical: 'Химический состав',
      physical: 'Физические свойства',
      microbiology: 'Микробиология',
    };
    return category ? (labels[category] || category) : 'Без категории';
  };

  return (
    <div className="min-h-screen bg-background">
      <AppHeader showDashboardLink />

      <main className="app-main py-6">
        <div className="container-fluid">
          <div className="page-wrapper">
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-text-primary mb-1">Администрирование</h1>
              <p className="text-text-secondary text-sm">Управление шаблонами, справочником показателей и пользователями</p>
            </div>

            <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k || 'templates')} className="mb-6">
              {/* Templates Tab */}
              <Tab eventKey="templates" title={
                <span><i className="bi bi-list-ul me-1"></i>Шаблоны анализа</span>
              }>
                <Card className="border-0 shadow-md">
                    <CardHeader className="bg-white border-b border-border d-flex justify-content-between align-items-center">
                      <CardTitle className="h5 mb-0 flex items-center gap-2">
                        <i className="bi bi-file-earmark-text text-primary"></i>
                        Управление шаблонами
                      </CardTitle>
                      <div className="flex gap-2">
                        {templates.length > 0 && (
                          <Button variant="outline-danger" size="sm" onClick={handleClearAllTemplates} className="flex items-center gap-1">
                            <i className="bi bi-trash"></i>
                            Очистить все
                          </Button>
                        )}
                        <Button variant="primary" onClick={() => { resetTemplateForm(); setShowTemplateModal(true); }} className="flex items-center gap-1">
                          <i className="bi bi-plus-circle"></i>
                          Создать шаблон
                        </Button>
                      </div>
                    </CardHeader>
                  <CardBody className="p-6">
                    {isLoading ? (
                      <div className="text-center py-8">
                        <Spinner animation="border" />
                        <p className="text-text-muted mt-2">Загрузка...</p>
                      </div>
                    ) : templates.length === 0 ? (
                      <div className="text-center py-8">
                        <i className="bi bi-inbox display-1 text-text-muted"></i>
                        <p className="text-text-muted mt-2">Нет шаблонов анализа</p>
                      </div>
                    ) : (
                      <div className="table-responsive">
                        <Table striped hover className="rounded-lg overflow-hidden">
                          <thead className="bg-background-gray">
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
                                <td>
                                  <Badge bg="info" className="font-mono">{getTotalIndicators(template)}</Badge>
                                </td>
                                <td>
                                  <Badge bg={template.is_active ? 'success' : 'danger'} className="flex items-center gap-1 w-fit">
                                    <div className={`w-1.5 h-1.5 rounded-full ${template.is_active ? 'bg-white' : 'bg-white'}`} />
                                    {template.is_active ? 'Активен' : 'Неактивен'}
                                  </Badge>
                                </td>
                                <td className="text-end">
                                  <div className="flex gap-1 justify-content-end">
                                    <Button variant="outline-primary" size="sm" onClick={() => handleEditTemplate(template)} className="p-1.5" title="Редактировать">
                                      <i className="bi bi-pencil"></i>
                                    </Button>
                                    <Button variant="outline-secondary" size="sm" onClick={() => handleOpenPreview(template)} className="p-1.5" title="Просмотр">
                                      <i className="bi bi-eye"></i>
                                    </Button>
                                    <Button variant="outline-info" size="sm" onClick={() => handleOpenCopyModal(template)} className="p-1.5" title="Копировать">
                                      <i className="bi bi-copy"></i>
                                    </Button>
                                    <Button variant={template.is_active ? 'warning' : 'success'} size="sm" onClick={() => handleToggleTemplate(template.id, template.is_active)} className="p-1.5" title={template.is_active ? 'Деактивировать' : 'Активировать'}>
                                      <i className={`bi ${template.is_active ? 'bi-pause-fill' : 'bi-play-fill'}`}></i>
                                    </Button>
                                    <Button variant="outline-danger" size="sm" onClick={() => handleDeleteTemplate(template.id)} className="p-1.5" title="Удалить">
                                      <i className="bi bi-trash"></i>
                                    </Button>
                                  </div>
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

              {/* Presets Tab */}
              <Tab eventKey="presets" title={
                <span><i className="bi bi-collection-fill me-1"></i>Пресеты</span>
              }>
                <Card className="border-0 shadow-md">
                  <CardHeader className="bg-white border-b border-border">
                    <CardTitle className="h5 mb-0 flex items-center gap-2">
                      <i className="bi bi-layers text-primary"></i>
                      Предустановленные наборы показателей
                    </CardTitle>
                  </CardHeader>
                  <CardBody className="p-6">
                    {presets.length === 0 ? (
                      <div className="text-center py-8">
                        <i className="bi bi-inbox display-1 text-text-muted"></i>
                        <p className="text-text-muted mt-2">Нет пресетов</p>
                        <p className="text-text-secondary text-sm">Пресеты — это предустановленные наборы показателей из справочника.</p>
                      </div>
                    ) : (
                      <div className="table-responsive">
                        <Table striped hover className="rounded-lg overflow-hidden">
                          <thead className="bg-background-gray">
                            <tr>
                              <th>Название</th>
                              <th>Категория</th>
                              <th>Показателей</th>
                              <th className="text-end">Действия</th>
                            </tr>
                          </thead>
                          <tbody>
                            {presets.map((preset) => (
                              <tr key={preset.id}>
                                <td><strong>{preset.name}</strong></td>
                                <td>
                                  <Badge bg="secondary">{getCategoryLabel(preset.category)}</Badge>
                                </td>
                                <td><Badge bg="info" className="font-mono">{preset.indicators_count}</Badge></td>
                                <td className="text-end">
                                  <Button variant="success" size="sm" onClick={() => handleOpenCreateFromPresetModal(preset.id)} className="flex items-center gap-1">
                                    <i className="bi bi-plus-circle"></i>
                                    Создать шаблон
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

              {/* Indicators Library Tab */}
              <Tab eventKey="library" title={
                <span><i className="bi bi-book me-1"></i>Справочник показателей</span>
              }>
                <Card className="border-0 shadow-md">
                  <CardHeader className="bg-white border-b border-border d-flex justify-content-between align-items-center flex-wrap gap-3">
                    <CardTitle className="h5 mb-0 flex items-center gap-2">
                      <i className="bi bi-collection text-primary"></i>
                      Справочник показателей
                    </CardTitle>
                    <div className="d-flex gap-2 align-items-center flex-wrap">
                      <div className="btn-group">
                        <button className="btn btn-outline-success btn-sm dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                          <i className="bi bi-download me-1"></i>Экспорт
                        </button>
                        <ul className="dropdown-menu dropdown-menu-end">
                          <li><button className="dropdown-item" onClick={() => handleExport('csv')}><i className="bi bi-filetype-csv me-2"></i>CSV</button></li>
                          <li><button className="dropdown-item" onClick={() => handleExport('excel')}><i className="bi bi-file-earmark-excel me-2"></i>Excel</button></li>
                        </ul>
                      </div>
                      <div className="btn-group">
                        <button className="btn btn-outline-warning btn-sm dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                          <i className="bi bi-upload me-1"></i>Импорт
                        </button>
                        <ul className="dropdown-menu dropdown-menu-end">
                          <li>
                            <label className="dropdown-item" style={{cursor: 'pointer'}}>
                              <i className="bi bi-filetype-csv me-2"></i>CSV
                              <input type="file" accept=".csv,.txt" style={{display: 'none'}} onChange={(e) => handleImportFile(e, 'csv')} />
                            </label>
                          </li>
                          <li>
                            <label className="dropdown-item" style={{cursor: 'pointer'}}>
                              <i className="bi bi-filetype-json me-2"></i>JSON
                              <input type="file" accept=".json" style={{display: 'none'}} onChange={(e) => handleImportFile(e, 'json')} />
                            </label>
                          </li>
                        </ul>
                      </div>
                      <Button variant="primary" size="sm" onClick={() => setShowLibModal(true)} className="flex items-center gap-1">
                        <i className="bi bi-plus-circle"></i>Добавить
                      </Button>
                    </div>
                  </CardHeader>
                  <CardBody className="p-6">
                    {/* Search & filters */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4 p-4 bg-background-gray rounded-xl">
                      <div className="md:col-span-2">
                        <div className="input-group input-group-sm">
                          <span className="input-group-text"><i className="bi bi-search"></i></span>
                          <Form.Control type="text" placeholder="Поиск по названию, описанию..." value={libSearch} onChange={(e) => handleLibSearchChange(e.target.value)} />
                          {libSearch && (<button className="btn btn-outline-secondary" onClick={() => handleLibSearchChange('')}><i className="bi bi-x"></i></button>)}
                        </div>
                      </div>
                      <Form.Select size="sm" value={libFilterCategory} onChange={(e) => handleLibFilterChange('category', e.target.value)}>
                        <option value="">Все категории</option>
                        <option value="quality">Качество</option>
                        <option value="safety">Безопасность</option>
                        <option value="performance">Производительность</option>
                        <option value="chemical">Химический состав</option>
                        <option value="physical">Физические свойства</option>
                        <option value="microbiology">Микробиология</option>
                      </Form.Select>
                      <div className="d-flex align-items-center gap-2">
                        <Form.Select size="sm" value={libFilterType} onChange={(e) => handleLibFilterChange('type', e.target.value)} className="flex-1">
                          <option value="">Все типы</option>
                          <option value="number">Число</option>
                          <option value="text">Текст</option>
                          <option value="select">Выбор</option>
                        </Form.Select>
                        {libIsSearching && <Spinner animation="border" size="sm" />}
                        <small className="text-text-muted font-mono">{libIndicators.length}</small>
                      </div>
                    </div>
                    {libIndicators.length === 0 && !libIsSearching ? (
                      <div className="text-center py-4">
                        <i className="bi bi-inbox display-1 text-muted"></i>
                        <p className="text-muted mt-2">Нет показателей в справочнике</p>
                        <p className="text-muted">Добавьте показатели, которые будут использоваться в шаблонах</p>
                      </div>
                    ) : (
                      <div className="table-responsive">
                        <Table striped hover>
                          <thead>
                            <tr>
                              <th>Название</th>
                              <th>Ед. изм.</th>
                              <th>Тип</th>
                              <th>Варианты</th>
                              <th className="text-end">Действия</th>
                            </tr>
                          </thead>
                          <tbody>
                            {libIndicators.map((ind) => (
                              <tr key={ind.id}>
                                <td><strong>{ind.name}</strong></td>
                                <td>{ind.unit || '-'}</td>
                                <td>
                                  <Badge bg="secondary">
                                    {ind.data_type === 'number' ? 'Число' : ind.data_type === 'text' ? 'Текст' : 'Выбор'}
                                  </Badge>
                                </td>
                                <td>
                                  {ind.data_type === 'select' && ind.options ? (
                                    <small className="text-muted">{ind.options.join(', ')}</small>
                                  ) : '-'}
                                </td>
                                <td className="text-end">
                                  <Button 
                                    variant="outline-primary" 
                                    size="sm" 
                                    className="me-1"
                                    onClick={() => handleEditLibIndicator(ind)}
                                  >
                                    <i className="bi bi-pencil me-1"></i>
                                    Ред.
                                  </Button>
                                  <Button 
                                    variant="outline-danger" 
                                    size="sm"
                                    onClick={() => handleDeleteLibIndicator(ind.id)}
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
                <Card className="border-0 shadow-md">
                  <CardHeader className="bg-white border-b border-border d-flex justify-content-between align-items-center">
                    <CardTitle className="h5 mb-0 flex items-center gap-2">
                      <i className="bi bi-person-lines-fill text-primary"></i>
                      Управление пользователями
                    </CardTitle>
                    <Button variant="primary" size="sm" onClick={handleCreateUser} className="flex items-center gap-1">
                      <i className="bi bi-plus-circle"></i>
                      Создать
                    </Button>
                  </CardHeader>
                  <CardBody className="p-0">
                    {users.length === 0 ? (
                      <div className="text-center py-8">
                        <i className="bi bi-inbox display-1 text-text-muted"></i>
                        <p className="text-text-muted mt-2">Нет пользователей</p>
                      </div>
                    ) : (
                      <div className="divide-y divide-border">
                        {users.map((user) => (
                          <div key={user.id} className="flex items-center justify-between p-4 hover:bg-background-gray transition-colors">
                            <div className="flex items-center gap-3">
                              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold text-sm ${user.is_admin ? 'bg-primary' : 'bg-secondary'}`}>
                                {(user.username || user.email || '?').charAt(0).toUpperCase()}
                              </div>
                              <div>
                                <p className="font-medium text-text-primary">{user.username || '—'}</p>
                                <p className="text-sm text-text-muted">{user.email}</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <Badge bg={user.is_admin ? 'primary' : 'secondary'} className="text-xs">
                                {user.is_admin ? 'Админ' : 'Пользователь'}
                              </Badge>
                              <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${user.is_active ? 'bg-success-light text-success' : 'bg-danger-light text-danger'}`}>
                                <div className={`w-1.5 h-1.5 rounded-full ${user.is_active ? 'bg-success' : 'bg-danger'}`} />
                                {user.is_active ? 'Активен' : 'Заблокирован'}
                              </div>
                              <div className="flex gap-1">
                                <Button variant="outline-primary" size="sm" onClick={() => handleEditUser(user)} className="p-1.5">
                                  <i className="bi bi-pencil"></i>
                                </Button>
                                <Button variant={user.is_active ? 'warning' : 'success'} size="sm" onClick={() => handleToggleUser(user.id, user.is_active)} className="p-1.5">
                                  <i className={`bi ${user.is_active ? 'bi-pause-fill' : 'bi-play-fill'}`}></i>
                                </Button>
                                <Button variant="outline-danger" size="sm" onClick={() => handleDeleteUser(user.id)} className="p-1.5">
                                  <i className="bi bi-trash"></i>
                                </Button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardBody>
                </Card>
              </Tab>

              {/* Integrations Tab */}
              <Tab eventKey="integrations" title={
                <span><i className="bi bi-plug-fill me-1"></i>Интеграции</span>
              }>
                <Card className="border-0 shadow-md">
                  <CardHeader className="bg-white border-b border-border">
                    <CardTitle className="h5 mb-0 flex items-center gap-2">
                      <i className="bi bi-plug text-primary"></i>
                      Внешние интеграции
                    </CardTitle>
                  </CardHeader>
                  <CardBody className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* 1C Integration Card */}
                      <div className="p-5 border border-border rounded-xl hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-warning-light rounded-xl flex items-center justify-center">
                              <i className="bi bi-building text-warning text-xl"></i>
                            </div>
                            <div>
                              <h3 className="font-semibold text-text-primary">1С Предприятие</h3>
                              <p className="text-sm text-text-muted">Импорт справочника показателей</p>
                            </div>
                          </div>
                          <Badge bg="success" className="flex items-center gap-1">
                            <div className="w-1.5 h-1.5 rounded-full bg-white" />
                            Доступно
                          </Badge>
                        </div>
                        <p className="text-sm text-text-secondary mb-4">
                          Подключите 1С для автоматического импорта справочника показателей. Поддерживается маппинг полей.
                        </p>
                        <Button variant="primary" size="sm" onClick={() => { reset1CForm(); setShow1CModal(true); }} className="flex items-center gap-1">
                          <i className="bi bi-gear"></i>
                          Настроить
                        </Button>
                      </div>

                      {/* API Settings Card */}
                      <div className="p-5 border border-border rounded-xl hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-info-light rounded-xl flex items-center justify-center">
                              <i className="bi bi-key text-info text-xl"></i>
                            </div>
                            <div>
                              <h3 className="font-semibold text-text-primary">API Ключ</h3>
                              <p className="text-sm text-text-muted">Управление доступом к API</p>
                            </div>
                          </div>
                          <Badge bg="secondary">Системное</Badge>
                        </div>
                        <p className="text-sm text-text-secondary mb-4">
                          Настройте API-ключ для защиты внешних запросов к системе.
                        </p>
                        <Button variant="outline-secondary" size="sm" disabled>
                          <i className="bi bi-lock"></i>
                          Скоро
                        </Button>
                      </div>
                    </div>
                  </CardBody>
                </Card>
              </Tab>
            </Tabs>
          </div>
        </div>
      </main>

      {/* Template Modal */}
      <Modal show={showTemplateModal} onHide={() => setShowTemplateModal(false)} size="lg">
        <Modal.Header closeButton className="border-b border-border">
          <Modal.Title className="flex items-center gap-2">
            <i className="bi bi-file-earmark-text text-primary"></i>
            {editingTemplate ? 'Редактирование шаблона' : 'Создание шаблона'}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body className="p-6">
          <Form onSubmit={handleTemplateSubmit}>
            <Form.Group className="mb-4">
              <Form.Label className="font-medium">Название шаблона</Form.Label>
              <Form.Control type="text" value={templateName} onChange={(e) => setTemplateName(e.target.value)} className="h-12" required />
            </Form.Group>
            
            <Form.Group className="mb-4">
              <Form.Label className="font-medium">Описание</Form.Label>
              <Form.Control as="textarea" rows={3} value={templateDescription} onChange={(e) => setTemplateDescription(e.target.value)} />
            </Form.Group>

            <Form.Group className="mb-4">
              <Form.Check type="switch" label="Активен" checked={templateActive} onChange={(e) => setTemplateActive(e.target.checked)} />
            </Form.Group>

            {/* Показатели из справочника */}
            <div className="mb-4">
              <div className="flex justify-between items-center mb-3">
                <h5 className="mb-0 flex items-center gap-2">
                  <i className="bi bi-book text-primary"></i>
                  Показатели из справочника
                </h5>
                <Button variant="outline-primary" size="sm" onClick={handleOpenSelectLibModal} className="flex items-center gap-1">
                  <i className="bi bi-plus-circle"></i>Выбрать
                </Button>
              </div>
              
              {templateLibIndicators.length === 0 ? (
                <div className="border-2 border-dashed border-border rounded-xl p-6 text-center bg-background-gray">
                  <i className="bi bi-inbox text-text-muted text-2xl"></i>
                  <p className="text-text-muted text-sm mt-2">Нет показателей. Нажмите "Выбрать" для добавления.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {templateLibIndicators.map((ref, index) => {
                    const libInd = getLibIndicator(ref.indicator_id);
                    const isFirst = index === 0;
                    const isLast = index === templateLibIndicators.length - 1;
                    return (
                      <div key={ref.indicator_id} className="p-3 border border-border rounded-xl bg-background-gray">
                        <div className="flex justify-between items-start">
                          <div className="flex items-start gap-3">
                            <div className="flex flex-col gap-0.5 mt-1">
                              <button className="p-0.5 rounded hover:bg-white text-text-muted disabled:opacity-30" disabled={isFirst} onClick={() => handleMoveLibIndicator(ref.indicator_id, 'up')} title="Вверх">
                                <i className="bi bi-chevron-up"></i>
                              </button>
                              <button className="p-0.5 rounded hover:bg-white text-text-muted disabled:opacity-30" disabled={isLast} onClick={() => handleMoveLibIndicator(ref.indicator_id, 'down')} title="Вниз">
                                <i className="bi bi-chevron-down"></i>
                              </button>
                            </div>
                            <div>
                              <div className="flex items-center gap-2 flex-wrap">
                                <strong>{libInd?.name || `#${ref.indicator_id}`}</strong>
                                <small className="text-text-muted font-mono">{libInd?.unit}</small>
                                <Badge bg="info" pill>Справочник</Badge>
                                {libInd?.category && <Badge bg="secondary">{getCategoryLabel(libInd.category)}</Badge>}
                              </div>
                              {libInd?.description && <p className="text-text-muted text-sm mt-1">{libInd.description}</p>}
                              <div className="flex gap-2 mt-2 items-center">
                                <small className="text-text-muted">Норма:</small>
                                <Form.Control type="number" size="sm" style={{ width: '80px' }} value={ref.min_value ?? ''} onChange={(e) => handleUpdateLibNorm(ref.indicator_id, 'min', e.target.value)} placeholder="от" />
                                <span className="text-text-muted">—</span>
                                <Form.Control type="number" size="sm" style={{ width: '80px' }} value={ref.max_value ?? ''} onChange={(e) => handleUpdateLibNorm(ref.indicator_id, 'max', e.target.value)} placeholder="до" />
                              </div>
                            </div>
                          </div>
                          <Button variant="outline-danger" size="sm" onClick={() => handleRemoveLibIndicator(ref.indicator_id)} className="p-1.5" title="Убрать">
                            <i className="bi bi-x"></i>
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </Form>
        </Modal.Body>
        <Modal.Footer className="border-t border-border">
          <Button variant="secondary" onClick={() => setShowTemplateModal(false)}>Отмена</Button>
          <Button variant="primary" onClick={handleTemplateSubmit}>
            {editingTemplate ? 'Сохранить изменения' : 'Создать шаблон'}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Copy Template Modal */}
      <Modal show={showCopyModal} onHide={() => setShowCopyModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Копирование шаблона</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={(e) => { e.preventDefault(); handleCopyTemplate(); }}>
            <Form.Group className="mb-3">
              <Form.Label>Название для копии</Form.Label>
              <Form.Control
                type="text"
                value={copyTemplateName}
                onChange={(e) => setCopyTemplateName(e.target.value)}
                required
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowCopyModal(false)}>
            Отмена
          </Button>
          <Button variant="primary" onClick={handleCopyTemplate}>
            <i className="bi bi-copy me-1"></i>
            Создать копию
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Create From Preset Modal */}
      <Modal show={showCreateFromPresetModal} onHide={() => setShowCreateFromPresetModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Создание шаблона из пресета</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {presetDetail && (
            <div className="mb-3">
              <p><strong>Пресет:</strong> {presetDetail.name}</p>
              <p><strong>Категория:</strong> {getCategoryLabel(presetDetail.category)}</p>
              <p><strong>Показателей:</strong> {presetDetail.indicators.length}</p>
              {presetDetail.indicators.length > 0 && (
                <ul className="list-group list-group-flush mb-3">
                  {presetDetail.indicators.slice(0, 5).map((pi) => (
                    <li key={pi.id} className="list-group-item py-1">
                      <small>{pi.indicator_name} ({pi.indicator_unit})</small>
                    </li>
                  ))}
                  {presetDetail.indicators.length > 5 && (
                    <li className="list-group-item py-1 text-muted">
                      <small>...и ещё {presetDetail.indicators.length - 5}</small>
                    </li>
                  )}
                </ul>
              )}
            </div>
          )}
          <Form onSubmit={(e) => { e.preventDefault(); handleCreateFromPreset(); }}>
            <Form.Group className="mb-3">
              <Form.Label>Название нового шаблона</Form.Label>
              <Form.Control
                type="text"
                value={newTemplateName}
                onChange={(e) => setNewTemplateName(e.target.value)}
                required
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowCreateFromPresetModal(false)}>
            Отмена
          </Button>
          <Button variant="success" onClick={handleCreateFromPreset}>
            <i className="bi bi-plus-circle me-1"></i>
            Создать шаблон
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Library Indicator Modal */}
      <Modal show={showLibModal} onHide={() => setShowLibModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>
            {editingLibIndicator ? 'Редактирование показателя' : 'Добавление показателя в справочник'}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleLibIndicatorSubmit}>
            <Form.Group className="mb-3">
              <Form.Label>Название показателя</Form.Label>
              <Form.Control
                type="text"
                value={libIndicatorName}
                onChange={(e) => setLibIndicatorName(e.target.value)}
                required
              />
            </Form.Group>
            
            <Form.Group className="mb-3">
              <Form.Label>Единица измерения</Form.Label>
              <Form.Control
                type="text"
                value={libIndicatorUnit}
                onChange={(e) => setLibIndicatorUnit(e.target.value)}
                required
              />
            </Form.Group>
            
            <Form.Group className="mb-3">
              <Form.Label>Тип</Form.Label>
              <Form.Select
                value={libIndicatorType}
                onChange={(e) => setLibIndicatorType(e.target.value as 'number' | 'text' | 'select')}
              >
                <option value="number">Число с плавающей точкой</option>
                <option value="text">Текст</option>
                <option value="select">Выбор из списка</option>
              </Form.Select>
            </Form.Group>
            
            {libIndicatorType === 'select' && (
              <Form.Group className="mb-3">
                <Form.Label>Варианты выбора (через запятую)</Form.Label>
                <Form.Control
                  type="text"
                  value={libIndicatorOptions}
                  onChange={(e) => setLibIndicatorOptions(e.target.value)}
                  placeholder="Вариант 1, Вариант 2, Вариант 3"
                />
              </Form.Group>
            )}
            
            {/* Новые поля */}
            <Form.Group className="mb-3">
              <Form.Label>Описание</Form.Label>
              <Form.Control
                as="textarea"
                rows={2}
                value={libIndicatorDescription}
                onChange={(e) => setLibIndicatorDescription(e.target.value)}
                placeholder="Подробное описание показателя"
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Категория</Form.Label>
              <Form.Select
                value={libIndicatorCategory}
                onChange={(e) => setLibIndicatorCategory(e.target.value)}
              >
                <option value="">Без категории</option>
                <option value="quality">Качество</option>
                <option value="safety">Безопасность</option>
                <option value="performance">Производительность</option>
                <option value="chemical">Химический состав</option>
                <option value="physical">Физические свойства</option>
                <option value="microbiology">Микробиология</option>
              </Form.Select>
            </Form.Group>

            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Check
                    type="switch"
                    label="Обязательный показатель"
                    checked={libIndicatorRequired}
                    onChange={(e) => setLibIndicatorRequired(e.target.checked)}
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Значение по умолчанию</Form.Label>
                  <Form.Control
                    type="text"
                    value={libIndicatorDefaultValue}
                    onChange={(e) => setLibIndicatorDefaultValue(e.target.value)}
                    placeholder="Например: 0.0"
                  />
                </Form.Group>
              </Col>
            </Row>

            {libIndicatorType !== 'number' && (
              <Alert variant="info">
                <small><i className="bi bi-info-circle me-1"></i>Нормы (min/max) задаются при добавлении показателя в шаблон.</small>
              </Alert>
            )}
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowLibModal(false)}>
            Отмена
          </Button>
          <Button variant="primary" onClick={handleLibIndicatorSubmit}>
            {editingLibIndicator ? 'Сохранить изменения' : 'Добавить показатель'}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Select from Library Modal */}
      <Modal show={showSelectLibModal} onHide={() => setShowSelectLibModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            Выбор показателей из справочника
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p className="text-muted mb-3">
            Выберите показатели для добавления в шаблон и задайте для них нормы (min/max).
          </p>
          
          {libIndicators.length === 0 ? (
            <Alert variant="warning">
              <i className="bi bi-exclamation-triangle-fill me-2"></i>
              Справочник показателей пуст. Сначала добавьте показатели на вкладке "Справочник показателей".
            </Alert>
          ) : (
            <div className="table-responsive">
              <Table striped hover size="sm">
                <thead>
                  <tr>
                    <th style={{ width: '40px' }}>#</th>
                    <th>Показатель</th>
                    <th>Тип</th>
                    <th style={{ width: '120px' }}>Норма min</th>
                    <th style={{ width: '120px' }}>Норма max</th>
                  </tr>
                </thead>
                <tbody>
                  {libIndicators.map((ind) => (
                    <tr key={ind.id} className={selectedLibIndicators.includes(ind.id) ? 'table-primary' : ''}>
                      <td>
                        <Form.Check
                          type="checkbox"
                          checked={selectedLibIndicators.includes(ind.id)}
                          onChange={() => handleToggleLibSelection(ind.id)}
                        />
                      </td>
                      <td>
                        <strong>{ind.name}</strong>{ind.unit && `, ${ind.unit}`}
                        {ind.data_type === 'select' && ind.options && (
                          <small className="text-muted d-block">Варианты: {ind.options.join(', ')}</small>
                        )}
                      </td>
                      <td>
                        <Badge bg="secondary">
                          {ind.data_type === 'number' ? 'Число' : ind.data_type === 'text' ? 'Текст' : 'Выбор'}
                        </Badge>
                      </td>
                      <td>
                        <Form.Control
                          type="number"
                          size="sm"
                          value={libIndicatorNorms[ind.id]?.min ?? ''}
                          onChange={(e) => handleLibNormChange(ind.id, 'min', e.target.value)}
                          disabled={!selectedLibIndicators.includes(ind.id)}
                          placeholder="min"
                        />
                      </td>
                      <td>
                        <Form.Control
                          type="number"
                          size="sm"
                          value={libIndicatorNorms[ind.id]?.max ?? ''}
                          onChange={(e) => handleLibNormChange(ind.id, 'max', e.target.value)}
                          disabled={!selectedLibIndicators.includes(ind.id)}
                          placeholder="max"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowSelectLibModal(false)}>
            Отмена
          </Button>
          <Button variant="primary" onClick={handleConfirmLibSelection} disabled={selectedLibIndicators.length === 0}>
            <i className="bi bi-check-circle me-1"></i>
            Добавить выбранные ({selectedLibIndicators.length})
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Preview Template Modal */}
      <Modal show={showPreviewModal} onHide={() => setShowPreviewModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            <i className="bi bi-eye me-2"></i>
            {previewTemplate?.name}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {previewTemplate && (
            <>
              <div className="mb-3">
                <Badge bg={previewTemplate.is_active ? 'success' : 'danger'}>
                  {previewTemplate.is_active ? 'Активен' : 'Неактивен'}
                </Badge>
              </div>
              
              {previewTemplate.description && (
                <p className="text-muted mb-3">{previewTemplate.description}</p>
              )}

              <h6 className="mb-2">Показатели ({getTotalIndicators(previewTemplate)})</h6>
              
              {/* Library indicators */}
              {previewTemplate.template_indicators && previewTemplate.template_indicators.length > 0 && (
                <div className="mb-3">
                  <small className="text-muted fw-bold d-block mb-1">
                    <i className="bi bi-book me-1"></i>Из справочника:
                  </small>
                  <div className="list-group list-group-flush">
                    {previewTemplate.template_indicators.map((ti, idx) => (
                      <div key={ti.id} className="list-group-item py-1 px-2 d-flex justify-content-between align-items-center">
                        <div>
                          <span className="badge bg-secondary me-1">{idx + 1}</span>
                          <strong>{ti.name}</strong>
                          <small className="text-muted ms-1">{ti.unit}</small>
                          {(ti.min_value !== null || ti.max_value !== null) && (
                            <small className="text-muted ms-2">
                              Норма: {ti.min_value !== null ? ti.min_value : 'от'} - {ti.max_value !== null ? ti.max_value : 'до'}
                            </small>
                          )}
                          <Badge bg="info" className="ms-1" pill>{ti.data_type}</Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowPreviewModal(false)}>
            Закрыть
          </Button>
          {previewTemplate && (
            <Button variant="primary" onClick={() => { setShowPreviewModal(false); handleEditTemplate(previewTemplate); }}>
              <i className="bi bi-pencil me-1"></i>Редактировать
            </Button>
          )}
        </Modal.Footer>
      </Modal>

      {/* 1C Integration Modal */}
      <Modal show={show1CModal} onHide={() => setShow1CModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            <i className="bi bi-cloud-download me-2"></i>
            Загрузка из 1С Предприятие
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>URL сервера 1С</Form.Label>
              <Form.Control
                type="text"
                placeholder="http://1c-server:8080"
                value={c1CBaseUrl}
                onChange={(e) => setC1CBaseUrl(e.target.value)}
              />
              <Form.Text className="text-muted">
                Базовый URL для подключения к 1С (например, http://server:8080)
              </Form.Text>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>API-ключ (опционально)</Form.Label>
              <Form.Control
                type="password"
                placeholder="Введите API-ключ"
                value={c1CApiKey}
                onChange={(e) => setC1CApiKey(e.target.value)}
              />
              <Form.Text className="text-muted">
                Если используется авторизация по API-ключу
              </Form.Text>
            </Form.Group>

            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Логин (опционально)</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="Имя пользователя"
                    value={c1CUsername}
                    onChange={(e) => setC1CUsername(e.target.value)}
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Пароль (опционально)</Form.Label>
                  <Form.Control
                    type="password"
                    placeholder="Пароль"
                    value={c1CPassword}
                    onChange={(e) => setC1CPassword(e.target.value)}
                  />
                </Form.Group>
              </Col>
            </Row>

            {connection1CStatus !== 'idle' && (
              <Alert variant={connection1CStatus === 'success' ? 'success' : 'danger'}>
                <i className={`bi bi-${connection1CStatus === 'success' ? 'check-circle' : 'exclamation-triangle'}-fill me-2`}></i>
                {connection1CMessage}
              </Alert>
            )}

            {import1CResult && (
              <div className="mt-3">
                <h6>Результат импорта:</h6>
                <ul className="list-unstyled">
                  <li><strong>Всего получено:</strong> {import1CResult.total}</li>
                  <li><strong>Создано:</strong> {import1CResult.created}</li>
                  <li><strong>Пропущено (дубликаты):</strong> {import1CResult.skipped}</li>
                  {import1CResult.errors.length > 0 && (
                    <li className="text-danger">
                      <strong>Ошибок:</strong> {import1CResult.errors.length}
                    </li>
                  )}
                </ul>
              </div>
            )}
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShow1CModal(false)}>
            Закрыть
          </Button>
          <Button
            variant="outline-primary"
            onClick={handleTest1CConnection}
            disabled={is1CConnecting}
          >
            {is1CConnecting ? (
              <>
                <Spinner as="span" animation="border" size="sm" className="me-2" />
                Проверка...
              </>
            ) : (
              <>
                <i className="bi bi-check-circle me-1"></i>
                Проверить подключение
              </>
            )}
          </Button>
          <Button
            variant="primary"
            onClick={handleImportFrom1C}
            disabled={is1CImporting}
          >
            {is1CImporting ? (
              <>
                <Spinner as="span" animation="border" size="sm" className="me-2" />
                Импорт...
              </>
            ) : (
              <>
                <i className="bi bi-cloud-download me-1"></i>
                Загрузить показатели
              </>
            )}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* User Modal - Create/Edit */}
      <Modal show={showUserModal} onHide={() => { setShowUserModal(false); resetUserForm(); }}>
        <Modal.Header closeButton>
          <Modal.Title>
            <i className={`bi bi-${editingUser ? 'pencil' : 'person-plus'} me-2`}></i>
            {editingUser ? 'Редактирование пользователя' : 'Создание пользователя'}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleUserSubmit} noValidate>
            <Form.Group className="mb-3">
              <Form.Label>Имя пользователя</Form.Label>
              <Form.Control
                type="text"
                placeholder="Введите имя пользователя"
                value={userUsername}
                onChange={(e) => setUserUsername(e.target.value)}
                isInvalid={!!userFormErrors.username}
                required
              />
              <Form.Control.Feedback type="invalid">
                {userFormErrors.username}
              </Form.Control.Feedback>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Email</Form.Label>
              <Form.Control
                type="email"
                placeholder="user@example.com"
                value={userEmail}
                onChange={(e) => setUserEmail(e.target.value)}
                isInvalid={!!userFormErrors.email}
                required
              />
              <Form.Control.Feedback type="invalid">
                {userFormErrors.email}
              </Form.Control.Feedback>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>
                Пароль
                {editingUser && <small className="text-muted ms-1">(оставьте пустым, чтобы не менять)</small>}
              </Form.Label>
              <Form.Control
                type="password"
                placeholder={editingUser ? "Введите новый пароль" : "Введите пароль"}
                value={userPassword}
                onChange={(e) => setUserPassword(e.target.value)}
                isInvalid={!!userFormErrors.password}
                required={!editingUser}
              />
              <Form.Control.Feedback type="invalid">
                {userFormErrors.password}
              </Form.Control.Feedback>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Подтверждение пароля</Form.Label>
              <Form.Control
                type="password"
                placeholder="Подтвердите пароль"
                value={userConfirmPassword}
                onChange={(e) => setUserConfirmPassword(e.target.value)}
                isInvalid={!!userFormErrors.confirmPassword}
                required={!editingUser || !!userPassword}
              />
              <Form.Control.Feedback type="invalid">
                {userFormErrors.confirmPassword}
              </Form.Control.Feedback>
            </Form.Group>

            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Check
                    type="switch"
                    label="Администратор"
                    checked={userIsAdmin}
                    onChange={(e) => setUserIsAdmin(e.target.checked)}
                  />
                  <Form.Text className="text-muted">
                    Администраторы имеют доступ к управлению шаблонами и пользователями
                  </Form.Text>
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Check
                    type="switch"
                    label="Активен"
                    checked={userIsActive}
                    onChange={(e) => setUserIsActive(e.target.checked)}
                  />
                  <Form.Text className="text-muted">
                    Неактивные пользователи не могут войти в систему
                  </Form.Text>
                </Form.Group>
              </Col>
            </Row>

            {editingUser && (
              <Alert variant="info" className="py-2">
                <small>
                  <i className="bi bi-info-circle me-1"></i>
                  ID пользователя: {editingUser.id}
                </small>
              </Alert>
            )}
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => { setShowUserModal(false); resetUserForm(); }}>
            Отмена
          </Button>
          <Button variant="primary" onClick={handleUserSubmit}>
            <i className={`bi bi-${editingUser ? 'check' : 'plus-circle'} me-1`}></i>
            {editingUser ? 'Сохранить изменения' : 'Создать'}
          </Button>
        </Modal.Footer>
      </Modal>

      <AppToast toast={toast} onClose={hideToast} />
    </div>
  );
};

export default Admin;