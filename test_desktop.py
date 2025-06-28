#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест настольного приложения
"""

def test_imports():
    """Тестирование импорта модулей"""
    print("Тестирование импорта модулей...")
    
    try:
        import tkinter as tk
        print("✅ tkinter: OK")
    except ImportError as e:
        print(f"❌ tkinter: {e}")
        return False
    
    try:
        from utils import get_supported_audio_formats, load_settings
        print("✅ utils: OK")
    except ImportError as e:
        print(f"❌ utils: {e}")
        return False
    
    try:
        from text_processor import TextProcessor
        print("✅ text_processor: OK")
    except ImportError as e:
        print(f"❌ text_processor: {e}")
        return False
    
    try:
        from translation import TranslationProcessor
        print("✅ translation: OK")
    except ImportError as e:
        print(f"❌ translation: {e}")
        return False
    
    try:
        from transcription import TRANSFORMERS_AVAILABLE
        if TRANSFORMERS_AVAILABLE:
            print("✅ transcription (с PyTorch): OK")
        else:
            print("⚠️ transcription (без PyTorch): OK")
    except ImportError as e:
        print(f"❌ transcription: {e}")
        return False
    
    return True

def test_desktop_app():
    """Тестирование запуска desktop приложения"""
    print("\nТестирование desktop приложения...")
    
    try:
        # Создаем невидимое окно для теста
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Скрываем окно
        
        from desktop_app import AudioTranscriptionApp
        
        # Создаем приложение
        app = AudioTranscriptionApp(root)
        print("✅ Desktop приложение создано успешно")
        
        # Закрываем тестовое окно
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания desktop приложения: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("=== Тестирование настольного приложения ===\n")
    
    # Тест импортов
    if not test_imports():
        print("\n❌ Ошибки при импорте модулей")
        return
    
    # Тест создания приложения
    if not test_desktop_app():
        print("\n❌ Ошибки при создании приложения")
        return
    
    print("\n✅ Все тесты прошли успешно!")
    print("\nДля запуска приложения используйте:")
    print("python run_app.py")

if __name__ == "__main__":
    main()