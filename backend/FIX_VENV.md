# Исправление проблемы с виртуальным окружением

## Проблема: externally-managed-environment

Эта ошибка возникает, когда используется системный pip вместо pip из виртуального окружения.

## Решение

### Вариант 1: Использовать python -m pip (рекомендуется)

```bash
# Убедитесь, что виртуальное окружение активировано
source .venv/bin/activate

# Используйте python -m pip вместо просто pip
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Вариант 2: Проверить, что используется правильный pip

```bash
# Проверьте, какой pip используется
which pip
# Должно быть: /root/projects/hackathons/hackathon_max/backend/.venv/bin/pip

# Если показывает системный путь, пересоздайте виртуальное окружение
deactivate  # если активировано
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate

# Теперь проверьте снова
which pip
which python

# Установите зависимости
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Вариант 3: Установить python3-full (если виртуальное окружение не работает)

```bash
apt-get install -y python3-full python3-venv

# Пересоздайте виртуальное окружение
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate

# Установите зависимости
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Проверка

После установки проверьте:

```bash
# Должно показать путь к .venv
which python
which pip

# Должно работать без ошибок
python -c "import fastapi; print('OK')"
```

