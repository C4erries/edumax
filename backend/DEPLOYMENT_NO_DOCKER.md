# Развертывание без Docker

## Быстрая инструкция для сервера

### 1. Установка зависимостей на сервере

```bash
# Обновляем систему
apt-get update

# Устанавливаем Python 3.11 и pip
apt-get install -y python3.11 python3.11-venv python3-pip

# Устанавливаем системные зависимости (если нужны для некоторых пакетов)
apt-get install -y gcc
```

### 2. Подготовка проекта

```bash
cd ~/projects/hackathons/hackathon_max/backend

# Создаем виртуальное окружение
python3.11 -m venv .venv

# Активируем виртуальное окружение
source .venv/bin/activate

# Устанавливаем зависимости
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Настройка окружения (опционально)

**Примечание:** Проект работает без `.env` файла, используя значения по умолчанию. Но для продакшена рекомендуется установить `SECRET_KEY`.

#### Вариант А: Без .env (для теста/разработки)
Просто пропустите этот шаг - все будет работать с дефолтными значениями.

#### Вариант Б: С переменными окружения (рекомендуется для продакшена)

Можно установить переменные окружения напрямую или через systemd:

```bash
# Для теста можно экспортировать в текущей сессии
export SECRET_KEY="ваш-очень-длинный-случайный-ключ-для-продакшена"
export DATABASE_URL="sqlite:///./app.db"
```

Или установить в systemd сервисе (см. шаг 5).

### 4. Инициализация базы данных

```bash
# Убедитесь, что виртуальное окружение активировано
source .venv/bin/activate

# Запускаем скрипт инициализации
bash init_db.sh
```

### 5. Запуск приложения

#### Вариант А: Прямой запуск (для теста)

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Вариант Б: Через systemd (для продакшена)

Создайте файл сервиса:

```bash
sudo nano /etc/systemd/system/hackathon-backend.service
```

Содержимое:
```ini
[Unit]
Description=Hackathon Backend API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/projects/hackathons/hackathon_max/backend
Environment="PATH=/root/projects/hackathons/hackathon_max/backend/.venv/bin"
# Опционально: установите SECRET_KEY для продакшена
# Environment="SECRET_KEY=ваш-очень-длинный-случайный-ключ-для-продакшена"
ExecStart=/root/projects/hackathons/hackathon_max/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активируйте и запустите:

```bash
sudo systemctl daemon-reload
sudo systemctl enable hackathon-backend
sudo systemctl start hackathon-backend

# Проверка статуса
sudo systemctl status hackathon-backend

# Логи
sudo journalctl -u hackathon-backend -f
```

### 6. Настройка Nginx (опционально, но рекомендуется)

```bash
# Установка nginx
apt-get install -y nginx

# Создаем конфиг
sudo nano /etc/nginx/sites-available/hackathon-backend
```

Конфигурация:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # или IP адрес

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /root/projects/hackathons/hackathon_max/backend/static;
    }
}
```

Активируем:
```bash
sudo ln -s /etc/nginx/sites-available/hackathon-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. Полезные команды

```bash
# Перезапуск сервиса
sudo systemctl restart hackathon-backend

# Остановка
sudo systemctl stop hackathon-backend

# Логи
sudo journalctl -u hackathon-backend -f --lines 100

# Проверка, что порт слушается
netstat -tlnp | grep 8000
# или
ss -tlnp | grep 8000
```

### 8. Обновление кода

```bash
cd ~/projects/hackathons/hackathon_max/backend

# Обновляем код (git pull или scp новых файлов)
# ...

# Активируем окружение
source .venv/bin/activate

# Обновляем зависимости (если requirements.txt изменился)
pip install -r requirements.txt

# Перезапускаем сервис
sudo systemctl restart hackathon-backend
```

### 9. Бэкап базы данных

```bash
# Создать бэкап
cp app.db app.db.backup.$(date +%Y%m%d_%H%M%S)

# Восстановить из бэкапа
cp app.db.backup.YYYYMMDD_HHMMSS app.db
```

### 10. Troubleshooting

**Проблема: Порт 8000 занят**
```bash
# Найти процесс
lsof -i :8000
# или
netstat -tlnp | grep 8000

# Убить процесс
kill -9 <PID>
```

**Проблема: Модули не найдены**
```bash
# Убедитесь, что виртуальное окружение активировано
source .venv/bin/activate
which python  # Должен показать путь к .venv/bin/python
```

**Проблема: Права доступа**
```bash
# Убедитесь, что у пользователя есть права на директорию
chown -R root:root /root/projects/hackathons/hackathon_max/backend
chmod +x init_db.sh
```

