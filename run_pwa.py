#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Запуск PWA приложения с проверкой зависимостей
"""

import sys
import subprocess
import os

def check_flask():
    """Проверка Flask"""
    try:
        import flask
        return True
    except ImportError:
        return False

def install_flask():
    """Установка Flask"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Главная функция"""
    print("=== PWA Приложение для транскрибации и перевода ===\n")
    
    # Проверяем Flask
    if not check_flask():
        print("Flask не найден. Устанавливаю...")
        if not install_flask():
            print("❌ Ошибка установки Flask")
            print("Попробуйте вручную: pip install flask")
            input("Нажмите Enter для выхода...")
            return
        print("✅ Flask установлен!")
    
    # Запускаем приложение
    try:
        from pwa_simple import app
        print("\n🚀 Запуск PWA приложения...")
        print("📱 Откройте в браузере: http://localhost:5000")
        print("💡 Для установки на рабочий стол:")
        print("   1. Откройте меню браузера (три точки)")
        print("   2. Выберите 'Установить приложение'")
        print("   3. Приложение появится на рабочем столе\n")
        
        app.run(debug=False, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        input("Нажмите Enter для выхода...")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()