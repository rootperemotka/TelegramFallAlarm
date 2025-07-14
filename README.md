# Telegram Fall Alarm Bot


# Краткое руководство

## Клонирование и отправка изменений

```bash
git clone https://git.ccn.rest/peremotka/TelegramFallAlarm.git
cd TelegramFallAlarm
# ...работайте с проектом...
git add .
git commit -m "ваш коммит"
git push
```

## Если репозиторий уже существует локально:

```bash
git remote set-url origin https://git.ccn.rest/peremotka/TelegramFallAlarm.git
git push -u origin main
```

---

# Возможности

- 🔍 Мониторинг каналов Telegram **или** внешнего API (выбирается режим)
- ⏰ Настраиваемый таймаут для проверки
- 👥 Система доступа пользователей
- 📊 Статус мониторинга
- 🔔 Единоразовые уведомления в личные сообщения и звонки при тревоге
- 🐳 Запуск в Docker-контейнере
- 📞 Голосовые уведомления через сервис Звонобот
- 🚨 Автоматические звонки при тревоге

---

# Как работает тревога?

- При срабатывании тревоги (отсутствие сообщений или недоступность API) **уведомление и звонок отправляются только один раз**.
- Как только система восстанавливается (API снова доступен или появляется новое сообщение), счетчик тревоги сбрасывается.
- Повторные уведомления и звонки не отправляются, пока тревога не сброшена.

---

# Установка

## Требования
- Docker
- Docker Compose

## Установка и запуск

1. Клонируйте репозиторий:

```bash
git clone https://git.ccn.rest/peremotka/TelegramFallAlarm.git
cd TelegramFallAlarm
```

2. Настройте переменные окружения в файле `.env` (особенно TELEGRAM_BOT_TOKEN)
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

---

# Настройка

Файл `.env` уже содержит все необходимые настройки (за исключением TELEGRAM_BOT_TOKEN). При необходимости вы можете изменить следующие параметры:

```env
# Telegram Bot Settings
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_HANDLERS_PATH=components/handlers
TELEGRAM_BOT_USERS_ID_ACCESS=all  # или список ID через запятую

# Alarm Settings
ALARM_MONITOR_MODE=api            # режим мониторинга: 'api' или 'channel'
ALARM_MONITOR_CHANNEL_ID=auto     # или ID конкретного канала (для режима channel)
ALARM_TIMEOUT_FOR_MESSAGE=300     # таймаут в секундах
ALARM_MESSAGE_AUTHOR_ID=all       # или ID автора
ALARM_USERS_ID_NOTIFICATION=all   # или список ID через запятую
ALARM_MONITOR_TIMEOUT=60          # интервал проверки в секундах
ALARM_PHONES_FOR_CALL=79XXXXXXXXX,79XXXXXXXXX  # список телефонов для звонков

# Настройки API (для режима 'api')
ALARM_API_URL=http://example.com/alive
ALARM_API_METHOD=GET
ALARM_API_HEADERS=key:value
ALARM_API_BODY=

# Zvonobot Settings
ZVONOBOT_API_KEY=your_api_key     # API-ключ от сервиса Звонобот
ZVONOBOT_OUTGOING_PHONE=79XXXXXXXXX # Номер для исходящих звонков
ZVONOBOT_DUTY_PHONE=0             # Использовать дежурный номер (0 - нет, 1 - да)
ZVONOBOT_VOICE_GENDER=0           # Пол голоса (0 - женский, 1 - мужской)
ZVONOBOT_MESSAGE=                 # Текст сообщения при тревоге (если пусто, будет сгенерирован автоматически)
```

---

# Использование

1. Запустите бота с помощью Docker
2. В Telegram:
   - Отправьте `/start` для просмотра доступных команд
   - Используйте `/start_monitoring` для запуска мониторинга
   - Используйте `/status` для проверки статуса
   - Используйте `/stop_monitoring` для остановки

---

# Команды

- `/start` - Показать информацию о боте и доступных командах
- `/start_monitoring` - Запустить мониторинг (API или каналов, в зависимости от режима)
- `/stop_monitoring` - Остановить мониторинг
- `/status` - Показать текущий статус мониторинга

---

# Разработка

## Структура проекта

```
TelegramFallAlarm/
├── components/
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── __example.py
│   │   ├── base.py
│   │   ├── api_monitor.py
│   │   └── channel_monitor.py
│   ├── logs/
│   └── modules/
│       ├── __init__.py
│       ├── applogger.py
│       ├── envreader.py
│       └── zvonobot.py
├── main.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
└── README.md
```

## Добавление новых роутеров

1. Создайте новый файл в директории `components/handlers/`
2. Унаследуйте класс от `BaseRouter`
3. Реализуйте необходимые обработчики
4. Роутер будет автоматически загружен при запуске (кроме `api_monitor` и `channel_monitor`, которые выбираются по режиму)

---

# Лицензия

MIT License
