"""
Упрощенная версия транскрибации с прямой проверкой PyTorch
"""
import os
import sys
import subprocess
import io
from pathlib import Path

# Папка для сохранения моделей, чтобы не скачивать их повторно
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)
from pydub import AudioSegment
from tqdm import tqdm

class TranscriptionProcessor:
    """Класс для транскрибации аудиофайлов с помощью Whisper"""
    
    def __init__(self):
        self.device = 'cpu'
        self.torch_dtype = None
        self.model = None
        self.processor = None
        self._check_and_install_deps()
        self._load_model()
    
    def _check_and_install_deps(self):
        """Проверка и установка зависимостей"""
        try:
            # Попытка импорта PyTorch
            import torch
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu' 
            self.torch_dtype = torch.float16 if self.device == 'cuda' else torch.float32
            
            # Попытка импорта transformers
            from transformers import WhisperForConditionalGeneration, WhisperProcessor
            
            print(f"✅ PyTorch найден. Устройство: {self.device}")
            
        except ImportError as e:
            print(f"⚠️ Отсутствующие зависимости: {e}")
            print("🔄 Установка PyTorch и transformers...")
            
            # Установка через pip
            try:
                # Используем CPU-only версию PyTorch для экономии места
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", 
                    "torch", "transformers", "accelerate",
                    "--index-url", "https://download.pytorch.org/whl/cpu",
                    "--no-cache-dir"
                ], timeout=300)
                print("✅ Зависимости установлены успешно")
                
                # Повторный импорт
                import torch
                from transformers import WhisperForConditionalGeneration, WhisperProcessor
                
                self.device = 'cpu'  # Принудительно используем CPU
                self.torch_dtype = torch.float32
                
            except subprocess.TimeoutExpired:
                raise ImportError("Тайм-аут установки зависимостей. Попробуйте позже.")
            except Exception as install_error:
                raise ImportError(f"Не удалось установить зависимости: {install_error}")
    
    def _load_model(self):
        """Загрузка модели Whisper"""
        try:
            import torch
            from transformers import WhisperForConditionalGeneration, WhisperProcessor
            
            print("🔄 Загрузка модели Whisper...")
            
            # Загружаем русскую модель
            try:
                self.model = WhisperForConditionalGeneration.from_pretrained(
                    "antony66/whisper-large-v3-russian",
                    torch_dtype=self.torch_dtype,
                    low_cpu_mem_usage=True,
                    use_safetensors=True,
                    cache_dir=MODELS_DIR,
                ).to(self.device)

                self.processor = WhisperProcessor.from_pretrained(
                    "antony66/whisper-large-v3-russian",
                    cache_dir=MODELS_DIR,
                )
                print("✅ Загружена русская модель Whisper Large V3")
                
            except Exception as e:
                print(f"⚠️ Ошибка загрузки русской модели: {e}")
                print("🔄 Загрузка базовой модели...")
                
                # Fallback к базовой модели
                self.model = WhisperForConditionalGeneration.from_pretrained(
                    "openai/whisper-large-v3",
                    torch_dtype=self.torch_dtype,
                    low_cpu_mem_usage=True,
                    use_safetensors=True,
                    cache_dir=MODELS_DIR,
                ).to(self.device)

                self.processor = WhisperProcessor.from_pretrained(
                    "openai/whisper-large-v3",
                    cache_dir=MODELS_DIR,
                )
                print("✅ Загружена базовая модель Whisper Large V3")
                
        except Exception as e:
            raise Exception(f"Критическая ошибка загрузки модели: {e}")
    
    def transcribe_file(self, file_path, progress_callback=None):
        """
        Транскрибация одного аудиофайла
        
        Args:
            file_path: Путь к аудиофайлу
            
        Returns:
            dict: Результат транскрибации с текстом и путем к выходному файлу
        """
        if not self.model or not self.processor:
            raise Exception("Модель не загружена")
            
        file_path = Path(file_path)
        
        try:
            import torch
            import numpy as np
            
            # Проверка существования файла
            if not file_path.exists():
                raise Exception(f"Файл не найден: {file_path}")
            
            # Чтение аудиофайла
            try:
                with open(file_path, "rb") as f:
                    audio_bytes = f.read()
            except Exception as e:
                raise Exception(f"Ошибка чтения файла: {e}")
            
            # Определение формата файла
            audio_format = file_path.suffix.lower().lstrip('.')
            
            try:
                # Создаем новый BytesIO объект для каждого использования
                audio_io = io.BytesIO(audio_bytes)
                
                if audio_format == 'mp3':
                    audio = AudioSegment.from_mp3(audio_io)
                elif audio_format in ['wav', 'wave']:
                    audio = AudioSegment.from_wav(audio_io)
                elif audio_format == 'flac':
                    audio = AudioSegment.from_file(audio_io, format='flac')
                elif audio_format in ['m4a', 'mp4']:
                    audio = AudioSegment.from_file(audio_io, format='mp4')
                else:
                    raise Exception(f"Неподдерживаемый формат аудио: {audio_format}")
                    
                # BytesIO будет автоматически закрыт при сборке мусора
                
            except Exception as e:
                raise Exception(f"Ошибка декодирования аудио: {e}")
            
            # Конвертация в моно 16кГц
            audio = audio.set_channels(1).set_frame_rate(16000)
            
            # Преобразование в numpy array
            audio_array = np.array(audio.get_array_of_samples(), dtype=np.float32)
            audio_array = audio_array / np.iinfo(np.int16).max  # Нормализация
            
            # Разбивка на чанки если файл большой
            chunk_length = 30 * 16000  # 30 секунд
            chunks = []
            
            if len(audio_array) <= chunk_length:
                chunks = [audio_array]
            else:
                for i in range(0, len(audio_array), chunk_length):
                    chunks.append(audio_array[i:i + chunk_length])
            
            # Транскрибация чанков
            all_text = []
            total_chunks = len(chunks)
            for i, chunk in enumerate(tqdm(chunks, desc="Транскрибация")):
                # Подготовка входных данных
                inputs = self.processor(
                    chunk,
                    sampling_rate=16000,
                    return_tensors="pt"
                )
                input_features = inputs.input_features.to(
                    device=self.device,
                    dtype=self.torch_dtype
                )
                
                # Генерация
                with torch.no_grad():
                    predicted_ids = self.model.generate(
                        input_features,
                        max_length=448,
                        num_beams=5,
                        early_stopping=True,
                        return_dict_in_generate=True
                    )
                
                # Декодирование
                transcription = self.processor.batch_decode(
                    predicted_ids.sequences, 
                    skip_special_tokens=True
                )[0]
                
                all_text.append(transcription.strip())

                if progress_callback:
                    progress = ((i + 1) / total_chunks) * 100
                    try:
                        progress_callback(progress)
                    except Exception:
                        pass
            
            # Объединение результатов
            final_text = " ".join(all_text)
            
            # Сохранение результата
            output_file = file_path.with_suffix('.txt')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_text)
            
            return {
                'text': final_text,
                'output_file': str(output_file),
                'success': True
            }
            
        except Exception as e:
            return {
                'text': '',
                'output_file': '',
                'success': False,
                'error': str(e)
            }
    
    def get_model_info(self):
        """Возвращает информацию о загруженной модели"""
        if self.model:
            return {
                'model_loaded': True,
                'device': self.device,
                'torch_dtype': str(self.torch_dtype)
            }
        else:
            return {
                'model_loaded': False,
                'device': None,
                'torch_dtype': None
            }