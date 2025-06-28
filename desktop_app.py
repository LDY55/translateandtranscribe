#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Настольное приложение для транскрибации аудио и перевода текста
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
from pathlib import Path
import json
from typing import List, Dict

# Импорт наших модулей
from transcription import TranscriptionProcessor, TRANSFORMERS_AVAILABLE
from translation import TranslationProcessor
from text_processor import TextProcessor
from utils import get_supported_audio_formats, load_settings, save_settings as save_settings_to_file, get_audio_file_info, format_duration

class AudioTranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Транскрибация аудио и перевод текста")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Настройки
        self.settings = load_settings()
        self.text_chunks = []
        self.current_chunk_index = 0
        self.transcription_results = []
        
        # Создаем интерфейс
        self.create_interface()
        
    def create_interface(self):
        """Создание основного интерфейса"""
        # Главное меню
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню настроек
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Настройки", menu=settings_menu)
        settings_menu.add_command(label="API настройки", command=self.open_settings_window)
        
        # Основной фрейм с вкладками
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Вкладка транскрибации
        self.transcription_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.transcription_frame, text="🎤 Транскрибация аудио")
        self.create_transcription_tab()
        
        # Вкладка перевода
        self.translation_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.translation_frame, text="📝 Перевод текста")
        self.create_translation_tab()
        
        # Статусная строка
        self.status_var = tk.StringVar(value="Готов к работе")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken')
        self.status_bar.pack(side='bottom', fill='x')
        
    def create_transcription_tab(self):
        """Создание вкладки транскрибации"""
        main_frame = ttk.Frame(self.transcription_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Выбор папки
        folder_frame = ttk.LabelFrame(main_frame, text="Выбор папки с аудиофайлами", padding=10)
        folder_frame.pack(fill='x', pady=(0, 10))
        
        self.folder_path = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path, width=60)
        folder_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        folder_btn = ttk.Button(folder_frame, text="Выбрать папку", command=self.select_folder)
        folder_btn.pack(side='right')
        
        # Информация о файлах
        files_frame = ttk.LabelFrame(main_frame, text="Найденные аудиофайлы", padding=10)
        files_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Список файлов
        self.files_tree = ttk.Treeview(files_frame, columns=('Name', 'Duration', 'Size'), show='tree headings', height=8)
        self.files_tree.heading('#0', text='')
        self.files_tree.heading('Name', text='Имя файла')
        self.files_tree.heading('Duration', text='Длительность')
        self.files_tree.heading('Size', text='Размер')
        
        self.files_tree.column('#0', width=0, stretch=False)
        self.files_tree.column('Name', width=400)
        self.files_tree.column('Duration', width=100)
        self.files_tree.column('Size', width=100)
        
        scrollbar_files = ttk.Scrollbar(files_frame, orient='vertical', command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar_files.set)
        
        self.files_tree.pack(side='left', fill='both', expand=True)
        scrollbar_files.pack(side='right', fill='y')
        
        # Кнопки управления
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill='x', pady=(0, 10))
        
        self.transcribe_btn = ttk.Button(control_frame, text="🚀 Начать транскрибацию", 
                                        command=self.start_transcription, state='disabled')
        self.transcribe_btn.pack(side='left', padx=(0, 10))
        
        # Прогресс-бар
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(control_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Результаты транскрибации
        results_frame = ttk.LabelFrame(main_frame, text="Результаты транскрибации", padding=10)
        results_frame.pack(fill='both', expand=True)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=10, wrap='word')
        self.results_text.pack(fill='both', expand=True)
        
    def create_translation_tab(self):
        """Создание вкладки перевода"""
        main_frame = ttk.Frame(self.translation_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Загрузка файла
        file_frame = ttk.LabelFrame(main_frame, text="Загрузка текстового файла", padding=10)
        file_frame.pack(fill='x', pady=(0, 10))
        
        self.text_file_path = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.text_file_path, width=60)
        file_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        file_btn = ttk.Button(file_frame, text="Выбрать файл", command=self.select_text_file)
        file_btn.pack(side='right')
        
        # Навигация по чанкам
        nav_frame = ttk.LabelFrame(main_frame, text="Навигация по чанкам", padding=10)
        nav_frame.pack(fill='x', pady=(0, 10))
        
        self.prev_btn = ttk.Button(nav_frame, text="⬅️ Предыдущий", command=self.prev_chunk, state='disabled')
        self.prev_btn.pack(side='left', padx=(0, 10))
        
        self.chunk_info = tk.StringVar(value="Чанк 0 из 0")
        ttk.Label(nav_frame, textvariable=self.chunk_info).pack(side='left', padx=(0, 10))
        
        self.next_btn = ttk.Button(nav_frame, text="Следующий ➡️", command=self.next_chunk, state='disabled')
        self.next_btn.pack(side='left', padx=(0, 10))
        
        self.translate_chunk_btn = ttk.Button(nav_frame, text="🌐 Перевести чанк", 
                                            command=self.translate_current_chunk, state='disabled')
        self.translate_chunk_btn.pack(side='right', padx=(10, 0))
        
        self.translate_all_btn = ttk.Button(nav_frame, text="🚀 Перевести все", 
                                          command=self.translate_all_chunks, state='disabled')
        self.translate_all_btn.pack(side='right', padx=(10, 0))
        
        # Область текста
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill='both', expand=True)
        
        # Оригинальный текст
        original_frame = ttk.LabelFrame(text_frame, text="📄 Оригинальный текст", padding=5)
        original_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        self.original_text = scrolledtext.ScrolledText(original_frame, height=15, wrap='word', state='disabled')
        self.original_text.pack(fill='both', expand=True)
        
        # Переведенный текст
        translated_frame = ttk.LabelFrame(text_frame, text="🔄 Перевод", padding=5)
        translated_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        self.translated_text = scrolledtext.ScrolledText(translated_frame, height=15, wrap='word', state='disabled')
        self.translated_text.pack(fill='both', expand=True)
        
        # Кнопки экспорта
        export_frame = ttk.Frame(main_frame)
        export_frame.pack(fill='x', pady=(10, 0))
        
        self.export_btn = ttk.Button(export_frame, text="💾 Экспортировать результаты", 
                                    command=self.export_translation, state='disabled')
        self.export_btn.pack(side='right')
        
    def open_settings_window(self):
        """Открытие окна настроек API"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Настройки API")
        settings_window.geometry("500x400")
        settings_window.resizable(False, False)
        
        # Центрирование окна
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        main_frame = ttk.Frame(settings_window, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # API Endpoint
        ttk.Label(main_frame, text="API Эндпоинт:").pack(anchor='w', pady=(0, 5))
        endpoint_var = tk.StringVar(value=self.settings.get('api_endpoint', ''))
        endpoint_entry = ttk.Entry(main_frame, textvariable=endpoint_var, width=60)
        endpoint_entry.pack(fill='x', pady=(0, 15))
        
        # API Token
        ttk.Label(main_frame, text="API Токен:").pack(anchor='w', pady=(0, 5))
        token_var = tk.StringVar(value=self.settings.get('api_token', ''))
        token_entry = ttk.Entry(main_frame, textvariable=token_var, width=60, show='*')
        token_entry.pack(fill='x', pady=(0, 15))
        
        # Model
        ttk.Label(main_frame, text="Модель:").pack(anchor='w', pady=(0, 5))
        model_var = tk.StringVar(value=self.settings.get('api_model', 'gpt-3.5-turbo'))
        model_entry = ttk.Entry(main_frame, textvariable=model_var, width=60)
        model_entry.pack(fill='x', pady=(0, 15))
        
        # System Prompt
        ttk.Label(main_frame, text="Системный промпт:").pack(anchor='w', pady=(0, 5))
        prompt_text = scrolledtext.ScrolledText(main_frame, height=8, wrap='word')
        prompt_text.insert('1.0', self.settings.get('system_prompt', 
            'Переведи следующий текст на русский язык. Сохрани структуру и стиль оригинала.'))
        prompt_text.pack(fill='both', expand=True, pady=(0, 15))
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        def save_and_close():
            new_settings = {
                'api_endpoint': endpoint_var.get(),
                'api_token': token_var.get(),
                'api_model': model_var.get(),
                'system_prompt': prompt_text.get('1.0', 'end-1c')
            }
            self.settings = new_settings
            save_settings_to_file(new_settings)
            messagebox.showinfo("Настройки", "Настройки сохранены!")
            settings_window.destroy()
        
        ttk.Button(button_frame, text="Сохранить", command=save_and_close).pack(side='right', padx=(10, 0))
        ttk.Button(button_frame, text="Отмена", command=settings_window.destroy).pack(side='right')
        
    def select_folder(self):
        """Выбор папки с аудиофайлами"""
        folder = filedialog.askdirectory(title="Выберите папку с аудиофайлами")
        if folder:
            self.folder_path.set(folder)
            self.scan_audio_files(folder)
            
    def scan_audio_files(self, folder_path):
        """Сканирование папки на наличие аудиофайлов"""
        self.status_var.set("Сканирование папки...")
        
        # Очищаем список
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
            
        audio_files = []
        supported_extensions = get_supported_audio_formats()
        
        try:
            for file_path in Path(folder_path).rglob("*"):
                if file_path.suffix.lower() in supported_extensions:
                    audio_files.append(file_path)
                    
            # Добавляем файлы в список
            for i, file_path in enumerate(audio_files):
                try:
                    file_info = get_audio_file_info(file_path)
                    duration = file_info.get('duration_formatted', 'N/A')
                    size = f"{file_info.get('file_size', 0) / (1024*1024):.1f} MB"
                except:
                    duration = 'N/A'
                    size = 'N/A'
                    
                self.files_tree.insert('', 'end', values=(file_path.name, duration, size))
                
            self.transcribe_btn.config(state='normal' if audio_files and TRANSFORMERS_AVAILABLE else 'disabled')
            
            if not TRANSFORMERS_AVAILABLE:
                self.status_var.set("Найдено файлов: " + str(len(audio_files)) + 
                                  " (Для транскрибации необходимо установить PyTorch и Transformers)")
            else:
                self.status_var.set(f"Найдено аудиофайлов: {len(audio_files)}")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сканировании папки: {str(e)}")
            self.status_var.set("Ошибка сканирования")
            
    def start_transcription(self):
        """Запуск транскрибации в отдельном потоке"""
        if not TRANSFORMERS_AVAILABLE:
            messagebox.showerror("Ошибка", "PyTorch и Transformers не установлены!")
            return
            
        folder = self.folder_path.get()
        if not folder:
            messagebox.showwarning("Предупреждение", "Выберите папку с аудиофайлами")
            return
            
        # Запускаем в отдельном потоке
        self.transcribe_btn.config(state='disabled')
        threading.Thread(target=self.transcribe_files, args=(folder,), daemon=True).start()
        
    def transcribe_files(self, folder_path):
        """Транскрибация файлов"""
        try:
            processor = TranscriptionProcessor()
            audio_files = []
            supported_extensions = get_supported_audio_formats()
            
            for file_path in Path(folder_path).rglob("*"):
                if file_path.suffix.lower() in supported_extensions:
                    audio_files.append(file_path)
                    
            total_files = len(audio_files)
            results = []
            
            for i, audio_file in enumerate(audio_files):
                self.root.after(0, lambda: self.status_var.set(f"Обработка: {audio_file.name}"))
                
                try:
                    result = processor.transcribe_file(audio_file)
                    results.append(f"=== {audio_file.name} ===\n{result['text']}\n\n")
                    
                    # Обновляем прогресс
                    progress = (i + 1) / total_files * 100
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    
                except Exception as e:
                    results.append(f"=== ОШИБКА: {audio_file.name} ===\n{str(e)}\n\n")
                    
            # Обновляем интерфейс
            full_results = "".join(results)
            self.root.after(0, lambda: self.results_text.delete('1.0', 'end'))
            self.root.after(0, lambda: self.results_text.insert('1.0', full_results))
            self.root.after(0, lambda: self.status_var.set(f"Транскрибация завершена. Обработано: {len(audio_files)} файлов"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка транскрибации: {str(e)}"))
            
        finally:
            self.root.after(0, lambda: self.transcribe_btn.config(state='normal'))
            self.root.after(0, lambda: self.progress_var.set(0))
            
    def select_text_file(self):
        """Выбор текстового файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите текстовый файл",
            filetypes=[("Текстовые файлы", "*.txt"), ("Markdown", "*.md"), ("RTF", "*.rtf"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            self.text_file_path.set(file_path)
            self.load_text_file(file_path)
            
    def load_text_file(self, file_path):
        """Загрузка и обработка текстового файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
                
            # Обработка текста
            processor = TextProcessor()
            self.text_chunks = processor.split_into_chunks(text_content, sentences_per_chunk=30)
            self.current_chunk_index = 0
            self.translations = {}  # Словарь переводов
            
            # Обновляем интерфейс
            self.update_chunk_display()
            self.prev_btn.config(state='normal')
            self.next_btn.config(state='normal')
            self.translate_chunk_btn.config(state='normal')
            self.translate_all_btn.config(state='normal')
            
            self.status_var.set(f"Загружен файл: {Path(file_path).name}. Чанков: {len(self.text_chunks)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке файла: {str(e)}")
            
    def update_chunk_display(self):
        """Обновление отображения текущего чанка"""
        if not self.text_chunks:
            return
            
        # Обновляем информацию о чанке
        self.chunk_info.set(f"Чанк {self.current_chunk_index + 1} из {len(self.text_chunks)}")
        
        # Обновляем кнопки навигации
        self.prev_btn.config(state='normal' if self.current_chunk_index > 0 else 'disabled')
        self.next_btn.config(state='normal' if self.current_chunk_index < len(self.text_chunks) - 1 else 'disabled')
        
        # Показываем текст
        current_chunk = self.text_chunks[self.current_chunk_index]
        
        self.original_text.config(state='normal')
        self.original_text.delete('1.0', 'end')
        self.original_text.insert('1.0', current_chunk)
        self.original_text.config(state='disabled')
        
        # Показываем перевод если есть
        translation = self.translations.get(self.current_chunk_index, '')
        self.translated_text.config(state='normal')
        self.translated_text.delete('1.0', 'end')
        self.translated_text.insert('1.0', translation if translation else "Нажмите кнопку для перевода")
        self.translated_text.config(state='disabled')
        
        # Обновляем кнопку экспорта
        has_translations = any(self.translations.values())
        self.export_btn.config(state='normal' if has_translations else 'disabled')
        
    def prev_chunk(self):
        """Переход к предыдущему чанку"""
        if self.current_chunk_index > 0:
            self.current_chunk_index -= 1
            self.update_chunk_display()
            
    def next_chunk(self):
        """Переход к следующему чанку"""
        if self.current_chunk_index < len(self.text_chunks) - 1:
            self.current_chunk_index += 1
            self.update_chunk_display()
            
    def translate_current_chunk(self):
        """Перевод текущего чанка"""
        if not self.text_chunks:
            return
            
        # Проверяем настройки API
        if not self.settings.get('api_endpoint') or not self.settings.get('api_token'):
            messagebox.showwarning("Настройки", "Настройте API эндпоинт и токен в меню Настройки")
            return
            
        # Запускаем перевод в отдельном потоке
        self.translate_chunk_btn.config(state='disabled')
        current_chunk = self.text_chunks[self.current_chunk_index]
        threading.Thread(target=self.translate_chunk, args=(current_chunk, self.current_chunk_index), daemon=True).start()
        
    def translate_chunk(self, chunk_text, chunk_index):
        """Перевод чанка"""
        try:
            translator = TranslationProcessor(
                api_endpoint=self.settings.get('api_endpoint', ''),
                api_token=self.settings.get('api_token', ''),
                model=self.settings.get('api_model', 'gpt-3.5-turbo'),
                system_prompt=self.settings.get('system_prompt', '')
            )
            
            self.root.after(0, lambda: self.status_var.set("Выполняется перевод..."))
            translation = translator.translate_text(chunk_text)
            
            # Сохраняем перевод
            self.translations[chunk_index] = translation
            
            # Обновляем интерфейс
            self.root.after(0, self.update_chunk_display)
            self.root.after(0, lambda: self.status_var.set("Перевод завершен"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка при переводе: {str(e)}"))
            
        finally:
            self.root.after(0, lambda: self.translate_chunk_btn.config(state='normal'))
            
    def translate_all_chunks(self):
        """Перевод всех чанков"""
        if not self.text_chunks:
            return
            
        if not self.settings.get('api_endpoint') or not self.settings.get('api_token'):
            messagebox.showwarning("Настройки", "Настройте API эндпоинт и токен в меню Настройки")
            return
            
        # Запускаем перевод в отдельном потоке
        self.translate_all_btn.config(state='disabled')
        threading.Thread(target=self.translate_all, daemon=True).start()
        
    def translate_all(self):
        """Перевод всех чанков"""
        try:
            translator = TranslationProcessor(
                api_endpoint=self.settings.get('api_endpoint', ''),
                api_token=self.settings.get('api_token', ''),
                model=self.settings.get('api_model', 'gpt-3.5-turbo'),
                system_prompt=self.settings.get('system_prompt', '')
            )
            
            total_chunks = len(self.text_chunks)
            
            for i, chunk in enumerate(self.text_chunks):
                self.root.after(0, lambda i=i: self.status_var.set(f"Перевод чанка {i + 1} из {total_chunks}"))
                
                try:
                    translation = translator.translate_text(chunk)
                    self.translations[i] = translation
                    
                    # Обновляем прогресс
                    if i == self.current_chunk_index:
                        self.root.after(0, self.update_chunk_display)
                        
                except Exception as e:
                    self.translations[i] = f"[Ошибка перевода: {str(e)}]"
                    
            self.root.after(0, lambda: self.status_var.set("Перевод всех чанков завершен"))
            self.root.after(0, self.update_chunk_display)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка при переводе: {str(e)}"))
            
        finally:
            self.root.after(0, lambda: self.translate_all_btn.config(state='normal'))
            
    def export_translation(self):
        """Экспорт результатов перевода"""
        if not self.translations:
            messagebox.showwarning("Предупреждение", "Нет переводов для экспорта")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Сохранить перевод",
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            try:
                # Собираем переведенные чанки
                translated_chunks = []
                for i in range(len(self.text_chunks)):
                    translation = self.translations.get(i, f"[Чанк {i + 1} не переведен]")
                    translated_chunks.append(translation)
                    
                # Сохраняем файл
                full_translation = "\n\n".join(translated_chunks)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(full_translation)
                    
                messagebox.showinfo("Экспорт", f"Результаты сохранены в: {file_path}")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}")

def main():
    """Главная функция"""
    root = tk.Tk()
    app = AudioTranscriptionApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()