# Audio Transcription and Translation App

## Overview

This project provides a Progressive Web App for audio transcription and text translation. It uses Whisper models for speech-to-text conversion and API-based translation services. The PWA can be installed on the desktop and works offline for cached resources.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

 - **Frontend**: Progressive Web App (Flask-based) for user interaction
- **Processing Layer**: Separate modules for transcription, translation, and text processing
- **Configuration Management**: JSON-based settings storage
- **Model Integration**: Hugging Face Transformers for Whisper models

## Key Components

### 1. Frontend Layer (`pwa_simple.py`)
 - **Technology**: Flask (PWA)
 - **Purpose**: Web interface for file uploads, translation settings and model interaction
 - **Features**:
   - API endpoints for transcription and translation
   - Can be installed as a desktop-like application

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

1. **Audio Input**: User uploads audio files through the web interface
2. **Preprocessing**: Audio converted to mono 16kHz format using pydub
3. **Transcription**: Whisper model processes audio chunks to generate text
4. **Text Processing**: Transcribed text is segmented into manageable chunks
5. **Translation**: Text chunks sent to configured API for translation
6. **Output**: Results displayed in the PWA interface

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
 - **Session Management**: Browser session storage for temporary data
- **Resource Management**: Automatic GPU/CPU detection and optimization

### Hardware Requirements
- **GPU**: CUDA-compatible GPU recommended for faster transcription
- **Memory**: Sufficient RAM for loading Whisper Large models
- **Storage**: Space for model caching and temporary audio processing

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

### June 28, 2025 - PWA Implementation
- Added Progressive Web App version for Windows desktop installation
- Created Flask-based web server with modern REST API
- Implemented Service Worker for offline caching
- Added manifest.json for PWA installation capability
- Built responsive web interface with drag-and-drop support
- Maintained all original functionality (transcription + translation)
- PWA can be installed as desktop app without browser UI

### June 28, 2025 - Initial setup
- Created initial application prototype
- Implemented audio transcription with Whisper models
- Added text translation via API
- Built text processing with chunking functionality