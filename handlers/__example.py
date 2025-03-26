from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message
from handlers.base import BaseRouter

# <-- Dataclass test -->
# ps. this file is not used in the project

class ExampleRouter(BaseRouter):
    def __post_init__(self):
        super().__post_init__()
        self._register_handlers()
        
    def _register_handlers(self):
        @self.router.message(Command("start"))
        async def cmd_start(message: Message):
            self.logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
            await message.answer("Привет! Я бот с автоматической инициализацией роутеров!")
        