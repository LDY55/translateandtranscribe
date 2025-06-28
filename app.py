import streamlit as st
import os
from pathlib import Path
import json
from transcription import TranscriptionProcessor
from translation import TranslationProcessor
from text_processor import TextProcessor
from utils import get_supported_audio_formats, load_settings, save_settings

# Настройка страницы
st.set_page_config(
    page_title="Транскрибация и Перевод",
    page_icon="🎵",
    layout="wide"
)

# Инициализация session state
if 'settings' not in st.session_state:
    st.session_state.settings = load_settings()

if 'transcription_results' not in st.session_state:
    st.session_state.transcription_results = []

if 'text_chunks' not in st.session_state:
    st.session_state.text_chunks = []

if 'current_chunk_index' not in st.session_state:
    st.session_state.current_chunk_index = 0

def main():
    st.title("🎵 Транскрибация аудио и перевод текстов")
    
    # Боковая панель для настроек
    with st.sidebar:
        st.header("⚙️ Настройки")
        
        # Настройки API
        st.subheader("🔑 Настройки API")
        api_endpoint = st.text_input(
            "API Эндпоинт",
            value=st.session_state.settings.get('api_endpoint', ''),
            help="URL эндпоинта для API переводчика"
        )
        
        api_token = st.text_input(
            "API Токен",
            value=st.session_state.settings.get('api_token', ''),
            type="password",
            help="Токен для аутентификации API"
        )
        
        api_model = st.text_input(
            "Модель",
            value=st.session_state.settings.get('api_model', 'gpt-3.5-turbo'),
            help="Название модели для использования"
        )
        
        system_prompt = st.text_area(
            "Системный промпт",
            value=st.session_state.settings.get('system_prompt', 
                'Переведи следующий текст на русский язык. Сохрани структуру и стиль оригинала.'),
            height=100,
            help="Инструкции для модели перевода"
        )
        
        # Сохранение настроек
        if st.button("💾 Сохранить настройки"):
            settings = {
                'api_endpoint': api_endpoint,
                'api_token': api_token,
                'api_model': api_model,
                'system_prompt': system_prompt
            }
            st.session_state.settings = settings
            save_settings(settings)
            st.success("Настройки сохранены!")
    
    # Основные вкладки
    tab1, tab2 = st.tabs(["🎤 Транскрибация аудио", "📝 Перевод текста"])
    
    with tab1:
        audio_transcription_tab()
    
    with tab2:
        text_translation_tab()

def audio_transcription_tab():
    st.header("🎤 Транскрибация аудиофайлов")
    
    # Выбор папки с аудиофайлами
    col1, col2 = st.columns([2, 1])
    
    with col1:
        folder_path = st.text_input(
            "📁 Путь к папке с аудиофайлами",
            help="Укажите полный путь к папке, содержащей аудиофайлы"
        )
    
    with col2:
        st.write("**Поддерживаемые форматы:**")
        formats = get_supported_audio_formats()
        st.write(", ".join(formats))
    
    if folder_path and os.path.exists(folder_path):
        # Поиск аудиофайлов в папке
        audio_files = []
        supported_extensions = get_supported_audio_formats()
        
        for file_path in Path(folder_path).rglob("*"):
            if file_path.suffix.lower() in supported_extensions:
                audio_files.append(file_path)
        
        if audio_files:
            st.success(f"Найдено {len(audio_files)} аудиофайлов")
            
            # Показ найденных файлов
            with st.expander("📄 Список найденных файлов"):
                for i, file_path in enumerate(audio_files[:10]):  # Показываем первые 10
                    st.write(f"{i+1}. {file_path.name}")
                if len(audio_files) > 10:
                    st.write(f"... и еще {len(audio_files) - 10} файлов")
            
            # Кнопка запуска транскрибации
            if st.button("🚀 Начать транскрибацию", type="primary"):
                transcribe_audio_files(audio_files)
        else:
            st.warning("В указанной папке не найдено поддерживаемых аудиофайлов")
    elif folder_path:
        st.error("Указанная папка не существует")
    
    # Отображение результатов транскрибации
    if st.session_state.transcription_results:
        st.subheader("📋 Результаты транскрибации")
        
        for result in st.session_state.transcription_results:
            with st.expander(f"📄 {result['filename']}"):
                st.write("**Текст:**")
                st.write(result['text'])
                st.write(f"**Файл сохранен:** {result['output_file']}")

def text_translation_tab():
    st.header("📝 Перевод текстовых документов")
    
    # Загрузка текстового файла
    uploaded_file = st.file_uploader(
        "📎 Выберите текстовый файл",
        type=['txt', 'md', 'rtf'],
        help="Поддерживаемые форматы: TXT, MD, RTF"
    )
    
    if uploaded_file is not None:
        try:
            # Чтение файла
            text_content = uploaded_file.read().decode('utf-8')
            st.success(f"Файл загружен: {uploaded_file.name}")
            
            # Обработка текста
            processor = TextProcessor()
            chunks = processor.split_into_chunks(text_content, sentences_per_chunk=30)
            st.session_state.text_chunks = chunks
            st.session_state.current_chunk_index = 0
            
            st.info(f"Текст разделен на {len(chunks)} чанков по 30 предложений")
            
            # Навигация по чанкам
            if chunks:
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    if st.button("⬅️ Предыдущий", disabled=st.session_state.current_chunk_index == 0):
                        st.session_state.current_chunk_index -= 1
                        st.rerun()
                
                with col2:
                    st.write(f"Чанк {st.session_state.current_chunk_index + 1} из {len(chunks)}")
                
                with col3:
                    if st.button("Следующий ➡️", disabled=st.session_state.current_chunk_index >= len(chunks) - 1):
                        st.session_state.current_chunk_index += 1
                        st.rerun()
                
                # Отображение текущего чанка
                current_chunk = chunks[st.session_state.current_chunk_index]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📄 Оригинальный текст")
                    st.text_area("", value=current_chunk, height=300, disabled=True, key="original_text")
                
                with col2:
                    st.subheader("🔄 Перевод")
                    
                    # Кнопка перевода
                    if st.button(f"🌐 Перевести чанк {st.session_state.current_chunk_index + 1}", type="primary"):
                        translate_current_chunk(current_chunk)
                    
                    # Отображение перевода
                    translation_key = f"translation_{st.session_state.current_chunk_index}"
                    if translation_key in st.session_state:
                        st.text_area("", value=st.session_state[translation_key], height=300, key="translated_text")
                    else:
                        st.text_area("", value="Нажмите кнопку для перевода", height=300, disabled=True)
                
                # Кнопка перевода всех чанков
                st.divider()
                if st.button("🚀 Перевести все чанки", type="secondary"):
                    translate_all_chunks(chunks)
                
                # Экспорт результатов
                if any(f"translation_{i}" in st.session_state for i in range(len(chunks))):
                    if st.button("💾 Экспортировать результаты"):
                        export_translation_results(chunks, uploaded_file.name)
        
        except UnicodeDecodeError:
            st.error("Ошибка чтения файла. Убедитесь, что файл имеет кодировку UTF-8")
        except Exception as e:
            st.error(f"Ошибка при обработке файла: {str(e)}")

def transcribe_audio_files(audio_files):
    """Транскрибация списка аудиофайлов"""
    try:
        processor = TranscriptionProcessor()
        
        # Создание прогресс-бара
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        
        for i, audio_file in enumerate(audio_files):
            status_text.text(f"Обработка: {audio_file.name}")
            
            try:
                result = processor.transcribe_file(audio_file)
                results.append({
                    'filename': audio_file.name,
                    'text': result['text'],
                    'output_file': result['output_file']
                })
                
                progress_bar.progress((i + 1) / len(audio_files))
                
            except Exception as e:
                st.error(f"Ошибка при обработке {audio_file.name}: {str(e)}")
        
        st.session_state.transcription_results = results
        status_text.text("Транскрибация завершена!")
        st.success(f"Успешно обработано {len(results)} из {len(audio_files)} файлов")
        
    except Exception as e:
        st.error(f"Ошибка при инициализации транскрибации: {str(e)}")

def translate_current_chunk(chunk_text):
    """Перевод текущего чанка"""
    try:
        translator = TranslationProcessor(
            api_endpoint=st.session_state.settings.get('api_endpoint', ''),
            api_token=st.session_state.settings.get('api_token', ''),
            model=st.session_state.settings.get('api_model', 'gpt-3.5-turbo'),
            system_prompt=st.session_state.settings.get('system_prompt', '')
        )
        
        with st.spinner("Выполняется перевод..."):
            translation = translator.translate_text(chunk_text)
            translation_key = f"translation_{st.session_state.current_chunk_index}"
            st.session_state[translation_key] = translation
            st.success("Перевод завершен!")
            st.rerun()
    
    except Exception as e:
        st.error(f"Ошибка при переводе: {str(e)}")

def translate_all_chunks(chunks):
    """Перевод всех чанков"""
    try:
        translator = TranslationProcessor(
            api_endpoint=st.session_state.settings.get('api_endpoint', ''),
            api_token=st.session_state.settings.get('api_token', ''),
            model=st.session_state.settings.get('api_model', 'gpt-3.5-turbo'),
            system_prompt=st.session_state.settings.get('system_prompt', '')
        )
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, chunk in enumerate(chunks):
            status_text.text(f"Перевод чанка {i + 1} из {len(chunks)}")
            
            try:
                translation = translator.translate_text(chunk)
                st.session_state[f"translation_{i}"] = translation
                progress_bar.progress((i + 1) / len(chunks))
            
            except Exception as e:
                st.error(f"Ошибка при переводе чанка {i + 1}: {str(e)}")
        
        status_text.text("Перевод всех чанков завершен!")
        st.success("Все чанки переведены!")
        st.rerun()
    
    except Exception as e:
        st.error(f"Ошибка при переводе: {str(e)}")

def export_translation_results(chunks, original_filename):
    """Экспорт результатов перевода"""
    try:
        # Собираем переведенные чанки
        translated_chunks = []
        for i in range(len(chunks)):
            translation_key = f"translation_{i}"
            if translation_key in st.session_state:
                translated_chunks.append(st.session_state[translation_key])
            else:
                translated_chunks.append(f"[Чанк {i + 1} не переведен]")
        
        # Создаем итоговый текст
        full_translation = "\n\n".join(translated_chunks)
        
        # Предлагаем скачать
        output_filename = f"translated_{original_filename}"
        st.download_button(
            label="⬇️ Скачать перевод",
            data=full_translation,
            file_name=output_filename,
            mime="text/plain"
        )
        
        st.success(f"Результаты готовы для скачивания: {output_filename}")
    
    except Exception as e:
        st.error(f"Ошибка при экспорте: {str(e)}")

if __name__ == "__main__":
    main()
