#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Progressive Web App версия приложения для транскрибации и перевода
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
from pathlib import Path
import threading
import time

# Импорт наших модулей
from transcription import TranscriptionProcessor, TRANSFORMERS_AVAILABLE
from translation import TranslationProcessor
from text_processor import TextProcessor
from utils import (
    get_supported_audio_formats,
    load_settings,
    save_settings as save_settings_to_file,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500MB максимум

# Глобальные переменные для состояния
transcription_status = {"progress": 0, "status": "idle", "results": []}
translation_status = {"progress": 0, "status": "idle", "chunks": [], "translations": {}}


@app.route("/")
def index():
    """Главная страница"""
    return render_template("index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    """Статические файлы"""
    return send_from_directory("static", filename)


@app.route("/api/transcribe", methods=["POST"])
def api_transcribe():
    """API для транскрибации аудиофайлов"""
    global transcription_status

    if not TRANSFORMERS_AVAILABLE:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "PyTorch и Transformers не установлены. Установите: pip install torch transformers",
                }
            ),
            400,
        )

    if "files" not in request.files:
        return jsonify({"success": False, "error": "Нет файлов"}), 400

    files = request.files.getlist("files")
    audio_files = []

    # Фильтруем аудиофайлы
    supported_extensions = get_supported_audio_formats()
    for file in files:
        if any(file.filename.lower().endswith(ext) for ext in supported_extensions):
            audio_files.append(file)

    if not audio_files:
        return (
            jsonify({"success": False, "error": "Нет поддерживаемых аудиофайлов"}),
            400,
        )

    # Запускаем транскрибацию в отдельном потоке
    def transcribe_task():
        global transcription_status

        try:
            processor = TranscriptionProcessor()
            transcription_status = {
                "progress": 0,
                "status": "processing",
                "results": [],
            }

            for i, file in enumerate(audio_files):
                transcription_status["status"] = f"Обработка: {file.filename}"

                # Сохраняем временный файл
                temp_path = Path(f"temp_{file.filename}")
                file.save(temp_path)

                try:
                    result = processor.transcribe_file(temp_path)
                    transcription_status["results"].append(
                        {
                            "filename": file.filename,
                            "text": result["text"],
                            "success": True,
                        }
                    )
                except Exception as e:
                    transcription_status["results"].append(
                        {
                            "filename": file.filename,
                            "text": "",
                            "error": str(e),
                            "success": False,
                        }
                    )
                finally:
                    # Удаляем временный файл
                    if temp_path.exists():
                        temp_path.unlink()

                transcription_status["progress"] = int((i + 1) / len(audio_files) * 100)

            transcription_status["status"] = "completed"

        except Exception as e:
            transcription_status = {
                "progress": 0,
                "status": "error",
                "error": str(e),
                "results": [],
            }

    thread = threading.Thread(target=transcribe_task)
    thread.daemon = True
    thread.start()

    return jsonify({"success": True, "message": "Транскрибация запущена"})


@app.route("/api/transcription-status")
def api_transcription_status():
    """Получение статуса транскрибации"""
    return jsonify(transcription_status)


@app.route("/api/process-text", methods=["POST"])
def api_process_text():
    """API для обработки текста"""
    global translation_status

    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"success": False, "error": "Нет текста"}), 400

    text = data["text"]
    sentences_per_chunk = data.get("sentences_per_chunk", 30)

    try:
        processor = TextProcessor()
        chunks = processor.split_into_chunks(
            text, sentences_per_chunk=sentences_per_chunk
        )

        translation_status = {
            "progress": 0,
            "status": "ready",
            "chunks": chunks,
            "translations": {},
            "current_chunk": 0,
        }

        return jsonify({"success": True, "chunks": chunks, "total_chunks": len(chunks)})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/translate", methods=["POST"])
def api_translate():
    """API для перевода текста"""
    global translation_status

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Нет данных"}), 400

    settings = data.get("settings", {})
    if not settings.get("api_endpoint") or not settings.get("api_token"):
        return jsonify({"success": False, "error": "Не настроены параметры API"}), 400

    chunk_index = data.get("chunk_index")
    translate_all = data.get("translate_all", False)

    if translation_status.get("status") == "processing":
        return jsonify({"success": False, "error": "Перевод уже выполняется"}), 400

    def translate_task():
        global translation_status

        try:
            translator = TranslationProcessor(
                api_endpoint=settings["api_endpoint"],
                api_token=settings["api_token"],
                model=settings.get("api_model", "gpt-3.5-turbo"),
                system_prompt=settings.get(
                    "system_prompt", "Переведи следующий текст на русский язык."
                ),
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
                    translation_status["progress"] = int(((i + 1) / len(chunks)) * 100)

                    try:
                        translation = translator.translate_text(chunk)
                        translation_status["translations"][str(i)] = translation
                    except Exception as e:
                        translation_status["translations"][str(i)] = (
                            f"[Ошибка перевода: {str(e)}]"
                        )

                    # Задержка между запросами для избежания лимитов
                    time.sleep(5)

            else:
                # Переводим один чанк
                if chunk_index is not None and 0 <= chunk_index < len(chunks):
                    chunk = chunks[chunk_index]
                    translation = translator.translate_text(chunk)
                    translation_status["translations"][str(chunk_index)] = translation
                    translation_status["progress"] = 100

            translation_status["progress"] = 100
            translation_status["status"] = "completed"

        except Exception as e:
            translation_status["status"] = "error"
            translation_status["error"] = str(e)

    thread = threading.Thread(target=translate_task)
    thread.daemon = True
    thread.start()

    return jsonify({"success": True, "message": "Перевод запущен"})


@app.route("/api/translation-status")
def api_translation_status():
    """Получение статуса перевода"""
    return jsonify(translation_status)


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    """API для работы с настройками"""
    if request.method == "GET":
        settings = load_settings()
        return jsonify({"success": True, "settings": settings})

    elif request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Нет данных"}), 400

        try:
            save_settings_to_file(data)
            return jsonify({"success": True, "message": "Настройки сохранены"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/export-translation")
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

    return jsonify(
        {
            "success": True,
            "translation": full_translation,
            "filename": "translation.txt",
        }
    )


@app.route("/api/system-info")
def api_system_info():
    """Информация о системе"""
    return jsonify(
        {
            "transformers_available": TRANSFORMERS_AVAILABLE,
            "supported_audio_formats": get_supported_audio_formats(),
            "max_file_size": app.config["MAX_CONTENT_LENGTH"],
        }
    )


if __name__ == "__main__":
    # Создаем папки если их нет
    os.makedirs("static", exist_ok=True)
    os.makedirs("templates", exist_ok=True)

    # Запускаем сервер
    print("🚀 Запуск PWA приложения...")
    print("📱 Откройте в браузере: http://localhost:5000")
    print(
        "💾 Для установки как приложение используйте 'Установить приложение' в браузере"
    )

    app.run(debug=True, host="0.0.0.0", port=5000)
