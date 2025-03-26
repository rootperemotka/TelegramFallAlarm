#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Telegram Fall Alarm Bot - Установка${NC}\n"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 не установлен. Пожалуйста, установите Python 3.8 или выше.${NC}"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}pip3 не установлен. Пожалуйста, установите pip3.${NC}"
    exit 1
fi

echo -e "${YELLOW}Создание виртуального окружения...${NC}"
python3 -m venv venv

echo -e "${YELLOW}Активация виртуального окружения...${NC}"
source venv/bin/activate

echo -e "${YELLOW}Установка зависимостей...${NC}"
pip install -r requirements.txt

echo -e "${GREEN}Запуск бота...${NC}"
python main.py 