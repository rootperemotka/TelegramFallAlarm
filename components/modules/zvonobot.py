import requests
from typing import Dict, Any, Optional, List


class ZvonoBot:
    """
    Класс для работы с API сервиса Звонобот.
    
    Предоставляет интерфейс для совершения автоматических звонков через API Звонобота.
    
    Attributes:
        api_key (str): API-ключ для доступа к сервису Звонобот
        base_url (str): Базовый URL API Звонобота
    
    Examples:
        >>> from components.modules import EnvReader
        >>> env = EnvReader()
        >>> zvonobot = ZvonoBot(api_key=env.ZVONOBOT_API_KEY)
        >>> result = zvonobot.make_call("79123456789", "Это тестовое сообщение")
    """
    
    def __init__(self, api_key: str, base_url: str = "https://lk.zvonobot.ru") -> None:
        """
        Инициализация клиента Звонобота.
        
        Args:
            api_key (str): API-ключ для доступа к сервису Звонобот
            base_url (str): Базовый URL API Звонобота (по умолчанию "https://lk.zvonobot.ru")
        """
        self.api_key = api_key
        self.base_url = base_url
    
    def make_call(
        self, 
        phone: str, 
        message: str, 
        outgoing_phone: Optional[str] = None,
        gender: int = 0,
        duty_phone: int = 0
    ) -> Dict[str, Any]:
        """
        Совершить простой звонок с текстовым сообщением.
        
        Args:
            phone (str): Номер телефона получателя в формате 79XXXXXXXXX
            message (str): Текстовое сообщение, которое будет преобразовано в речь
            outgoing_phone (Optional[str]): Номер телефона, с которого будет совершен звонок
            gender (int): Пол голоса для генерации речи (0 - женский, 1 - мужской)
            duty_phone (int): Использовать дежурный номер (0 - нет, 1 - да)
            
        Returns:
            Dict[str, Any]: Ответ от API Звонобота
            
        Raises:
            ValueError: Если не указан ни outgoing_phone, ни duty_phone
            Exception: При ошибке во время выполнения запроса
        """
        if not outgoing_phone and duty_phone != 1:
            raise ValueError("Необходимо указать либо исходящий номер (outgoing_phone), либо использовать дежурный номер (duty_phone=1)")
        
        endpoint = f"{self.base_url}/apiCalls/create"
        
        payload = {
            "apiKey": self.api_key,
            "phone": phone,
            "record": {
                "text": message,
                "gender": gender
            }
        }
        
        if outgoing_phone:
            payload["outgoingPhone"] = outgoing_phone
        else:
            payload["dutyPhone"] = duty_phone
        
        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка при отправке запроса к Звоноботу: {str(e)}")
    
    def make_bulk_call(
        self, 
        phones: List[str], 
        message: str, 
        outgoing_phone: Optional[str] = None,
        gender: int = 0,
        duty_phone: int = 0
    ) -> Dict[str, Any]:
        """
        Совершить массовый звонок с текстовым сообщением.
        
        Args:
            phones (List[str]): Список номеров телефонов получателей
            message (str): Текстовое сообщение, которое будет преобразовано в речь
            outgoing_phone (Optional[str]): Номер телефона, с которого будет совершен звонок
            gender (int): Пол голоса для генерации речи (0 - женский, 1 - мужской)
            duty_phone (int): Использовать дежурный номер (0 - нет, 1 - да)
            
        Returns:
            Dict[str, Any]: Ответ от API Звонобота
            
        Raises:
            ValueError: Если не указан ни outgoing_phone, ни duty_phone
            Exception: При ошибке во время выполнения запроса
        """
        if not outgoing_phone and duty_phone != 1:
            raise ValueError("Необходимо указать либо исходящий номер (outgoing_phone), либо использовать дежурный номер (duty_phone=1)")
        
        endpoint = f"{self.base_url}/apiCalls/create"
        
        payload = {
            "apiKey": self.api_key,
            "phones": phones,
            "record": {
                "text": message,
                "gender": gender
            }
        }
        
        if outgoing_phone:
            payload["outgoingPhone"] = outgoing_phone
        else:
            payload["dutyPhone"] = duty_phone
        
        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка при отправке запроса к Звоноботу: {str(e)}") 