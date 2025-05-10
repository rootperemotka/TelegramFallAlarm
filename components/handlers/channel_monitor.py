from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message
from components.handlers.base import BaseRouter
from components.modules import ZvonoBot
import asyncio
from datetime import datetime
from functools import wraps
from typing import Any, List

class ChannelMonitorRouter(BaseRouter):
    def __post_init__(self):
        super().__post_init__()
        self._register_handlers()
        self.last_message_time = datetime.now()
        self.monitoring_task = None
        
    def _get_env_value(self, key: str, expected_type: type = str) -> Any:
        """
        Безопасное получение значения из переменных окружения с преобразованием типа.
        
        Args:
            key (str): Ключ переменной окружения
            expected_type (type): Ожидаемый тип данных (str, int, bool, list)
            
        Returns:
            Any: Значение переменной окружения нужного типа или значение по умолчанию
        """
        try:
            # Сначала пробуем получить значение через атрибут
            value = getattr(self.env, key, None)
            
            # Если значение не найдено, возвращаем значение по умолчанию для типа
            if value is None:
                self.logger.warning(f"Переменная {key} не найдена, возвращается значение по умолчанию")
                return [] if expected_type == list else expected_type()
            
            # Преобразуем в нужный тип, если необходимо
            if expected_type == list and isinstance(value, str):
                return [v.strip() for v in value.split(",")]
            elif expected_type == list:
                return value if isinstance(value, list) else []
            elif expected_type == int and not isinstance(value, int):
                return int(value)
            elif expected_type == bool and not isinstance(value, bool):
                return bool(value)
            elif expected_type == str and not isinstance(value, str):
                return str(value)
                
            return value
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении {key} из env: {e}")
            return [] if expected_type == list else expected_type()
            
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
            phones_for_call = self._get_env_value("ALARM_PHONES_FOR_CALL", list)
            
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
                f"• Получатели уведомлений: {'все' if 'all' in notify_users else ', '.join(notify_users)}\n"
                f"• Телефоны для звонков: {', '.join(phones_for_call) if phones_for_call else 'не указаны'}\n\n"
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
    
    async def _make_alarm_calls(self, phones: List[str], channel_info: str, timeout: int):
        """
        Выполняет звонки на указанные номера с уведомлением о тревоге.
        
        Args:
            phones (List[str]): Список телефонных номеров
            channel_info (str): Информация о канале
            timeout (int): Время отсутствия сообщений в секундах
        """
        try:
            if not phones:
                self.logger.warning("Список телефонов для звонка пуст")
                return
                
            api_key = self._get_env_value("ZVONOBOT_API_KEY")
            if not api_key:
                self.logger.error("API-ключ Звонобота не указан в настройках")
                return
                
            outgoing_phone = self._get_env_value("ZVONOBOT_OUTGOING_PHONE")
            duty_phone = self._get_env_value("ZVONOBOT_DUTY_PHONE", int)
            gender = self._get_env_value("ZVONOBOT_VOICE_GENDER", int)
            
            # Получаем сообщение для звонка
            message = self._get_env_value("ZVONOBOT_MESSAGE")
            if not message:
                message = f"Внимание! В {channel_info} не было новых сообщений более {timeout} секунд. Требуется проверка системы."
                
            # Создаем экземпляр Звонобота
            zvonobot = ZvonoBot(api_key=api_key)
            
            # Выполняем звонки
            result = zvonobot.make_bulk_call(
                phones=phones,
                message=message,
                outgoing_phone=outgoing_phone,
                gender=gender,
                duty_phone=duty_phone
            )
            
            self.logger.info(f"Отправлены звонки на номера: {', '.join(phones)}")
            self.logger.debug(f"Результат запроса к Звоноботу: {result}")
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке звонков: {e}")
                
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
            
            # Отправляем уведомление в Telegram
            await notification_message.answer(notification_text)
            self.logger.warning(f"Отправлено уведомление о отсутствии сообщений в {channel_info}")
            
            # Получаем список телефонов для звонка
            phones = self._get_env_value("ALARM_PHONES_FOR_CALL", list)
            
            # Отправляем звонки
            await self._make_alarm_calls(phones, channel_info, timeout)
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке уведомления: {e}") 