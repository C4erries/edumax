# Инструкция по развертыванию

## Быстрый старт

### 1. Подготовка

```bash
cd backend
cp .env.example .env
# Отредактируйте .env файл, установите SECRET_KEY
```

### 2. Запуск через Docker Compose

```bash
# Создать и запустить контейнер
docker-compose up -d

# Посмотреть логи
docker-compose logs -f backend

# Остановить
docker-compose down

# Остановить и удалить volumes (удалит БД!)
docker-compose down -v
```

### 3. Инициализация базы данных

После первого запуска нужно создать таблицы и загрузить данные:

```bash
# Войти в контейнер backend
docker-compose exec backend bash

# Создать таблицы
python -c "from app.db.base import Base; from app.db.session import engine; Base.metadata.create_all(bind=engine)"

# Загрузить начальные данные
python seed_data.py
python seed_students.py
python seed_schedule.py
python seed_events.py
python seed_electives.py
```

Или все в одной команде (рекомендуется):

```bash
docker-compose exec backend bash /app/init_db.sh
```

**Скрипт автоматически загрузит:**
- Университеты, факультеты, группы
- Тестовых студентов и преподавателей  
- Расписание занятий
- **20+ тематических событий** (бизнес-куб, встречи с экспертами, хакатоны, конференции, мастер-классы и др.)
- **22+ элективных курса** (программирование, дизайн, языки, бизнес, личностное развитие и др.)

### 4. Проверка

Откройте в браузере:
- API: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## База данных SQLite

Проект использует SQLite для простоты развертывания. База данных хранится в файле `app.db` в корне проекта.

**Важно:** Файл `app.db` сохраняется в Docker volume `db_data`, поэтому данные не потеряются при перезапуске контейнера.

### Бэкап базы данных

```bash
# Создать бэкап
docker-compose exec backend cp app.db app.db.backup

# Или скопировать из контейнера
docker cp hackathon_backend:/app/app.db ./backup_$(date +%Y%m%d_%H%M%S).db

# Восстановить из бэкапа
docker cp ./backup.db hackathon_backend:/app/app.db
```

## Продакшен развертывание

### 1. Обновите .env для продакшена

```env
SECRET_KEY=очень-длинный-случайный-ключ-для-продакшена
YOOKASSA_SHOP_ID=ваш-реальный-id
YOOKASSA_SECRET_KEY=ваш-реальный-ключ
YOOKASSA_TEST_MODE=false
```

### 2. Используйте production-ready команду

В `docker-compose.yml` измените команду для backend:

```yaml
command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Настройте reverse proxy (nginx)

Пример конфигурации nginx:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/static;
    }
}
```

## Мониторинг

```bash
# Статус контейнера
docker-compose ps

# Логи
docker-compose logs -f

# Использование ресурсов
docker stats hackathon_backend
```

## Полезные команды

```bash
# Пересобрать контейнер после изменений
docker-compose up -d --build

# Перезапустить сервис
docker-compose restart backend

# Посмотреть логи
docker-compose logs -f backend

# Выполнить команду в контейнере
docker-compose exec backend python -c "print('Hello from container')"

# Очистить все (контейнеры, volumes, сети)
docker-compose down -v --remove-orphans
```

## Troubleshooting

### Проблема: Порт 8000 занят

Измените порт в `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Внешний порт:внутренний порт
```

### Проблема: Статика не отдается

Проверьте, что volume `static_data` создан:

```bash
docker volume ls | grep static
```

### Проблема: База данных не сохраняется

Убедитесь, что volume `db_data` создан и подключен:

```bash
docker volume ls | grep db_data
docker-compose exec backend ls -la /app/app.db
```

### Проблема: Изменения в коде не применяются

Убедитесь, что volume с кодом подключен:

```yaml
volumes:
  - .:/app  # Это должно быть в docker-compose.yml
```
