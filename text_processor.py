import re
import nltk
from typing import List
import os

class TextProcessor:
    """Класс для обработки и разбивки текста на чанки"""
    
    def __init__(self):
        self._download_nltk_data()
    
    def _download_nltk_data(self):
        """Скачивание необходимых данных NLTK"""
        try:
            # Проверяем, есть ли уже скачанные данные
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            try:
                nltk.download('punkt', quiet=True)
            except Exception:
                # Если NLTK недоступен, будем использовать простую регулярку
                pass
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Разбивка текста на предложения
        
        Args:
            text: Исходный текст
            
        Returns:
            List[str]: Список предложений
        """
        try:
            # Попытка использовать NLTK
            sentences = nltk.sent_tokenize(text, language='russian')
            return [s.strip() for s in sentences if s.strip()]
        except:
            # Fallback на простую регулярку
            return self._simple_sentence_split(text)
    
    def _simple_sentence_split(self, text: str) -> List[str]:
        """
        Простая разбивка на предложения с помощью регулярных выражений
        """
        # Паттерн для разбивки на предложения
        sentence_pattern = r'(?<=[.!?])\s+(?=[А-ЯA-Z])'
        sentences = re.split(sentence_pattern, text)
        
        # Очистка и фильтрация
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 3:  # Минимальная длина предложения
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def split_into_chunks(self, text: str, sentences_per_chunk: int = 30) -> List[str]:
        """
        Разбивка текста на чанки по количеству предложений
        
        Args:
            text: Исходный текст
            sentences_per_chunk: Количество предложений в одном чанке
            
        Returns:
            List[str]: Список чанков текста
        """
        sentences = self.split_into_sentences(text)
        
        if not sentences:
            return [text]  # Возвращаем исходный текст если не удалось разбить
        
        chunks = []
        for i in range(0, len(sentences), sentences_per_chunk):
            chunk_sentences = sentences[i:i + sentences_per_chunk]
            chunk_text = ' '.join(chunk_sentences)
            chunks.append(chunk_text)
        
        return chunks
    
    def split_by_paragraphs(self, text: str) -> List[str]:
        """
        Разбивка текста на параграфы
        
        Args:
            text: Исходный текст
            
        Returns:
            List[str]: Список параграфов
        """
        # Разбивка по двойным переносам строк
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def smart_chunk_split(self, text: str, max_chunk_size: int = 3000, 
                         preferred_sentences: int = 30) -> List[str]:
        """
        Умная разбивка текста на чанки с учетом размера и предложений
        
        Args:
            text: Исходный текст
            max_chunk_size: Максимальный размер чанка в символах
            preferred_sentences: Предпочтительное количество предложений
            
        Returns:
            List[str]: Список чанков текста
        """
        sentences = self.split_into_sentences(text)
        
        if not sentences:
            return self._split_by_size(text, max_chunk_size)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # Проверяем, помещается ли предложение в текущий чанк
            if (len(current_chunk) < preferred_sentences and 
                current_size + sentence_size <= max_chunk_size):
                current_chunk.append(sentence)
                current_size += sentence_size
            else:
                # Сохраняем текущий чанк и начинаем новый
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                
                current_chunk = [sentence]
                current_size = sentence_size
                
                # Если одно предложение больше лимита, разбиваем его
                if sentence_size > max_chunk_size:
                    split_parts = self._split_by_size(sentence, max_chunk_size)
                    chunks.extend(split_parts[:-1])  # Добавляем все части кроме последней
                    current_chunk = [split_parts[-1]] if split_parts else []
                    current_size = len(split_parts[-1]) if split_parts else 0
        
        # Добавляем последний чанк
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _split_by_size(self, text: str, chunk_size: int) -> List[str]:
        """
        Разбивка текста по размеру (fallback метод)
        """
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i + chunk_size])
        return chunks
    
    def clean_text(self, text: str) -> str:
        """
        Очистка текста от лишних символов и форматирования
        
        Args:
            text: Исходный текст
            
        Returns:
            str: Очищенный текст
        """
        # Удаляем избыточные пробелы и переносы
        text = re.sub(r'\s+', ' ', text)
        
        # Удаляем специальные символы (оставляем базовую пунктуацию)
        text = re.sub(r'[^\w\s.,!?;:()\-—""«»]', '', text)
        
        # Нормализуем кавычки
        text = re.sub(r'[""«»]', '"', text)
        
        return text.strip()
    
    def get_text_stats(self, text: str) -> dict:
        """
        Получение статистики по тексту
        
        Args:
            text: Исходный текст
            
        Returns:
            dict: Статистика текста
        """
        sentences = self.split_into_sentences(text)
        words = text.split()
        paragraphs = self.split_by_paragraphs(text)
        
        return {
            'characters': len(text),
            'characters_no_spaces': len(text.replace(' ', '')),
            'words': len(words),
            'sentences': len(sentences),
            'paragraphs': len(paragraphs),
            'avg_sentence_length': len(words) / max(len(sentences), 1),
            'avg_word_length': sum(len(word) for word in words) / max(len(words), 1)
        }
