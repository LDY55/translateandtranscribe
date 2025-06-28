# Audio Transcription and Translation App

## Overview

This is a Python-based Streamlit application that provides audio transcription and text translation capabilities. The app uses Whisper models for speech-to-text conversion and API-based translation services for text translation. It's designed for processing Russian audio content with translation capabilities.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

- **Frontend**: Streamlit web interface for user interaction
- **Processing Layer**: Separate modules for transcription, translation, and text processing
- **Configuration Management**: JSON-based settings storage
- **Model Integration**: Hugging Face Transformers for Whisper models

## Key Components

### 1. Frontend Layer (`app.py`)
- **Technology**: Streamlit
- **Purpose**: Provides web-based UI for file uploads, settings configuration, and result display
- **Features**: 
  - Session state management for persistent data
  - Sidebar for API configuration
  - File upload interface for audio files

### 2. Transcription Module (`transcription.py`)
- **Technology**: Whisper models via Hugging Face Transformers
- **Primary Model**: `antony66/whisper-large-v3-russian` (Russian-optimized)
- **Fallback Model**: `openai/whisper-large-v3`
- **Features**:
  - Automatic GPU/CPU detection
  - Audio preprocessing (mono, 16kHz conversion)
  - Chunked processing for large files
  - Progress tracking with tqdm

### 3. Translation Module (`translation.py`)
- **Technology**: REST API integration (configurable endpoint)
- **Default Model**: GPT-3.5-turbo
- **Features**:
  - Configurable API endpoints and tokens
  - Retry mechanism for failed requests
  - Session-based HTTP connections
  - Error handling and timeouts

### 4. Text Processing Module (`text_processor.py`)
- **Technology**: NLTK with regex fallback
- **Purpose**: Text chunking and sentence segmentation
- **Features**:
  - Intelligent sentence splitting
  - Russian language support
  - Graceful degradation when NLTK unavailable

### 5. Utilities Module (`utils.py`)
- **Purpose**: Configuration management and helper functions
- **Features**:
  - JSON-based settings persistence
  - Supported audio format definitions
  - Default configuration handling

## Data Flow

1. **Audio Input**: User uploads audio files through Streamlit interface
2. **Preprocessing**: Audio converted to mono 16kHz format using pydub
3. **Transcription**: Whisper model processes audio chunks to generate text
4. **Text Processing**: Transcribed text is segmented into manageable chunks
5. **Translation**: Text chunks sent to configured API for translation
6. **Output**: Results displayed in Streamlit interface with session persistence

## External Dependencies

### Core Libraries
- **streamlit**: Web interface framework
- **torch**: PyTorch for model inference
- **transformers**: Hugging Face model integration
- **pydub**: Audio file processing
- **nltk**: Natural language processing
- **numpy**: Numerical operations
- **requests**: HTTP API communication
- **tqdm**: Progress bars

### Models
- **Whisper Large V3 Russian**: Primary transcription model
- **OpenAI Whisper Large V3**: Fallback transcription model

### External Services
- **Translation API**: Configurable endpoint (expects OpenAI-compatible format)

## Deployment Strategy

The application is designed for local deployment with the following considerations:

- **Model Storage**: Models downloaded and cached locally via Hugging Face
- **Configuration**: Settings stored in local `settings.json` file
- **Session Management**: Streamlit session state for temporary data
- **Resource Management**: Automatic GPU/CPU detection and optimization

### Hardware Requirements
- **GPU**: CUDA-compatible GPU recommended for faster transcription
- **Memory**: Sufficient RAM for loading Whisper Large models
- **Storage**: Space for model caching and temporary audio processing

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Changelog:
- June 28, 2025. Initial setup