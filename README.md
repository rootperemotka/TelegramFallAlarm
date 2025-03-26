# Telegram Fall Alarm Bot

Бот для мониторинга каналов Telegram и отправки уведомлений при отсутствии новых сообщений.

## Возможности

- 🔍 Мониторинг каналов Telegram
- ⏰ Настраиваемый таймаут для проверки сообщений
- 👥 Система доступа пользователей
- 📊 Статус мониторинга
- 🔔 Уведомления в личные сообщения

## Установка

### Требования

- Python 3.8+
- pip
- git

### Автоматическая установка

#### Linux/macOS

```bash
chmod +x run.sh
./run.sh
```

#### Windows

```batch
run.bat
```

### Ручная установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/rootperemotka/TelegramFallAlarm.git
cd TelegramFallAlarm
```

2. Создайте виртуальное окружение:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Установите зависимости:

```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

## Настройка

Отредактируйте файл `.env`:

```env
# Telegram Bot Settings
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_HANDLERS_PATH=components/handlers
TELEGRAM_BOT_USERS_ID_ACCESS=all  # или список ID через запятую

# Alarm Settings
ALARM_MONITOR_CHANNEL_ID=auto     # или ID конкретного канала
ALARM_TIMEOUT_FOR_MESSAGE=300     # таймаут в секундах
ALARM_MESSAGE_AUTHOR_ID=all       # или ID автора
ALARM_USERS_ID_NOTIFICATION=all   # или список ID через запятую
ALARM_MONITOR_TIMEOUT=60          # интервал проверки в секундах
```

## Использование

1. Запустите бота:

```bash
python main.py
```

2. В Telegram:
   - Отправьте `/start` для просмотра доступных команд
   - Используйте `/start_monitoring` для запуска мониторинга
   - Используйте `/status` для проверки статуса
   - Используйте `/stop_monitoring` для остановки

## Команды

- `/start` - Показать информацию о боте и доступных командах
- `/start_monitoring` - Запустить мониторинг каналов
- `/stop_monitoring` - Остановить мониторинг
- `/status` - Показать текущий статус мониторинга

## Разработка

### Структура проекта

```
TelegramFallAlarm/
├── components/
│   └── modules/
│       ├── __init__.py
│       ├── microenv.py
│       └── logger.py
├── handlers/
│   ├── __init__.py
│   ├── base.py
│   └── channel_monitor.py
├── main.py
├── requirements.txt
└── README.md
```

### Добавление новых роутеров

1. Создайте новый файл в директории `handlers/`
2. Унаследуйте класс от `BaseRouter`
3. Реализуйте необходимые обработчики
4. Роутер будет автоматически загружен при запуске

## Лицензия

MIT License
