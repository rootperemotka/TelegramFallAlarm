import os
import sys
import uuid
import time
import asyncio
import logging
import threading
from functools import wraps
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import (
    Optional,
    Union,
    List,
    Callable,
    Any,
)

from rich.panel import Panel
from rich.console import Console
from rich.traceback import Traceback
from rich.logging import RichHandler


class Logger:
    """
    Продвинутый логгер с поддержкой файлового и консольного вывода, трассировкой выполнения,
    обработкой исключений.
    
    Основные возможности:
    - Ротация лог-файлов
    - Трассировка выполнения функций
    - Автоматическая обработка исключений
    - Подсветка синтаксиса в консоли
    - Измерение времени выполнения
    
    Attributes:
        name (str): Имя логгера
        log_level (str): Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir (str): Директория для хранения лог-файлов
        max_bytes (int): Максимальный размер одного лог-файла
        backup_count (int): Количество резервных копий лог-файлов
        allowed_files (Union[str, List[str]]): Список файлов для трассировки
        code_snippet_lines (int): Количество строк контекста для отображения ошибок
        enable_file_logging (bool): Включение/выключение логирования в файл
        console (Console): Объект для форматированного вывода в консоль
        logger_name (str): Уникальное имя логгера
        logger (logging.Logger): Внутренний объект логгера
    
    Examples:
        # Базовое использование
        >>> logger = Logger(name="MyApp")
        >>> logger.info("Приложение запущено")
        
        # Трассировка функции
        >>> @logger.trace
        >>> def my_function():
        ...     x = 42
        ...     return x
    """
    
    def __init__(
        self,
        name: Optional[str] = "AppLogger",
        add_uuid_to_name: Optional[bool] = True,
        log_level: Optional[str] = "DEBUG",
        log_dir: Optional[str] = "logs",
        max_bytes: Optional[int] = 1024 * 1024,
        backup_count: Optional[int] = 5,
        allowed_files: Union[str, List[str]] = "all",
        code_snippet_lines: Optional[int] = 10,
        enable_file_logging: Optional[bool] = True,
    ):
        """
        Инициализация логгера.
        
        Args:
            name (Optional[str]): Имя логгера. По умолчанию "AppLogger".
            add_uuid_to_name (Optional[bool]): Добавлять ли UUID к имени логгера. По умолчанию True.
            log_level (Optional[str]): Уровень логирования. По умолчанию "DEBUG".
            log_dir (Optional[str]): Директория для лог-файлов. По умолчанию "logs".
            max_bytes (Optional[int]): Максимальный размер лог-файла. По умолчанию 1MB.
            backup_count (Optional[int]): Количество резервных копий. По умолчанию 5.
            allowed_files (Union[str, List[str]]): Список файлов для трассировки. По умолчанию "all".
            code_snippet_lines (Optional[int]): Количество строк контекста. По умолчанию 10.
            enable_file_logging (Optional[bool]): Включить логирование в файл. По умолчанию True.
        """
        self.name = name
        self.log_level = log_level.upper()
        self.log_dir = log_dir
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.allowed_files = allowed_files if allowed_files == "all" or isinstance(allowed_files, list) else "all"
        self.code_snippet_lines = code_snippet_lines
        self.enable_file_logging = enable_file_logging

        self.console = Console(width=120)
        self.logger_name = f"{self.name}-{uuid.uuid4()}" if add_uuid_to_name else self.name
        self._setup_logger()

        self.info = self.logger.info
        self.warning = self.logger.warning
        self.error = self.logger.error
        self.critical = self.logger.critical
        self.debug = self.logger.debug

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.set_exception_handler(self._handle_asyncio_exception)
        sys.excepthook = self._handle_uncaught_exception
        threading.excepthook = lambda args: self._handle_uncaught_exception(args.exc_type, args.exc_value, args.exc_traceback)

    def _setup_logger(self):
        """
        Настройка логгера с файловым и консольным обработчиками.
        
        Создает и настраивает:
        - RotatingFileHandler для ротации лог-файлов
        - RichHandler для форматированного вывода в консоль
        """
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(logging.DEBUG)
        if self.enable_file_logging:
            os.makedirs(self.log_dir, exist_ok=True)
            log_file = os.path.join(self.log_dir, f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
            file_handler = RotatingFileHandler(
                filename=log_file,
                mode="a",
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding="utf-8"
            )
            file_handler.setLevel(self._get_log_level())
            file_formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                "%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        console_handler = RichHandler(console=self.console, rich_tracebacks=True, markup=True)
        console_handler.setLevel(self._get_log_level())
        console_formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

    def _get_log_level(self) -> int:
        """
        Получение числового значения уровня логирования.
        
        Returns:
            int: Числовое значение уровня логирования из модуля logging.
        """
        return getattr(logging, self.log_level, logging.DEBUG)

    def close(self):
        """
        Закрытие всех обработчиков логгера.
        """
        while self.logger.handlers:
            handler = self.logger.handlers[0]
            handler.close()
            self.logger.removeHandler(handler)

    def _handle_uncaught_exception(self, exc_type, exc_value, exc_traceback):
        """
        Обработка неперехваченных исключений.
        
        Args:
            exc_type: Тип исключения
            exc_value: Значение исключения
            exc_traceback: Трейсбек исключения
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        else:
            self.log_exception(exc_type, exc_value, exc_traceback)

    def _handle_asyncio_exception(self, loop, context):
        """
        Обработка исключений asyncio.
        
        Args:
            loop: Event loop asyncio
            context: Контекст исключения
        """
        exception = context.get("exception")
        message = context.get("message")
        self.logger.error(f"Исключение asyncio: {exception or message}")

    def log_exception(self, exc_type, exc_value, exc_traceback):
        """
        Логирование исключения с трейсбеком и контекстом кода.
        
        Args:
            exc_type: Тип исключения
            exc_value: Значение исключения
            exc_traceback: Трейсбек исключения
        """
        try:
            tb = Traceback.from_exception(exc_type, exc_value, exc_traceback)
            self.console.print(tb)
            self.logger.error("Неперехваченное исключение", exc_info=(exc_type, exc_value, exc_traceback))
            self._print_code_snippet(exc_traceback)
        except Exception as e:
            sys.__stderr__.write(f"Ошибка при создании traceback: {e}\n")

    def _print_code_snippet(self, exc_traceback):
        """
        Вывод фрагмента кода с контекстом ошибки.
        
        Args:
            exc_traceback: Трейсбек исключения
        """
        seen_files = set()
        tb = exc_traceback
        while tb is not None:
            frame = tb.tb_frame
            filename = frame.f_code.co_filename
            lineno = tb.tb_lineno
            func_name = frame.f_code.co_name
            if filename in seen_files:
                tb = tb.tb_next
                continue
            seen_files.add(filename)
            if self.allowed_files != "all" and os.path.basename(filename) not in self.allowed_files:
                tb = tb.tb_next
                continue
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                start = max(lineno - self.code_snippet_lines - 1, 0)
                end = min(lineno + self.code_snippet_lines, len(lines))
                snippet_lines = []
                for idx, line in enumerate(lines[start:end], start=start + 1):
                    if idx == lineno:
                        snippet_lines.append(f"[bold red]>> {idx:4}: {line.rstrip()}[/bold red]")
                    else:
                        snippet_lines.append(f"{idx:4}: {line.rstrip()}")
                snippet = "\n".join(snippet_lines)
                msg = (
                    f"[bold blue]Файл:[/bold blue] {filename}\n"
                    f"[bold blue]Функция:[/bold blue] {func_name}\n"
                    f"[bold blue]Строка:[/bold blue] {lineno}\n"
                    f"[bold blue]Контекст ошибки:[/bold blue]\n{snippet}"
                )
                self._print_boxed_text(msg)
            except Exception as e:
                self.logger.error(f"Не удалось прочитать файл {filename}: {e}")
            tb = tb.tb_next

    def _print_boxed_text(self, text: str):
        """
        Вывод текста в рамке с помощью rich.Panel.
        
        Args:
            text (str): Текст для вывода
        """
        panel = Panel(text, title="Ошибка", border_style="bold red", expand=True)
        self.console.print(panel)

    def trace(self, func: Callable) -> Callable:
        """
        Декоратор для трассировки выполнения функции.
        
        Отслеживает:
        - Время выполнения
        - Вызовы других функций
        - Изменения локальных переменных
        - Исключения
        
        Args:
            func (Callable): Функция для трассировки
            
        Returns:
            Callable: Обернутая функция с трассировкой
        """
        def get_frame_depth(frame) -> int:
            depth = 0
            while frame:
                depth += 1
                frame = frame.f_back
            return depth

        def safe_log(log_method, message):
            try:
                log_method(message)
            except Exception as e:
                self.debug(f"Ошибка при логировании: {e}")

        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                safe_log(self.debug, f"Начало выполнения асинхронной функции '{func.__name__}'")
                changes = {}
                last_locals = {}
                base_depth = get_frame_depth(sys._getframe())

                def local_tracer(frame, event, arg):
                    filename = frame.f_code.co_filename
                    if filename.startswith(os.path.dirname(asyncio.__file__)):
                        return local_tracer

                    current_depth = get_frame_depth(frame) - base_depth
                    indent = "    " * max(current_depth, 0)

                    if event == "call":
                        safe_log(self.debug, f"{indent}[CALL] Вызов функции '{frame.f_code.co_name}'")
                    elif event == "line":
                        if frame.f_code == func.__code__:
                            current_locals = frame.f_locals.copy()
                            for var, value in current_locals.items():
                                if var not in last_locals:
                                    safe_log(self.debug, f"{indent}[NEW] Объявлена переменная '{var}': {value!r}")
                                    changes[var] = {"type": "declared", "count": 1}
                                else:
                                    old_val = last_locals[var]
                                    if value != old_val:
                                        safe_log(self.debug, f"{indent}[CHG] Изменение переменной '{var}': {old_val!r} -> {value!r}")
                                        changes[var] = {"type": "changed", "count": changes.get(var, {}).get("count", 0) + 1}
                            for var in last_locals:
                                if var not in current_locals:
                                    safe_log(self.debug, f"{indent}[DEL] Удалена переменная '{var}'")
                                    changes[var] = {"type": "deleted", "count": 1}
                            last_locals.clear()
                            last_locals.update(current_locals)
                    elif event == "return":
                        safe_log(self.debug, f"{indent}[RET] Возврат из функции '{frame.f_code.co_name}'")
                    elif event == "exception":
                        exc_type, exc_value, _ = arg
                        safe_log(self.debug, f"{indent}[ERR] Исключение в функции '{frame.f_code.co_name}': {exc_type.__name__}: {exc_value}")
                    return local_tracer

                original_trace = sys.gettrace()
                sys.settrace(local_tracer)
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                except Exception:
                    elapsed = (time.time() - start_time) * 1000
                    safe_log(self.error, f"Ошибка выполнения '{func.__name__}': {elapsed:.2f} мс")
                    self.log_exception(*sys.exc_info())
                    raise
                finally:
                    sys.settrace(original_trace)
                elapsed = (time.time() - start_time) * 1000
                safe_log(self.info, f"Успешное выполнение '{func.__name__}': {elapsed:.2f} мс")
                if changes:
                    safe_log(self.info, "Статистика изменений переменных:")
                    for var, info in changes.items():
                        safe_log(self.info, f"  {var}: {info['type']} ({info['count']} раз)")
                return result

            return async_wrapper

        else:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                safe_log(self.debug, f"Начало выполнения функции '{func.__name__}'")
                changes = {}
                last_locals = {}
                base_depth = get_frame_depth(sys._getframe())

                def local_tracer(frame, event, arg):
                    filename = frame.f_code.co_filename
                    if filename.startswith(os.path.dirname(asyncio.__file__)):
                        return local_tracer

                    current_depth = get_frame_depth(frame) - base_depth
                    indent = "    " * max(current_depth, 0)

                    if event == "call":
                        safe_log(self.debug, f"{indent}[CALL] Вызов функции '{frame.f_code.co_name}'")
                    elif event == "line":
                        if frame.f_code == func.__code__:
                            current_locals = frame.f_locals.copy()
                            for var, value in current_locals.items():
                                if var not in last_locals:
                                    safe_log(self.debug, f"{indent}[NEW] Объявлена переменная '{var}': {value!r}")
                                    changes[var] = {"type": "declared", "count": 1}
                                else:
                                    old_val = last_locals[var]
                                    if value != old_val:
                                        safe_log(self.debug, f"{indent}[CHG] Изменение переменной '{var}': {old_val!r} -> {value!r}")
                                        changes[var] = {"type": "changed", "count": changes.get(var, {}).get("count", 0) + 1}
                            for var in last_locals:
                                if var not in current_locals:
                                    safe_log(self.debug, f"{indent}[DEL] Удалена переменная '{var}'")
                                    changes[var] = {"type": "deleted", "count": 1}
                            last_locals.clear()
                            last_locals.update(current_locals)
                    elif event == "return":
                        safe_log(self.debug, f"{indent}[RET] Возврат из функции '{frame.f_code.co_name}'")
                    elif event == "exception":
                        exc_type, exc_value, _ = arg
                        safe_log(self.debug, f"{indent}[ERR] Исключение в функции '{frame.f_code.co_name}': {exc_type.__name__}: {exc_value}")
                    return local_tracer

                original_trace = sys.gettrace()
                sys.settrace(local_tracer)
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                except Exception:
                    elapsed = (time.time() - start_time) * 1000
                    safe_log(self.error, f"Ошибка выполнения '{func.__name__}': {elapsed:.2f} мс")
                    self.log_exception(*sys.exc_info())
                    raise
                finally:
                    sys.settrace(original_trace)
                elapsed = (time.time() - start_time) * 1000
                safe_log(self.info, f"Успешное выполнение '{func.__name__}': {elapsed:.2f} мс")
                if changes:
                    safe_log(self.info, "Статистика изменений переменных:")
                    for var, info in changes.items():
                        safe_log(self.info, f"  {var}: {info['type']} ({info['count']} раз)")
                return result

            return wrapper