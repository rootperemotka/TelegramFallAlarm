from components.modules import (
    EnvLoader,
    Logger
)

from typing import Optional
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
import argparse
from handlers.base import BaseRouter


class App:
    def __init__(
        self,
        default_env: Optional[str] = '.env'
    ) -> None:
        self.env: EnvLoader = EnvLoader(default_env)
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
        handlers_dir = os.path.dirname(os.path.abspath(__file__))
        handlers_path = os.path.join(handlers_dir, 'handlers')
        
        for filename in os.listdir(handlers_path):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = f'handlers.{filename[:-3]}'
                try:
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseRouter) and 
                            obj != BaseRouter):
                            router_instance = obj(self.env, self.logger)
                            self.dp.include_router(router_instance.router)
                            self.logger.info(f"Загружен роутер: {name}")
                except Exception as e:
                    self.logger.error(f"Ошибка при загрузке роутера {module_name}: {e}")
        
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
    parser = argparse.ArgumentParser(description = 'Telegram Fall Alarm Bot')
    parser.add_argument(
        '--env',
        type=str,
        default='.env',
        help='Путь к файлу с переменными окружения (по умолчанию: .env)'
    )
    args = parser.parse_args()
    
    app = App(default_env=args.env)
    app.run()


if __name__ == '__main__':
    main()