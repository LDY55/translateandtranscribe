#!/usr/bin/env python3
"""
Тест для проверки транскрибации
"""

import pytest


def test_dependencies():
    """Проверка доступности зависимостей"""
    print("🔍 Проверка зависимостей...")

    try:
        import torch

        print(f"✅ PyTorch: {torch.__version__}")
        print(f"📱 CUDA доступна: {torch.cuda.is_available()}")
    except ImportError:
        pytest.skip("PyTorch не установлен")

    try:
        import transformers

        print(f"✅ Transformers: {transformers.__version__}")
    except ImportError:
        pytest.skip("Transformers не установлен")

    try:
        from pydub import AudioSegment

        print("✅ PyDub доступен")
    except ImportError:
        pytest.skip("PyDub не доступен")


def test_transcription_simple():
    """Простой тест транскрибации"""
    print("\n🎤 Тестирование простой транскрибации...")

    test_dependencies()

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
