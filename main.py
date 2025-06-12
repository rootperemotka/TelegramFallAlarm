from components.modules import (
    EnvReader,
    Logger
)

import asyncio
import importlib
import os
import inspect

from aiogram import (
    Bot, 
    Dispatcher
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from components.handlers.base import BaseRouter


class App:
    def __init__(
        self
    ) -> None:
        self.env: EnvReader = EnvReader()
        self.logger: Logger = self._logger_init()
        self.bot: Bot = None
        self.dp: Dispatcher = None
        self.des = None
        
    def _logger_init(self):
        logger_settings = {
            key.replace('LOGGER_', '').lower(): value
            for key, value in self.env.env_data.items()
            if key.startswith('LOGGER_')
        }
        return Logger(**logger_settings)
        
    def _init_routers(self):
        handlers_path = self.env.TELEGRAM_HANDLERS_PATH
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_handlers_path = os.path.join(base_dir, handlers_path)
        
        if not os.path.exists(full_handlers_path):
            self.logger.error(f"Директория обработчиков не найдена: {full_handlers_path}")
            return
            
        # Определяем режим мониторинга
        monitor_mode = self.env.get("ALARM_MONITOR_MODE", "channel").lower()
        
        # Выбираем нужный роутер в зависимости от режима
        if monitor_mode == "api":
            router_module = "components.handlers.api_monitor"
            router_class = "ApiMonitorRouter"
        else:  # channel или любое другое значение
            router_module = "components.handlers.channel_monitor"
            router_class = "ChannelMonitorRouter"
            
        try:
            module = importlib.import_module(router_module)
            router_class_obj = getattr(module, router_class)
            router_instance = router_class_obj(self.env, self.logger)
            self.dp.include_router(router_instance.router)
            self.logger.info(f"Загружен роутер: {router_class} (режим: {monitor_mode})")
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке роутера {router_module}.{router_class}: {e}")
        
    async def _init_bot(self):
        if not self.env.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен в .env")
            
        self.bot = Bot(
            token=self.env.TELEGRAM_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.dp = Dispatcher()
        self._init_routers()
        
    async def start(self):
        try:
            await self._init_bot()
            self.logger.info("Бот успешно инициализирован")
            self.logger.info("Начинаем polling...")
            await self.dp.start_polling(self.bot)
        except Exception as e:
            self.logger.error(f"Ошибка при запуске бота: {e}")
            raise
        finally:
            await self.bot.session.close()
            
    def run(self):
        asyncio.run(self.start())
        
def main():
    app = App()
    app.run()


if __name__ == '__main__':
    main()