#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для создания .exe файла на Windows
"""

import os
import sys
import subprocess

def create_exe():
    """Создание .exe файла с помощью PyInstaller"""
    
    print("Создание исполняемого файла для Windows...")
    
    # Команда для PyInstaller
    command = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Один файл
        "--windowed",  # Без консоли
        "--name", "TranscriptionApp",
        "--add-data", "utils.py;.",
        "--add-data", "text_processor.py;.",
        "--add-data", "translation.py;.",
        "--add-data", "transcription.py;.",
        "run_app.py"
    ]
    
    # Добавляем иконку если есть
    if os.path.exists("icon.ico"):
        command.extend(["--icon", "icon.ico"])
    
    try:
        subprocess.run(command, check=True)
        print("\n✅ Исполняемый файл создан!")
        print("📁 Найдите TranscriptionApp.exe в папке dist/")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при создании .exe: {e}")
        print("\n💡 Установите PyInstaller:")
        print("pip install pyinstaller")
        
    except FileNotFoundError:
        print("❌ PyInstaller не найден")
        print("\n💡 Установите PyInstaller:")
        print("pip install pyinstaller")

def install_pyinstaller():
    """Установка PyInstaller"""
    try:
        print("Установка PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✅ PyInstaller установлен!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Ошибка установки PyInstaller")
        return False

def main():
    """Главная функция"""
    print("=== Создание настольного приложения для Windows ===\n")
    
    # Проверяем наличие PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller найден")
    except ImportError:
        print("⚠️ PyInstaller не найден")
        if input("Установить PyInstaller? (y/n): ").lower() == 'y':
            if not install_pyinstaller():
                return
        else:
            print("Без PyInstaller невозможно создать .exe файл")
            return
    
    # Проверяем наличие файлов
    required_files = ["run_app.py", "desktop_app.py", "utils.py", "text_processor.py", "translation.py", "transcription.py"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
        return
    
    print("✅ Все необходимые файлы найдены")
    
    # Создаем .exe
    create_exe()

if __name__ == "__main__":
    main()