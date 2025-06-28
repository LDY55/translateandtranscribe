#!/usr/bin/env python3
"""
Тест для проверки транскрибации
"""

def test_dependencies():
    """Проверка доступности зависимостей"""
    print("🔍 Проверка зависимостей...")
    
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
        print(f"📱 CUDA доступна: {torch.cuda.is_available()}")
    except ImportError:
        print("❌ PyTorch не установлен")
        return False
    
    try:
        import transformers
        print(f"✅ Transformers: {transformers.__version__}")
    except ImportError:
        print("❌ Transformers не установлен")
        return False
    
    try:
        from pydub import AudioSegment
        print("✅ PyDub доступен")
    except ImportError:
        print("❌ PyDub не доступен")
        return False
    
    return True

def test_transcription_simple():
    """Простой тест транскрибации"""
    print("\n🎤 Тестирование простой транскрибации...")
    
    if not test_dependencies():
        print("❌ Зависимости недоступны")
        return
    
    try:
        from transcription_simple import TranscriptionProcessor
        
        processor = TranscriptionProcessor()
        info = processor.get_model_info()
        print(f"📊 Модель загружена: {info['model_loaded']}")
        print(f"🖥️ Устройство: {info['device']}")
        
        print("✅ Тест прошел успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_transcription_simple()