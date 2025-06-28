import io
import math
from pathlib import Path

# Папка для хранения скачанных моделей
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)
import numpy as np
from pydub import AudioSegment
from tqdm import tqdm

# Проверяем наличие PyTorch и Transformers
try:
    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

class TranscriptionProcessor:
    """Класс для транскрибации аудиофайлов с помощью Whisper"""
    
    def __init__(self):
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("PyTorch и Transformers не установлены. Для полной функциональности транскрибации необходимо установить: pip install torch transformers")
        
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.torch_dtype = torch.float16 if self.device == 'cuda' else torch.float32
        self.model = None
        self.processor = None
        self._load_model()
    
    def _load_model(self):
        """Загрузка модели Whisper"""
        try:
            # Загружаем модель и процессор
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
            
        except Exception as e:
            # Fallback к базовой модели если специализированная недоступна
            try:
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
                
            except Exception as fallback_e:
                raise Exception(f"Не удалось загрузить модель Whisper: {str(e)}, fallback error: {str(fallback_e)}")
    
    def transcribe_file(self, file_path):
        """
        Транскрибация одного аудиофайла
        
        Args:
            file_path: Путь к аудиофайлу
            
        Returns:
            dict: Результат транскрибации с текстом и путем к выходному файлу
        """
        file_path = Path(file_path)
        
        try:
            # Определение формата файла и чтение при помощи pydub
            audio_format = file_path.suffix.lower().lstrip('.')
            if audio_format == 'mp3':
                audio = AudioSegment.from_mp3(file_path)
            elif audio_format in ['wav', 'wave']:
                audio = AudioSegment.from_wav(file_path)
            elif audio_format == 'flac':
                audio = AudioSegment.from_file(file_path, format="flac")
            elif audio_format in ['m4a', 'mp4']:
                audio = AudioSegment.from_file(file_path, format="mp4")
            elif audio_format == 'ogg':
                audio = AudioSegment.from_ogg(file_path)
            else:
                audio = AudioSegment.from_file(file_path)
            
            # Конвертация в моно и 16kHz
            audio = audio.set_channels(1).set_sample_width(2).set_frame_rate(16000)
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            samples = samples / 32768.0  # Нормализуем в диапазон [-1, 1]
            
            sr = audio.frame_rate  # Обычно 16000
            
            # Разбиваем на чанки по 30 секунд
            chunk_s = 30
            chunk_sz = chunk_s * sr
            n_chunks = math.ceil(len(samples) / chunk_sz)
            texts = []
            
            for i in tqdm(range(n_chunks), desc=f"Транскрибация {file_path.name}"):
                start = i * chunk_sz
                end = min((i + 1) * chunk_sz, len(samples))
                chunk = samples[start:end]
                if len(chunk) == 0:
                    continue
                
                # Подготовка входов с attention_mask
                inputs = self.processor(
                    chunk,
                    return_tensors="pt",
                    sampling_rate=sr,
                    return_attention_mask=True
                )
                inputs = {
                    k: v.to(device=self.device, dtype=self.torch_dtype if v.dtype.is_floating_point else torch.long)
                    for k, v in inputs.items()
                }
                
                # Генерация транскрипции
                with torch.no_grad():
                    out = self.model.generate(**inputs)
                transcription = self.processor.batch_decode(out, skip_special_tokens=True)[0]
                texts.append(transcription)
            
            # Объединяем результат
            full_text = " ".join(texts)
            
            # Сохраняем результат
            output_path = file_path.with_suffix(file_path.suffix + ".txt")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            return {
                'text': full_text,
                'output_file': str(output_path)
            }
            
        except Exception as e:
            raise Exception(f"Ошибка при транскрибации файла {file_path.name}: {str(e)}")
    
    def get_model_info(self):
        """Возвращает информацию о загруженной модели"""
        return {
            'device': self.device,
            'dtype': str(self.torch_dtype),
            'model_loaded': self.model is not None,
            'processor_loaded': self.processor is not None
        }
