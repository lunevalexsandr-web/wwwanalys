const API_BASE_URL = 'http://localhost:8000';
let authToken = localStorage.getItem('authToken');
let currentUser = null;

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    setupEventListeners();
});

// Проверка аутентификации
function checkAuth() {
    if (authToken) {
        fetchUserInfo();
    } else {
        showSection('login');
    }
}

// Получение информации о пользователе
async function fetchUserInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/users/me`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            currentUser = await response.json();
            updateUIForAuthenticatedUser();
            showSection('analysis-types');
        } else {
            logout();
        }
    } catch (error) {
        console.error('Error fetching user info:', error);
        logout();
    }
}

// Обновление UI для аутентифицированного пользователя
function updateUIForAuthenticatedUser() {
    document.getElementById('user-info').textContent = `Добро пожаловать, ${currentUser.username}`;
    document.getElementById('logout-btn').style.display = 'block';
    document.querySelector('[data-section="login"]').style.display = 'none';
    
    if (currentUser.is_admin) {
        document.querySelector('[data-section="users"]').style.display = 'block';
    }
    
    document.querySelector('[data-section="analysis-types"]').style.display = 'block';
    document.querySelector('[data-section="process-logs"]').style.display = 'block';
}

// Настройка обработчиков событий
function setupEventListeners() {
    // Обработка навигации
    document.querySelectorAll('[data-section]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.dataset.section;
            showSection(section);
        });
    });
    
    // Обработка выхода
    document.getElementById('logout-btn').addEventListener('click', logout);
    
    // Обработка формы входа
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    
    // Обработка создания типа анализа
    document.getElementById('create-analysis-type-btn').addEventListener('click', () => {
        new bootstrap.Modal(document.getElementById('create-analysis-type-modal')).show();
    });
    
    document.getElementById('add-indicator-btn').addEventListener('click', addIndicatorField);
    document.getElementById('save-analysis-type-btn').addEventListener('click', saveAnalysisType);
    
    // Обработка создания записи журнала
    document.getElementById('create-process-log-btn').addEventListener('click', () => {
        loadAnalysisTypesForDropdown();
        new bootstrap.Modal(document.getElementById('create-process-log-modal')).show();
    });
    
    document.getElementById('save-process-log-btn').addEventListener('click', saveProcessLog);
    
    // Обработка создания пользователя
    document.getElementById('create-user-btn').addEventListener('click', showCreateUserForm);
}

// Показать секцию
function showSection(sectionName) {
    document.querySelectorAll('.card').forEach(card => {
        card.style.display = 'none';
    });
    
    const section = document.getElementById(`${sectionName}-section`);
    if (section) {
        section.style.display = 'block';
    }
    
    // Загрузка данных при необходимости
    if (sectionName === 'analysis-types') {
        loadAnalysisTypes();
    } else if (sectionName === 'process-logs') {
        loadProcessLogs();
    } else if (sectionName === 'users' && currentUser && currentUser.is_admin) {
        loadUsers();
    }
}

// Обработка входа
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);
            fetchUserInfo();
        } else {
            alert('Неверное имя пользователя или пароль');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Ошибка при входе');
    }
}

// Выход
function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    document.getElementById('user-info').textContent = '';
    document.getElementById('logout-btn').style.display = 'none';
    document.querySelector('[data-section="login"]').style.display = 'block';
    document.querySelector('[data-section="users"]').style.display = 'none';
    document.querySelector('[data-section="analysis-types"]').style.display = 'none';
    document.querySelector('[data-section="process-logs"]').style.display = 'none';
    showSection('login');
}

// Загрузка типов анализов
async function loadAnalysisTypes() {
    try {
        const response = await fetch(`${API_BASE_URL}/analysis-types/`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const analysisTypes = await response.json();
            const container = document.getElementById('analysis-types-list');
            container.innerHTML = '';
            
            if (analysisTypes.length === 0) {
                container.innerHTML = '<p class="text-muted">Нет типов анализов</p>';
                return;
            }
            
            analysisTypes.forEach(type => {
                const card = document.createElement('div');
                card.className = 'card mb-3';
                card.innerHTML = `
                    <div class="card-body">
                        <h6 class="card-title">${type.name}</h6>
                        <p class="card-text">${type.description || ''}</p>
                        <small class="text-muted">Индикаторов: ${type.indicators.length}</small>
                    </div>
                `;
                container.appendChild(card);
            });
        }
    } catch (error) {
        console.error('Error loading analysis types:', error);
    }
}

// Добавление поля индикатора
function addIndicatorField() {
    const indicatorsList = document.getElementById('indicators-list');
    const indicatorIndex = indicatorsList.children.length;
    
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'mb-3 p-3 border rounded';
    indicatorDiv.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <h6>Индикатор ${indicatorIndex + 1}</h6>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="this.parentElement.parentElement.remove()">Удалить</button>
        </div>
        <div class="row">
            <div class="col-md-6">
                <input type="text" class="form-control" placeholder="Название индикатора" required>
            </div>
            <div class="col-md-3">
                <input type="text" class="form-control" placeholder="Ед. измерения" required>
            </div>
            <div class="col-md-3">
                <input type="number" class="form-control" placeholder="Мин. значение" step="0.01" required>
            </div>
        </div>
        <div class="row mt-2">
            <div class="col-md-6">
                <input type="number" class="form-control" placeholder="Макс. значение" step="0.01" required>
            </div>
        </div>
    `;
    
    indicatorsList.appendChild(indicatorDiv);
}

// Сохранение типа анализа
async function saveAnalysisType() {
    const name = document.getElementById('analysis-type-name').value;
    const description = document.getElementById('analysis-type-description').value;
    
    const indicators = [];
    const indicatorElements = document.querySelectorAll('#indicators-list > div');
    
    indicatorElements.forEach(element => {
        const name = element.querySelector('input[placeholder="Название индикатора"]').value;
        const unit = element.querySelector('input[placeholder="Ед. измерения"]').value;
        const minValue = parseFloat(element.querySelector('input[placeholder="Мин. значение"]').value);
        const maxValue = parseFloat(element.querySelector('input[placeholder="Макс. значение"]').value);
        
        indicators.push({ name, unit, min_value: minValue, max_value: maxValue });
    });
    
    const analysisTypeData = {
        name,
        description,
        indicators
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/analysis-types/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(analysisTypeData)
        });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('create-analysis-type-modal')).hide();
            document.getElementById('create-analysis-type-form').reset();
            document.getElementById('indicators-list').innerHTML = '';
            loadAnalysisTypes();
        } else {
            alert('Ошибка при сохранении типа анализа');
        }
    } catch (error) {
        console.error('Error saving analysis type:', error);
        alert('Ошибка при сохранении типа анализа');
    }
}

// Загрузка типов анализов для выпадающего списка
async function loadAnalysisTypesForDropdown() {
    try {
        const response = await fetch(`${API_BASE_URL}/analysis-types/`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const analysisTypes = await response.json();
            const select = document.getElementById('process-log-analysis-type');
            select.innerHTML = '<option value="">Выберите тип анализа</option>';
            
            analysisTypes.forEach(type => {
                const option = document.createElement('option');
                option.value = type.id;
                option.textContent = type.name;
                select.appendChild(option);
            });
            
            // Обработка изменения выбора типа анализа
            select.addEventListener('change', function() {
                if (this.value) {
                    loadIndicatorsForProcessLog(this.value);
                } else {
                    document.getElementById('indicator-values-list').innerHTML = '';
                }
            });
        }
    } catch (error) {
        console.error('Error loading analysis types for dropdown:', error);
    }
}

// Загрузка индикаторов для журнала процессов
async function loadIndicatorsForProcessLog(analysisTypeId) {
    try {
        const response = await fetch(`${API_BASE_URL}/analysis-types/${analysisTypeId}/indicators`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const indicators = await response.json();
            const container = document.getElementById('indicator-values-list');
            container.innerHTML = '';
            
            indicators.forEach((indicator, index) => {
                const indicatorDiv = document.createElement('div');
                indicatorDiv.className = 'mb-3';
                indicatorDiv.innerHTML = `
                    <label class="form-label">${indicator.name} (${indicator.unit})</label>
                    <div class="input-group">
                        <input type="number" class="form-control" id="indicator-${index}" step="0.01" required>
                        <input type="hidden" class="indicator-id" value="${indicator.id}">
                        <input type="hidden" class="indicator-name" value="${indicator.name}">
                        <span class="input-group-text">Норма: ${indicator.min_value} - ${indicator.max_value}</span>
                    </div>
                `;
                container.appendChild(indicatorDiv);
            });
        }
    } catch (error) {
        console.error('Error loading indicators for process log:', error);
    }
}

// Сохранение записи журнала
async function saveProcessLog() {
    const analysisTypeId = document.getElementById('process-log-analysis-type').value;
    const notes = document.getElementById('process-log-notes').value;
    
    if (!analysisTypeId) {
        alert('Пожалуйста, выберите тип анализа');
        return;
    }
    
    const indicatorValues = [];
    const indicatorElements = document.querySelectorAll('#indicator-values-list > div');
    
    indicatorElements.forEach(element => {
        const value = parseFloat(element.querySelector('input[type="number"]').value);
        const indicatorId = element.querySelector('.indicator-id').value;
        
        if (!isNaN(value)) {
            indicatorValues.push({
                indicator_id: parseInt(indicatorId),
                value: value
            });
        }
    });
    
    const processLogData = {
        analysis_type_id: parseInt(analysisTypeId),
        notes,
        indicator_values: indicatorValues
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/process-logs/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(processLogData)
        });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('create-process-log-modal')).hide();
            document.getElementById('create-process-log-form').reset();
            document.getElementById('indicator-values-list').innerHTML = '';
            loadProcessLogs();
        } else {
            alert('Ошибка при сохранении записи журнала');
        }
    } catch (error) {
        console.error('Error saving process log:', error);
        alert('Ошибка при сохранении записи журнала');
    }
}

// Загрузка записей журнала
async function loadProcessLogs() {
    try {
        const response = await fetch(`${API_BASE_URL}/process-logs/`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const processLogs = await response.json();
            const container = document.getElementById('process-logs-list');
            container.innerHTML = '';
            
            if (processLogs.length === 0) {
                container.innerHTML = '<p class="text-muted">Нет записей в журнале</p>';
                return;
            }
            
            processLogs.forEach(log => {
                const card = document.createElement('div');
                card.className = 'card mb-3';
                card.innerHTML = `
                    <div class="card-body">
                        <h6 class="card-title">${log.analysis_type?.name || 'Неизвестный тип'}</h6>
                        <p class="card-text">
                            <strong>Статус:</strong> ${log.status}<br>
                            <strong>Дата:</strong> ${new Date(log.started_at).toLocaleString('ru-RU')}<br>
                            ${log.completed_at ? `<strong>Завершено:</strong> ${new Date(log.completed_at).toLocaleString('ru-RU')}<br>` : ''}
                            <strong>Пользователь:</strong> ${log.user?.username || 'Неизвестно'}
                        </p>
                        ${log.notes ? `<p class="card-text"><strong>Примечания:</strong> ${log.notes}</p>` : ''}
                        ${log.indicator_values && log.indicator_values.length > 0 ? `
                            <p class="card-text"><strong>Значения индикаторов:</strong></p>
                            <ul class="list-group list-group-flush">
                                ${log.indicator_values.map(val => `
                                    <li class="list-group-item">
                                        ${val.indicator?.name || 'Неизвестный индикатор'}: ${val.value} ${val.indicator?.unit || ''}
                                    </li>
                                `).join('')}
                            </ul>
                        ` : ''}
                    </div>
                `;
                container.appendChild(card);
            });
        }
    } catch (error) {
        console.error('Error loading process logs:', error);
    }
}

// Загрузка пользователей (только для администраторов)
async function loadUsers() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/users/`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const users = await response.json();
            const container = document.getElementById('users-list');
            container.innerHTML = '';
            
            if (users.length === 0) {
                container.innerHTML = '<p class="text-muted">Нет пользователей</p>';
                return;
            }
            
            users.forEach(user => {
                const card = document.createElement('div');
                card.className = 'card mb-3';
                card.innerHTML = `
                    <div class="card-body">
                        <h6 class="card-title">${user.username}</h6>
                        <p class="card-text">
                            <strong>Email:</strong> ${user.email}<br>
                            <strong>Активен:</strong> ${user.is_active ? 'Да' : 'Нет'}<br>
                            <strong>Администратор:</strong> ${user.is_admin ? 'Да' : 'Нет'}
                        </p>
                    </div>
                `;
                container.appendChild(card);
            });
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Показать форму создания пользователя
function showCreateUserForm() {
    // Здесь можно реализовать модальное окно для создания пользователя
    alert('Функция создания пользователей будет реализована в следующих версиях');
}