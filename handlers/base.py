from aiogram import Router
from components.modules import EnvLoader, Logger
from dataclasses import dataclass

@dataclass
class BaseRouter:
    env: EnvLoader
    logger: Logger
    
    def __post_init__(self):
        self.router = Router() 