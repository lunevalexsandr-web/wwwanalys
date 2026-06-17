# WWWAnalys Frontend

Фронтенд приложения WWWAnalys — система для управления анализами и шаблонами показателей.

## Технологии

- **React 19** — UI библиотека
- **TypeScript** — статическая типизация
- **Bootstrap 5 + React-Bootstrap** — CSS фреймворк
- **React Router DOM v7** — маршрутизация
- **Vite** — сборщик проектов
- **Axios** — HTTP клиент

## Структура

```
src/
├── main.tsx             # Точка входа
├── App.tsx              # Основной компонент с маршрутизацией
├── App.css              # Стили приложения
├── index.css            # Глобальные стили (Bootstrap кастомизация)
├── components/          # UI компоненты
│   ├── AuthModal.tsx    # Модальное окно авторизации (SaaS-стиль)
│   ├── AuthModal.css    # Стили AuthModal с CSS-переменными
│   ├── AppHeader.tsx    # Шапка приложения
│   ├── AppToast.tsx     # Уведомления (toast)
│   ├── AlertToast.tsx   # Алерты
│   ├── PageHeader.tsx   # Заголовок страницы
│   ├── ActionButtons.tsx    # Кнопки действий
│   ├── IndicatorInput.tsx   # Ввод показателей
│   ├── IndicatorPreview.tsx # Предпросмотр показателей
│   ├── IndicatorSelector.tsx # Выбор показателей
│   └── TemplateBuilder.tsx  # Конструктор шаблонов
├── pages/               # Страницы
│   ├── Login.tsx        # Страница входа
│   ├── Dashboard.tsx    # Панель управления
│   ├── Admin.tsx        # Административная панель
│   └── Plans.tsx        # Планы анализа
├── context/             # React контексты
│   └── AuthContext.tsx  # Контекст аутентификации
├── hooks/               # Кастомные хуки
│   └── useToast.ts      # Хук уведомлений
├── types/               # TypeScript типы
│   └── index.ts
├── api/                 # API клиент
│   └── axios.ts         # Настройка Axios
└── assets/              # Статичные файлы
```

## Установка и запуск

```bash
# Установка зависимостей
npm install

# Запуск dev-сервера
npm run dev

# Сборка для production
npm run build

# Предпросмотр production-сборки
npm run preview
```

## Маршруты

| Путь | Компонент | Описание |
|------|-----------|----------|
| `/login` | Login | Страница входа (публичная) |
| `/dashboard` | Dashboard | Панель управления (требует авторизации) |
| `/admin` | Admin | Административная панель (только для админов) |
| `/plans` | Plans | Планы анализа (требует авторизации) |
| `/` | — | Редирект на `/dashboard` |

## Аутентификация

Используется JWT-аутентификация:
- Токен хранится в `localStorage`
- Интерцептор Axios автоматически добавляет токен в заголовки
- При получении 401 — автоматический редирект на `/login`

## Компонент AuthModal

Модальное окно авторизации в современном SaaS-стиле:

- Центрированная карточка (max-width: 400px)
- Поля ввода с иконками и анимацией фокуса
- Кнопка показа/скрытия пароля
- Социальные кнопки (Google, Bitrix24)
- Адаптивность (90vw на мобильных)
- CSS-переменные для темизации
- Поддержка dark mode

### Использование

```tsx
import AuthModal from './components/AuthModal';

<AuthModal
  show={showModal}
  onHide={() => setShowModal(false)}
  onSuccess={() => navigate('/dashboard')}
/>
```

### Темизация

Изменение цветов через CSS-переменные:

```css
:root {
  --auth-primary: #4e73df;
  --auth-primary-hover: #2e59d9;
  --auth-card-bg: #ffffff;
  --auth-text-primary: #1a1a2e;
  /* ... и другие */
}