# URL Shortener API

API-сервис сокращения ссылок на FastAPI с поддержкой кэширования Redis и базой данных PostgreSQL.

## Функциональность

### Основные функции
- **Создание коротких ссылок** (`POST /links/shorten`)
- **Перенаправление** (`GET /{short_code}`)
- **Обновление ссылки** (`PUT /links/{short_code}`)
- **Удаление ссылки** (`DELETE /links/{short_code}`)
- **Статистика по ссылке** (`GET /links/{short_code}/stats`)
- **Поиск по оригинальному URL** (`GET /links/search?original_url={url}`)
- **Кастомные алиасы** (параметр `custom_alias`)
- **Время жизни ссылки** (параметр `expires_at`)

### Дополнительные функции
- Группировка ссылок по проектам
- Создание ссылок для анонимных пользователей
- Автоматическая очистка истекших ссылок

## Технологии

- **FastAPI** - веб-фреймворк
- **PostgreSQL** - основная база данных
- **Redis** - кэширование
- **SQLAlchemy** - ORM
- **JWT** - аутентификация
- **Docker** - контейнеризация

## Установка и запуск

### С использованием Docker (рекомендуется)

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f app
```

Сервис будет доступен по адресу: http://localhost:8000

### Локальный запуск

```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Запуск PostgreSQL и Redis (должны быть установлены)
# Или используйте Docker:
docker-compose up -d db redis

# Запуск приложения
uvicorn src.main:app --reload
```

## API Документация

После запуска доступна интерактивная документация:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Примеры запросов

### Регистрация пользователя
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "testuser", "password": "password123"}'
```

### Авторизация
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

### Создание короткой ссылки
```bash
# Без авторизации
curl -X POST "http://localhost:8000/links/shorten" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com/very/long/url/path"}'

# С авторизацией и кастомным алиасом
curl -X POST "http://localhost:8000/links/shorten" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"original_url": "https://example.com", "custom_alias": "my-link"}'
```

### Получение статистики
```bash
curl -X GET "http://localhost:8000/links/abc123/stats"
```

### Поиск по URL
```bash
curl -X GET "http://localhost:8000/links/search?original_url=https://example.com"
```

## Структура базы данных

### Таблица `users`
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Первичный ключ |
| email | String | Email пользователя |
| username | String | Имя пользователя |
| hashed_password | String | Хэш пароля |
| is_active | Boolean | Активен ли пользователь |
| created_at | DateTime | Дата создания |

### Таблица `links`
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Первичный ключ |
| original_url | String | Оригинальный URL |
| short_code | String | Короткий код |
| custom_alias | String | Кастомный алиас (опционально) |
| click_count | Integer | Количество переходов |
| last_accessed_at | DateTime | Последний переход |
| created_at | DateTime | Дата создания |
| expires_at | DateTime | Дата истечения (опционально) |
| owner_id | Integer | FK на users (опционально) |
| project | String | Проект (опционально) |

## Тестирование

### Запуск тестов
```bash
# Установка тестовых зависимостей
pip install -r requirements.txt

# Запуск всех тестов
pytest tests/

# Запуск с покрытием
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

### Результаты тестирования

**Общая статистика:**
- ✅ **152 теста** успешно пройдено
- 📊 **87% покрытия кода**

**Покрытие по модулям:**

| Модуль | Покрытие |
|--------|----------|
| config.py | 100% |
| models/user.py | 100% |
| routers/auth.py | 100% |
| schemas/user.py | 100% |
| utils/url_helpers.py | 100% |
| models/link.py | 98% |
| schemas/link.py | 94% |
| services/cache_service.py | 93% |
| utils/short_code.py | 92% |
| services/link_service.py | 91% |
| services/auth_service.py | 83% |
| main.py | 78% |
| routers/links.py | 71% |

HTML-отчёт о покрытии доступен в директории `htmlcov/` после запуска тестов.

### Структура тестов
```
tests/
├── conftest.py              # Фикстуры и конфигурация
├── test_functional/         # Функциональные тесты
│   ├── test_auth.py         # Тесты аутентификации
│   └── test_links.py        # Тесты API ссылок
└── test_unit/               # Модульные тесты
    ├── test_auth_service.py
    ├── test_cache_service.py
    ├── test_link_service.py
    ├── test_schemas.py
    └── test_short_code.py
```

### Нагрузочное тестирование
```bash
# Запуск Locust с веб-интерфейсом
locust -f tests/test_load/locustfile.py --host=http://localhost:8000

# Headless режим
locust -f tests/test_load/locustfile.py --host=http://localhost:8000 \
  --headless -u 100 -r 10 -t 60s
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| DATABASE_URL | URL подключения к PostgreSQL | postgresql+asyncpg://postgres:postgres@localhost:5432/shortlinks |
| REDIS_URL | URL подключения к Redis | redis://localhost:6379/0 |
| SECRET_KEY | Секретный ключ для JWT | your-super-secret-key |
| ACCESS_TOKEN_EXPIRE_MINUTES | Время жизни токена | 30 |
| SHORT_CODE_LENGTH | Длина короткого кода | 6 |
| UNUSED_LINK_CLEANUP_DAYS | Дней до очистки | 90 |

## Лицензия

MIT License
