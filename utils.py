import json
import os
from pathlib import Path
from typing import Dict, List

def get_supported_audio_formats() -> List[str]:
    """
    Возвращает список поддерживаемых аудиоформатов
    
    Returns:
        List[str]: Список расширений файлов
    """
    return ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac', '.wma', '.mp4']

def load_settings() -> Dict:
    """
    Загружает настройки из файла
    
    Returns:
        Dict: Словарь с настройками
    """
    settings_file = Path("settings.json")
    
    default_settings = {
        'api_endpoint': '',
        'api_token': '',
        'api_model': 'gpt-3.5-turbo',
        'system_prompt': 'Переведи следующий текст на русский язык. Сохрани структуру и стиль оригинала.'
    }
    
    if settings_file.exists():
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                # Объединяем с дефолтными настройками
                default_settings.update(loaded_settings)
        except (json.JSONDecodeError, IOError):
            pass  # Используем дефолтные настройки при ошибке
    
    return default_settings

def save_settings(settings: Dict) -> bool:
    """
    Сохраняет настройки в файл
    
    Args:
        settings: Словарь с настройками
        
    Returns:
        bool: True если сохранение успешно
    """
    settings_file = Path("settings.json")
    
    try:
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False

def format_file_size(size_bytes: int) -> str:
    """
    Форматирует размер файла в человекочитаемый формат
    
    Args:
        size_bytes: Размер в байтах
        
    Returns:
        str: Форматированный размер
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def validate_api_settings(settings: Dict) -> Dict:
    """
    Проверяет корректность настроек API
    
    Args:
        settings: Словарь с настройками
        
    Returns:
        Dict: Результат валидации
    """
    errors = []
    warnings = []
    
    # Проверка обязательных полей
    required_fields = ['api_endpoint', 'api_token']
    for field in required_fields:
        if not settings.get(field, '').strip():
            errors.append(f"Поле '{field}' обязательно для заполнения")
    
    # Проверка формата endpoint
    endpoint = settings.get('api_endpoint', '')
    if endpoint and not (endpoint.startswith('http://') or endpoint.startswith('https://')):
        errors.append("API endpoint должен начинаться с http:// или https://")
    
    # Проверка модели
    model = settings.get('api_model', '')
    if not model.strip():
        warnings.append("Модель не указана, будет использована gpt-3.5-turbo")
    
    # Проверка системного промпта
    prompt = settings.get('system_prompt', '')
    if not prompt.strip():
        warnings.append("Системный промпт пуст")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }

def create_backup_filename(original_path: Path) -> Path:
    """
    Создает имя файла для резервной копии
    
    Args:
        original_path: Путь к оригинальному файлу
        
    Returns:
        Path: Путь к резервной копии
    """
    backup_dir = original_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = int(Path().stat().st_mtime) if original_path.exists() else 0
    backup_name = f"{original_path.stem}_backup_{timestamp}{original_path.suffix}"
    
    return backup_dir / backup_name

def sanitize_filename(filename: str) -> str:
    """
    Очищает имя файла от недопустимых символов
    
    Args:
        filename: Исходное имя файла
        
    Returns:
        str: Очищенное имя файла
    """
    # Удаляем недопустимые символы
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Ограничиваем длину
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        max_name_length = 255 - len(ext)
        filename = name[:max_name_length] + ext
    
    return filename

def get_audio_file_info(file_path: Path) -> Dict:
    """
    Получает информацию об аудиофайле
    
    Args:
        file_path: Путь к аудиофайлу
        
    Returns:
        Dict: Информация о файле
    """
    try:
        from pydub import AudioSegment
        
        audio = AudioSegment.from_file(file_path)
        
        return {
            'duration_seconds': len(audio) / 1000.0,
            'sample_rate': audio.frame_rate,
            'channels': audio.channels,
            'file_size': file_path.stat().st_size,
            'format': file_path.suffix.lower().lstrip('.'),
            'duration_formatted': format_duration(len(audio) / 1000.0)
        }
    except Exception as e:
        return {
            'error': str(e),
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'format': file_path.suffix.lower().lstrip('.')
        }

def format_duration(seconds: float) -> str:
    """
    Форматирует длительность в читаемый формат
    
    Args:
        seconds: Длительность в секундах
        
    Returns:
        str: Форматированная длительность
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def check_disk_space(path: str, required_mb: int = 100) -> bool:
    """
    Проверяет наличие свободного места на диске
    
    Args:
        path: Путь для проверки
        required_mb: Требуемое место в МБ
        
    Returns:
        bool: True если места достаточно
    """
    try:
        import shutil
        free_bytes = shutil.disk_usage(path).free
        free_mb = free_bytes / (1024 * 1024)
        return free_mb >= required_mb
    except:
        return True  # В случае ошибки считаем что места достаточно
