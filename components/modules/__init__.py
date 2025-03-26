import os
import warnings
import importlib
from typing import List

def initialize_modules() -> List[str]:
    modules = []
    base_dir = os.path.dirname(__file__)
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".py") and file != '__init__.py':
                relative_path = os.path.relpath(os.path.join(root, file), base_dir)
                module_name = relative_path[:-3].replace(os.sep, ".")
                try:
                    module = importlib.import_module(f".{module_name}", __name__)
                    globals().update({
                        name: obj
                        for name, obj in module.__dict__.items()
                        if not name.startswith("_")
                    })
                    modules.append(module_name)
                except ImportError as e:
                    warnings.warn(f"Не удалось импортировать модуль {module_name}: {e}")
                    continue
    return modules

initialize_modules()
