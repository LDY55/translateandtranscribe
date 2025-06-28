#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой запуск настольного приложения
"""

import sys
import tkinter as tk
from tkinter import messagebox
import subprocess
import os

def check_dependencies():
    """Проверка и установка зависимостей"""
    required_modules = ['numpy', 'requests', 'pydub', 'tqdm', 'nltk']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        root = tk.Tk()
        root.withdraw()  # Скрываем главное окно
        
        result = messagebox.askyesno(
            "Установка зависимостей",
            f"Необходимо установить следующие модули:\n{', '.join(missing_modules)}\n\nУстановить автоматически?"
        )
        
        if result:
            try:
                for module in missing_modules:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", module])
                messagebox.showinfo("Успех", "Все зависимости установлены!")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Ошибка", f"Ошибка при установке модулей: {e}")
                return False
        else:
            messagebox.showwarning("Внимание", 
                "Приложение может работать некорректно без необходимых модулей.\n" +
                "Для полной функциональности также установите: pip install torch transformers")
            
        root.destroy()
    
    return True

def main():
    """Главная функция запуска"""
    # Проверяем зависимости
    if not check_dependencies():
        return
    
    # Запускаем приложение
    try:
        from desktop_app import main as run_app
        run_app()
    except ImportError as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Ошибка", f"Ошибка импорта: {e}")
        root.destroy()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Ошибка", f"Ошибка запуска приложения: {e}")
        root.destroy()

if __name__ == "__main__":
    main()