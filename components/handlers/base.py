from aiogram import Router
from components.modules import EnvReader, Logger
from dataclasses import dataclass

@dataclass
class BaseRouter:
    env: EnvReader
    logger: Logger
    
    def __post_init__(self):
        self.router = Router() 