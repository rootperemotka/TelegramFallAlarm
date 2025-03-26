import os
from typing import Optional

try:
    from rich.table import Table
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

class EnvLoader:
    def __init__(self, env_file: str = None, is_test: Optional[bool] = False):
        self.console = Console() if RICH_AVAILABLE else None
        self.env_data = {}
        self.is_test = is_test
        if env_file:
            self._load_env_file(env_file)
        self._load_envs()
        self._display_env_table()

    def _load_env_file(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл '{file_path}' не найден.")
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, value = map(str.strip, line.split("=", 1))
                os.environ[key] = value

    def _load_envs(self):
        for name, value in os.environ.items():
            self.env_data[name.strip()] = self._convert_type(value.strip())

    def _convert_type(self, value: str):
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        if value.isdigit():
            return int(value)
        try:
            return float(value)
        except ValueError:
            pass
        if "," in value:
            return [v.strip() for v in value.split(",")]
        return value

    def __getattr__(self, name: str):
        if name in self.env_data:
            return self.env_data[name]
        raise AttributeError(f"Переменная окружения '{name}' не найдена.")

    def list_env_vars(self):
        return list(self.env_data.keys())

    def _display_env_table(self):
        if self.is_test:
            return

        if RICH_AVAILABLE:
            table = Table(title="Переменные окружения")
            table.add_column("Переменная", style="bold cyan")
            table.add_column("Значение", style="bold green")

            for key, value in self.env_data.items():
                display_value = "*" * len(str(value)) if any(substr in key.upper() for substr in ["TOKEN", "KEY", "SHA"]) else str(value)
                table.add_row(key, display_value)

            self.console.print(table)
        else:
            print("\nПеременные окружения:")
            print("-" * 50)
            for key, value in self.env_data.items():
                display_value = "*" * len(str(value)) if any(substr in key.upper() for substr in ["TOKEN", "KEY", "SHA"]) else str(value)
                print(f"{key}: {display_value}")
            print("-" * 50)