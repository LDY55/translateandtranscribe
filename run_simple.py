#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Упрощенный запуск настольного приложения без проверки зависимостей
"""

def main():
    """Простой запуск приложения"""
    try:
        from desktop_app import main as run_desktop_app
        run_desktop_app()
    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        print("\nУстановите недостающие библиотеки:")
        print("pip install numpy requests pydub tqdm nltk")
        print("\nДля транскрибации также:")
        print("pip install torch transformers")
        input("\nНажмите Enter для выхода...")
    except Exception as e:
        print(f"Ошибка запуска: {e}")
        input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()