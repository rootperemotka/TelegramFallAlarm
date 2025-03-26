@echo off
echo Telegram Fall Alarm Bot - Установка
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python не установлен. Пожалуйста, установите Python 3.8 или выше.
    pause
    exit /b 1
)

REM Проверка наличия pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo pip не установлен. Пожалуйста, установите pip.
    pause
    exit /b 1
)

REM Создание виртуального окружения
echo Создание виртуального окружения...
python -m venv venv

REM Активация виртуального окружения
echo Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Установка зависимостей
echo Установка зависимостей...
pip install -r requirements.txt

REM Запуск бота
echo Запуск бота...
python main.py 