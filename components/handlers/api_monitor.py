from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message
from components.handlers.base import BaseRouter
from components.modules import ZvonoBot
import asyncio
import aiohttp
from datetime import datetime
from functools import wraps
from typing import Any, List, Dict

class ApiMonitorRouter(BaseRouter):
    def __post_init__(self):
        super().__post_init__()
        self._register_handlers()
        self.last_successful_check = datetime.now()
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
            value = getattr(self.env, key, None)
            
            if value is None:
                self.logger.warning(f"Переменная {key} не найдена, возвращается значение по умолчанию")
                return [] if expected_type == list else expected_type()
            
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
        
    def _parse_headers(self, headers_str: str) -> Dict[str, str]:
        """
        Парсинг строки заголовков в словарь.
        
        Args:
            headers_str (str): Строка заголовков в формате key1:value1,key2:value2
            
        Returns:
            Dict[str, str]: Словарь заголовков
        """
        if not headers_str:
            return {}
            
        headers = {}
        for header in headers_str.split(','):
            if ':' in header:
                key, value = header.split(':', 1)
                headers[key.strip()] = value.strip()
        return headers
        
    def _register_handlers(self):
        @self.router.message(Command("start"))
        @self._check_access
        async def cmd_start(message: Message):
            timeout = self._get_env_value("ALARM_TIMEOUT_FOR_MESSAGE", int)
            monitor_timeout = self._get_env_value("ALARM_MONITOR_TIMEOUT", int)
            api_url = self._get_env_value("ALARM_API_URL")
            api_method = self._get_env_value("ALARM_API_METHOD")
            notify_users = self._get_env_value("ALARM_USERS_ID_NOTIFICATION", list)
            phones_for_call = self._get_env_value("ALARM_PHONES_FOR_CALL", list)
            
            help_text = (
                "👋 Привет! Я бот для мониторинга API.\n\n"
                "📝 Доступные команды:\n"
                "/start_monitoring - Запустить мониторинг API\n"
                "/stop_monitoring - Остановить мониторинг\n"
                "/status - Показать текущий статус мониторинга\n\n"
                "⚙️ Настройки в .env:\n"
                f"• Таймаут: {timeout} сек\n"
                f"• Интервал проверки: {monitor_timeout} сек\n"
                f"• API URL: {api_url}\n"
                f"• Метод: {api_method}\n"
                f"• Получатели уведомлений: {'все' if 'all' in notify_users else ', '.join(notify_users)}\n"
                f"• Телефоны для звонков: {', '.join(phones_for_call) if phones_for_call else 'не указаны'}\n\n"
                "ℹ️ Для начала работы отправьте /start_monitoring"
            )
            await message.answer(help_text)
            
        @self.router.message(Command("status"))
        @self._check_access
        async def cmd_status(message: Message):
            if self.monitoring_task and not self.monitoring_task.done():
                time_since_last = (datetime.now() - self.last_successful_check).total_seconds()
                monitor_timeout = self._get_env_value("ALARM_MONITOR_TIMEOUT", int)
                status_text = (
                    "📊 Статус мониторинга API:\n\n"
                    f"• Мониторинг: ✅ Активен\n"
                    f"• Последняя успешная проверка: {self.last_successful_check.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"• Прошло времени: {int(time_since_last)} сек\n"
                    f"• Следующая проверка через: {max(0, monitor_timeout - time_since_last):.0f} сек"
                )
            else:
                status_text = "📊 Статус мониторинга API:\n\n• Мониторинг: ❌ Неактивен"
            await message.answer(status_text)
            
        @self.router.message(Command("start_monitoring"))
        @self._check_access
        async def cmd_start_monitoring(message: Message):
            if self.monitoring_task is None or self.monitoring_task.done():
                self.monitoring_task = asyncio.create_task(self._monitor_api(message))
                await message.answer("🔍 Мониторинг API запущен")
            else:
                await message.answer("⚠️ Мониторинг уже запущен")
                
        @self.router.message(Command("stop_monitoring"))
        @self._check_access
        async def cmd_stop_monitoring(message: Message):
            if self.monitoring_task and not self.monitoring_task.done():
                self.monitoring_task.cancel()
                await message.answer("🛑 Мониторинг API остановлен")
            else:
                await message.answer("⚠️ Мониторинг не был запущен")
                
    async def _check_api(self) -> bool:
        """
        Проверка доступности API.
        
        Returns:
            bool: True если API доступен, False в противном случае
        """
        try:
            api_url = self._get_env_value("ALARM_API_URL")
            api_method = self._get_env_value("ALARM_API_METHOD")
            headers = self._parse_headers(self._get_env_value("ALARM_API_HEADERS"))
            body = self._get_env_value("ALARM_API_BODY")
            
            async with aiohttp.ClientSession() as session:
                if api_method.upper() == "GET":
                    async with session.get(api_url, headers=headers) as response:
                        return response.status == 200
                elif api_method.upper() == "POST":
                    async with session.post(api_url, headers=headers, data=body) as response:
                        return response.status == 200
                else:
                    self.logger.error(f"Неподдерживаемый метод API: {api_method}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Ошибка при проверке API: {e}")
            return False
            
    async def _make_alarm_calls(self, phones: List[str], api_info: str, timeout: int):
        """
        Выполняет звонки на указанные номера с уведомлением о тревоге.
        
        Args:
            phones (List[str]): Список телефонных номеров
            api_info (str): Информация об API
            timeout (int): Время недоступности API в секундах
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
                message = f"Внимание! API {api_info} недоступен более {timeout} секунд. Требуется проверка системы."
                
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
            api_url = self._get_env_value("ALARM_API_URL")
            timeout = self._get_env_value("ALARM_TIMEOUT_FOR_MESSAGE", int)
            
            notification_text = (
                f"⚠️ ВНИМАНИЕ!\n\n"
                f"API {api_url} недоступен "
                f"более {timeout} секунд!\n"
                f"Последняя успешная проверка была: {self.last_successful_check.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Отправляем уведомление в Telegram
            await notification_message.answer(notification_text)
            self.logger.warning(f"Отправлено уведомление о недоступности API {api_url}")
            
            # Получаем список телефонов для звонка
            phones = self._get_env_value("ALARM_PHONES_FOR_CALL", list)
            
            # Отправляем звонки
            await self._make_alarm_calls(phones, api_url, timeout)
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке уведомления: {e}")
            
    async def _monitor_api(self, notification_message: Message):
        while True:
            try:
                current_time = datetime.now()
                time_diff = (current_time - self.last_successful_check).total_seconds()
                timeout = self._get_env_value("ALARM_TIMEOUT_FOR_MESSAGE", int)
                monitor_timeout = self._get_env_value("ALARM_MONITOR_TIMEOUT", int)
                
                is_api_available = await self._check_api()
                
                if is_api_available:
                    self.last_successful_check = current_time
                elif time_diff > timeout:
                    await self._send_notification(notification_message)
                    self.last_successful_check = current_time
                    
                await asyncio.sleep(monitor_timeout)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Ошибка в мониторинге API: {e}")
                await asyncio.sleep(monitor_timeout) 