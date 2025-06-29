import requests
import json
import time
from typing import Optional

class TranslationProcessor:
    """Класс для перевода текста через API"""
    
    def __init__(self, api_endpoint: str, api_token: str, model: str = "gpt-3.5-turbo", 
                 system_prompt: str = "Переведи следующий текст на русский язык."):
        self.api_endpoint = api_endpoint
        self.api_token = api_token
        self.model = model
        self.system_prompt = system_prompt
        self.session = requests.Session()
        
        # Настройка заголовков
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_token}'
        })
    
    def translate_text(self, text: str, retry_count: int = 3) -> str:
        """
        Перевод текста через API
        
        Args:
            text: Текст для перевода
            retry_count: Количество повторных попыток при ошибке
            
        Returns:
            str: Переведенный текст
        """
        if not text.strip():
            return text
        
        # Подготовка данных для API запроса
        payload = self._prepare_payload(text)
        
        for attempt in range(retry_count):
            try:
                response = self.session.post(
                    self.api_endpoint,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return self._extract_translation(result)
                elif response.status_code == 429:  # Rate limit
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                else:
                    error_message = f"HTTP {response.status_code}"
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            msg = data.get("error") or data.get("message")
                            if msg:
                                error_message += f" - {msg}"
                    except Exception:
                        if response.text:
                            error_message += f" - {response.text}"
                    raise Exception(f"Ошибка API: {error_message}")
                    
            except requests.exceptions.Timeout:
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise Exception("Превышено время ожидания ответа от API")
            
            except requests.exceptions.RequestException as e:
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise Exception(f"Ошибка при обращении к API: {str(e)}")
        
        raise Exception("Не удалось получить перевод после нескольких попыток")
    
    def _prepare_payload(self, text: str) -> dict:
        """
        Подготовка payload для API запроса
        Поддерживает различные форматы API (OpenAI, Claude, etc.)
        """
        # Базовый формат для OpenAI-совместимых API
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user", 
                    "content": text
                }
            ],
            "max_tokens": 4000,
            "temperature": 0.3
        }
        
        return payload
    
    def _extract_translation(self, response_data: dict) -> str:
        """
        Извлечение переведенного текста из ответа API
        """
        try:
            # Формат OpenAI API
            if 'choices' in response_data:
                return response_data['choices'][0]['message']['content'].strip()
            
            # Формат Claude API
            elif 'content' in response_data:
                if isinstance(response_data['content'], list):
                    return response_data['content'][0].get('text', '').strip()
                else:
                    return response_data['content'].strip()
            
            # Общий fallback
            elif 'text' in response_data:
                return response_data['text'].strip()
            
            else:
                raise Exception("Неизвестный формат ответа API")
                
        except (KeyError, IndexError, TypeError) as e:
            raise Exception(f"Ошибка при извлечении перевода из ответа: {str(e)}")
    
    def test_connection(self) -> dict:
        """
        Тестирование подключения к API
        
        Returns:
            dict: Результат тестирования
        """
        try:
            test_text = "Hello, world!"
            result = self.translate_text(test_text)
            
            return {
                'success': True,
                'message': 'Подключение к API успешно',
                'test_translation': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка подключения: {str(e)}'
            }
    
    def estimate_cost(self, text: str, cost_per_1k_tokens: float = 0.002) -> dict:
        """
        Приблизительная оценка стоимости перевода
        
        Args:
            text: Текст для оценки
            cost_per_1k_tokens: Стоимость за 1000 токенов
            
        Returns:
            dict: Информация о стоимости
        """
        # Приблизительный подсчет токенов (1 токен ≈ 4 символа для английского)
        estimated_tokens = len(text) // 3  # Более консервативная оценка
        estimated_cost = (estimated_tokens / 1000) * cost_per_1k_tokens
        
        return {
            'estimated_tokens': estimated_tokens,
            'estimated_cost_usd': round(estimated_cost, 4),
            'text_length': len(text)
        }
