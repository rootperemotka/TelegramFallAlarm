# Telegram Fall Alarm Bot

Бот для мониторинга каналов Telegram и отправки уведомлений при отсутствии новых сообщений.

## Возможности

- 🔍 Мониторинг каналов Telegram
- ⏰ Настраиваемый таймаут для проверки сообщений
- 👥 Система доступа пользователей
- 📊 Статус мониторинга
- 🔔 Уведомления в личные сообщения
- 🐳 Запуск в Docker-контейнере
- 📞 Голосовые уведомления через сервис Звонобот
- 🚨 Автоматические звонки при отсутствии сообщений

## Установка

### Требования

- Docker
- Docker Compose

### Установка и запуск

1. Клонируйте репозиторий:

```bash
git clone https://github.com/rootperemotka/TelegramFallAlarm.git
cd TelegramFallAlarm
```

2. Настройте переменные окружения в файле `.env` (особенно добавьте токен бота в TELEGRAM_BOT_TOKEN)
3. Запустите с помощью Docker Compose:

```bash
docker-compose up -d
```

Для просмотра логов:

```bash
docker-compose logs -f
```

Для остановки:

```bash
docker-compose down
```

## Настройка

Файл `.env` уже содержит все необходимые настройки (за исключением TELEGRAM_BOT_TOKEN). При необходимости вы можете изменить следующие параметры:

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
ALARM_PHONES_FOR_CALL=79XXXXXXXXX,79XXXXXXXXX  # список телефонов для звонков

# Zvonobot Settings
ZVONOBOT_API_KEY=your_api_key     # API-ключ от сервиса Звонобот
ZVONOBOT_OUTGOING_PHONE=79XXXXXXXXX # Номер для исходящих звонков
ZVONOBOT_DUTY_PHONE=0             # Использовать дежурный номер (0 - нет, 1 - да)
ZVONOBOT_VOICE_GENDER=0           # Пол голоса (0 - женский, 1 - мужской)
ZVONOBOT_MESSAGE=                 # Текст сообщения при тревоге (если пусто, будет сгенерирован автоматически)
```

## Использование

1. Запустите бота с помощью Docker
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
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── __example.py
│   │   ├── base.py
│   │   └── channel_monitor.py
│   ├── logs/
│   └── modules/
│       ├── __init__.py
│       ├── microenv.py
│       ├── logger.py
│       └── zvonobot.py
├── main.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
└── README.md
```

### Добавление новых роутеров

1. Создайте новый файл в директории `components/handlers/`
2. Унаследуйте класс от `BaseRouter`
3. Реализуйте необходимые обработчики
4. Роутер будет автоматически загружен при запуске

## Обновления

### Последние обновления

- **Docker-интеграция**: Добавлена поддержка Docker и Docker Compose для удобного развертывания
- **Обновление системы работы с переменными окружения**: Замена `EnvLoader` на `EnvReader` с упрощенным механизмом загрузки
- **Упрощение инициализации**: Удалены аргументы командной строки для задания пути к файлу .env
- **Реорганизация структуры проекта**: Улучшена организация файлов и каталогов для большей модульности
- **Интеграция со Звоноботом**: Добавлена возможность отправки голосовых уведомлений через сервис Звонобот
- **Автоматические звонки при тревоге**: При отсутствии сообщений в каналах система автоматически совершает звонки на указанные номера

## Лицензия

MIT License
