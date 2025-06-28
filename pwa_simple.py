#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Упрощенная PWA версия без PyTorch для демонстрации
"""

import os
import json
from pathlib import Path
import time
import threading

# Минимальные зависимости
try:
    from flask import Flask, render_template, request, jsonify, send_from_directory
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

if not FLASK_AVAILABLE:
    print("❌ Flask не установлен. Установите: pip install flask")
    exit(1)

# Импорт только доступных модулей
from translation import TranslationProcessor
from text_processor import TextProcessor
from utils import get_supported_audio_formats, load_settings, save_settings as save_settings_to_file

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# Глобальные переменные для состояния
transcription_status = {"progress": 0, "status": "disabled", "results": [], "error": "PyTorch не установлен"}
translation_status = {"progress": 0, "status": "idle", "chunks": [], "translations": {}}

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Статические файлы"""
    return send_from_directory('static', filename)

@app.route('/api/transcribe', methods=['POST'])
def api_transcribe():
    """API для транскрибации (заглушка)"""
    return jsonify({
        "success": False,
        "error": "Транскрибация недоступна. Установите PyTorch и Transformers: pip install torch transformers"
    }), 400

@app.route('/api/transcription-status')
def api_transcription_status():
    """Получение статуса транскрибации"""
    return jsonify(transcription_status)

@app.route('/api/process-text', methods=['POST'])
def api_process_text():
    """API для обработки текста"""
    global translation_status
    
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"success": False, "error": "Нет текста"}), 400
    
    text = data['text']
    sentences_per_chunk = data.get('sentences_per_chunk', 30)
    
    try:
        processor = TextProcessor()
        chunks = processor.split_into_chunks(text, sentences_per_chunk=sentences_per_chunk)
        
        translation_status = {
            "progress": 0,
            "status": "ready",
            "chunks": chunks,
            "translations": {},
            "current_chunk": 0
        }
        
        return jsonify({
            "success": True,
            "chunks": chunks,
            "total_chunks": len(chunks)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/translate', methods=['POST'])
def api_translate():
    """API для перевода текста"""
    global translation_status
    
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Нет данных"}), 400
    
    settings = data.get('settings', {})
    if not settings.get('api_endpoint') or not settings.get('api_token'):
        return jsonify({"success": False, "error": "Не настроены параметры API"}), 400
    
    chunk_index = data.get('chunk_index')
    translate_all = data.get('translate_all', False)
    
    if translation_status.get("status") == "processing":
        return jsonify({"success": False, "error": "Перевод уже выполняется"}), 400
    
    def translate_task():
        global translation_status
        
        try:
            translator = TranslationProcessor(
                api_endpoint=settings['api_endpoint'],
                api_token=settings['api_token'],
                model=settings.get('api_model', 'gpt-3.5-turbo'),
                system_prompt=settings.get('system_prompt', 'Переведи следующий текст на русский язык.')
            )
            
            chunks = translation_status.get("chunks", [])
            if not chunks:
                translation_status["status"] = "error"
                translation_status["error"] = "Нет загруженных чанков"
                return
            
            translation_status["status"] = "processing"
            
            if translate_all:
                # Переводим все чанки
                for i, chunk in enumerate(chunks):
                    translation_status["progress"] = int((i / len(chunks)) * 100)
                    
                    try:
                        translation = translator.translate_text(chunk)
                        translation_status["translations"][str(i)] = translation
                    except Exception as e:
                        translation_status["translations"][str(i)] = f"[Ошибка перевода: {str(e)}]"
                    
                    time.sleep(0.1)  # Небольшая пауза между запросами
                    
            else:
                # Переводим один чанк
                if chunk_index is not None and 0 <= chunk_index < len(chunks):
                    chunk = chunks[chunk_index]
                    translation = translator.translate_text(chunk)
                    translation_status["translations"][str(chunk_index)] = translation
                    translation_status["progress"] = 100
            
            translation_status["status"] = "completed"
            
        except Exception as e:
            translation_status["status"] = "error"
            translation_status["error"] = str(e)
    
    thread = threading.Thread(target=translate_task)
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True, "message": "Перевод запущен"})

@app.route('/api/translation-status')
def api_translation_status():
    """Получение статуса перевода"""
    return jsonify(translation_status)

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """API для работы с настройками"""
    if request.method == 'GET':
        settings = load_settings()
        return jsonify({"success": True, "settings": settings})
    
    elif request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Нет данных"}), 400
        
        try:
            save_settings_to_file(data)
            return jsonify({"success": True, "message": "Настройки сохранены"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/export-translation')
def api_export_translation():
    """API для экспорта перевода"""
    global translation_status
    
    chunks = translation_status.get("chunks", [])
    translations = translation_status.get("translations", {})
    
    if not translations:
        return jsonify({"success": False, "error": "Нет переводов для экспорта"}), 400
    
    # Собираем переведенные чанки
    translated_chunks = []
    for i in range(len(chunks)):
        translation = translations.get(str(i), f"[Чанк {i + 1} не переведен]")
        translated_chunks.append(translation)
    
    full_translation = "\n\n".join(translated_chunks)
    
    return jsonify({
        "success": True,
        "translation": full_translation,
        "filename": "translation.txt"
    })

@app.route('/api/system-info')
def api_system_info():
    """Информация о системе"""
    return jsonify({
        "transformers_available": False,
        "supported_audio_formats": get_supported_audio_formats(),
        "max_file_size": app.config['MAX_CONTENT_LENGTH'],
        "transcription_available": False,
        "translation_available": True
    })

def create_demo_icons():
    """Создает простые иконки для PWA"""
    import base64
    
    # Простая SVG иконка
    svg_icon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192">
        <rect width="192" height="192" fill="#1f77b4"/>
        <text x="96" y="110" text-anchor="middle" fill="white" font-size="80" font-family="Arial">🎵</text>
    </svg>'''
    
    # Создаем файлы иконок (заглушки)
    with open('static/icon-192.png', 'w') as f:
        f.write("# PWA Icon 192x192 (placeholder)")
    
    with open('static/icon-512.png', 'w') as f:
        f.write("# PWA Icon 512x512 (placeholder)")

if __name__ == '__main__':
    # Создаем папки если их нет
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Создаем иконки-заглушки
    create_demo_icons()
    
    # Запускаем сервер
    print("🚀 Запуск PWA приложения...")
    print("📱 Откройте в браузере: http://localhost:5000")
    print("💾 Для установки как приложение используйте меню браузера")
    print("⚠️  Транскрибация отключена (нет PyTorch)")
    print("✅ Перевод текста доступен")
    
    app.run(debug=True, host='0.0.0.0', port=5000)