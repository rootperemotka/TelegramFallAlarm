from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message
from components.handlers.base import BaseRouter
import asyncio
from datetime import datetime
from functools import wraps
from typing import Any

class ChannelMonitorRouter(BaseRouter):
    def __post_init__(self):
        super().__post_init__()
        self._register_handlers()
        self.last_message_time = datetime.now()
        self.monitoring_task = None
        
    def _get_env_value(self, key: str, expected_type: type = str) -> Any:
        try:
            value = getattr(self.env, key)
            if expected_type == list:
                if isinstance(value, str):
                    return [v.strip() for v in value.split(",")]
                return value if isinstance(value, list) else []
            elif expected_type == int:
                return int(value) if isinstance(value, (str, int)) else 0
            elif expected_type == bool:
                return bool(value) if isinstance(value, (str, bool)) else False
            return str(value)
        except (AttributeError, ValueError) as e:
            self.logger.error(f"Ошибка при получении {key} из env: {e}")
            return expected_type()
            
    def _check_access(self, func):
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            user_id = str(message.from_user.id)
            allowed_users = self._get_env_value("TELEGRAM_BOT_USERS_ID_ACCESS", list)
            
            if "all" in allowed_users:
                return await func(message, *args, **kwargs)
                
            if user_id in allowed_users:
                return await func(message, *args, **kwargs)
                
            self.logger.warning(f"Попытка доступа к боту от неавторизованного пользователя {user_id}")
            await message.answer("⛔️ У вас нет доступа к этому боту")
        return wrapper
        
    def _register_handlers(self):
        @self.router.message(Command("start"))
        @self._check_access
        async def cmd_start(message: Message):
            timeout = self._get_env_value("ALARM_TIMEOUT_FOR_MESSAGE", int)
            monitor_timeout = self._get_env_value("ALARM_MONITOR_TIMEOUT", int)
            channel_id = self._get_env_value("ALARM_MONITOR_CHANNEL_ID")
            author_id = self._get_env_value("ALARM_MESSAGE_AUTHOR_ID")
            notify_users = self._get_env_value("ALARM_USERS_ID_NOTIFICATION", list)
            
            help_text = (
                "👋 Привет! Я бот для мониторинга каналов.\n\n"
                "📝 Доступные команды:\n"
                "/start_monitoring - Запустить мониторинг каналов\n"
                "/stop_monitoring - Остановить мониторинг\n"
                "/status - Показать текущий статус мониторинга\n\n"
                "⚙️ Настройки в .env:\n"
                f"• Таймаут: {timeout} сек\n"
                f"• Интервал проверки: {monitor_timeout} сек\n"
                f"• Мониторинг: {'всех каналов' if channel_id == 'auto' else f'канала {channel_id}'}\n"
                f"• Автор сообщений: {'все' if author_id == 'all' else author_id}\n"
                f"• Получатели уведомлений: {'все' if 'all' in notify_users else ', '.join(notify_users)}\n\n"
                "ℹ️ Для начала работы отправьте /start_monitoring"
            )
            await message.answer(help_text)
            
        @self.router.message(Command("status"))
        @self._check_access
        async def cmd_status(message: Message):
            if self.monitoring_task and not self.monitoring_task.done():
                time_since_last = (datetime.now() - self.last_message_time).total_seconds()
                monitor_timeout = self._get_env_value("ALARM_MONITOR_TIMEOUT", int)
                status_text = (
                    "📊 Статус мониторинга:\n\n"
                    f"• Мониторинг: ✅ Активен\n"
                    f"• Последнее сообщение: {self.last_message_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"• Прошло времени: {int(time_since_last)} сек\n"
                    f"• Следующая проверка через: {max(0, monitor_timeout - time_since_last):.0f} сек"
                )
            else:
                status_text = "📊 Статус мониторинга:\n\n• Мониторинг: ❌ Неактивен"
            await message.answer(status_text)
            
        @self.router.message(Command("start_monitoring"))
        @self._check_access
        async def cmd_start_monitoring(message: Message):
            if self.monitoring_task is None or self.monitoring_task.done():
                self.monitoring_task = asyncio.create_task(self._monitor_channel(message))
                await message.answer("🔍 Мониторинг канала запущен")
            else:
                await message.answer("⚠️ Мониторинг уже запущен")
                
        @self.router.message(Command("stop_monitoring"))
        @self._check_access
        async def cmd_stop_monitoring(message: Message):
            if self.monitoring_task and not self.monitoring_task.done():
                self.monitoring_task.cancel()
                await message.answer("🛑 Мониторинг канала остановлен")
            else:
                await message.answer("⚠️ Мониторинг не был запущен")
                
        @self.router.message(F.chat.type.in_({"channel", "group"}))
        async def handle_channel_message(message: Message):
            self.last_message_time = datetime.now()
            
    async def _monitor_channel(self, notification_message: Message):
        while True:
            try:
                current_time = datetime.now()
                time_diff = (current_time - self.last_message_time).total_seconds()
                timeout = self._get_env_value("ALARM_TIMEOUT_FOR_MESSAGE", int)
                monitor_timeout = self._get_env_value("ALARM_MONITOR_TIMEOUT", int)
                
                if time_diff > timeout:
                    await self._send_notification(notification_message)
                    self.last_message_time = current_time
                    
                await asyncio.sleep(monitor_timeout)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Ошибка в мониторинге канала: {e}")
                await asyncio.sleep(monitor_timeout)
                
    async def _send_notification(self, notification_message: Message):
        try:
            channel_id = self._get_env_value("ALARM_MONITOR_CHANNEL_ID")
            timeout = self._get_env_value("ALARM_TIMEOUT_FOR_MESSAGE", int)
            channel_info = "всех каналах" if channel_id == "auto" else f"канале {channel_id}"
            
            notification_text = (
                f"⚠️ ВНИМАНИЕ!\n\n"
                f"В {channel_info} не было новых сообщений "
                f"более {timeout} секунд!\n"
                f"Последнее сообщение было: {self.last_message_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            await notification_message.answer(notification_text)
            self.logger.warning(f"Отправлено уведомление о отсутствии сообщений в {channel_info}")
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке уведомления: {e}") 