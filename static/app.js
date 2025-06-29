class AudioTranslatorApp {
    constructor() {
        this.currentChunk = 0;
        this.chunks = [];
        this.translations = {};
        this.audioFiles = [];
        this.deferredPrompt = null;
        this.isTranslating = false;
        this.isTranscribing = false;
    }

    init() {
        this.setupTabs();
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.setupPWA();
        this.loadSettings();
        this.updateStatus("Приложение готово к работе");
    }

    setupTabs() {
        const tabs = document.querySelectorAll('.tab');
        const tabContents = document.querySelectorAll('.tab-content');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetTab = tab.dataset.tab;
                
                // Убираем активные классы
                tabs.forEach(t => t.classList.remove('active'));
                tabContents.forEach(tc => tc.classList.remove('active'));
                
                // Добавляем активные классы
                tab.classList.add('active');
                document.getElementById(targetTab).classList.add('active');
            });
        });
    }

    setupEventListeners() {
        // Кнопки навигации
        document.getElementById('settingsBtn').addEventListener('click', () => this.showSettingsModal());
        
        // Транскрибация
        document.getElementById('folderInput').addEventListener('change', (e) => this.handleFolderSelect(e));
        document.getElementById('transcribeBtn').addEventListener('click', () => this.startTranscription());
        document.getElementById('downloadTranscriptionBtn').addEventListener('click', () => {
            window.open('/api/download-transcription', '_blank');
        });
        
        // Обработка текста
        document.getElementById('textFileInput').addEventListener('change', (e) => this.handleTextFileSelect(e));
        
        // Навигация по чанкам
        document.getElementById('prevChunkBtn').addEventListener('click', () => this.navigateChunk(-1));
        document.getElementById('nextChunkBtn').addEventListener('click', () => this.navigateChunk(1));
        
        // Перевод
        document.getElementById('translateChunkBtn').addEventListener('click', () => this.translateCurrentChunk());
        document.getElementById('translateAllBtn').addEventListener('click', () => this.translateAllChunks());
        document.getElementById('exportBtn').addEventListener('click', () => this.exportTranslation());

        // Закрытие модального окна по клику вне его
        document.getElementById('settingsModal').addEventListener('click', (e) => {
            if (e.target === document.getElementById('settingsModal')) {
                this.hideSettingsModal();
            }
        });

        // Закрытие модального окна по ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && document.getElementById('settingsModal').style.display !== 'none') {
                this.hideSettingsModal();
            }
        });
    }

    setupDragAndDrop() {
        const audioFileList = document.getElementById('audioFileList');
        const translationTab = document.querySelector('#translation .file-list');

        // Drag and drop для аудиофайлов
        audioFileList.addEventListener('dragover', (e) => {
            e.preventDefault();
            audioFileList.classList.add('drag-over');
        });

        audioFileList.addEventListener('dragleave', () => {
            audioFileList.classList.remove('drag-over');
        });

        audioFileList.addEventListener('drop', (e) => {
            e.preventDefault();
            audioFileList.classList.remove('drag-over');
            this.handleFileDrop(e.dataTransfer.files, 'audio');
        });

        // Drag and drop для текстовых файлов
        translationTab.addEventListener('dragover', (e) => {
            e.preventDefault();
            translationTab.classList.add('drag-over');
        });

        translationTab.addEventListener('dragleave', () => {
            translationTab.classList.remove('drag-over');
        });

        translationTab.addEventListener('drop', (e) => {
            e.preventDefault();
            translationTab.classList.remove('drag-over');
            this.handleFileDrop(e.dataTransfer.files, 'text');
        });
    }

    setupPWA() {
        // Регистрация Service Worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/service-worker.js')
                .then(registration => {
                    console.log('Service Worker зарегистрирован:', registration);
                })
                .catch(error => {
                    console.log('Ошибка регистрации Service Worker:', error);
                });
        }

        // Обработка события beforeinstallprompt
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallBanner();
        });

        // Кнопка установки
        document.getElementById('installBtn').addEventListener('click', () => {
            if (this.deferredPrompt) {
                this.deferredPrompt.prompt();
                this.deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('Пользователь установил PWA');
                        this.showAlert('Приложение устанавливается...', 'success');
                        this.hideInstallBanner();
                    } else {
                        this.showAlert('Установка отменена', 'info');
                    }
                    this.deferredPrompt = null;
                });
            } else {
                // Показать инструкции для ручной установки
                this.showManualInstallInstructions();
            }
        });

        // Проверка, установлено ли приложение
        window.addEventListener('appinstalled', () => {
            console.log('PWA установлено');
            this.hideInstallBanner();
        });

        // Показываем баннер установки для некоторых браузеров
        if (window.matchMedia('(display-mode: browser)').matches) {
            setTimeout(() => this.showInstallBanner(), 3000);
        }
    }

    showInstallBanner() {
        const banner = document.getElementById('installBanner');
        if (banner && !window.matchMedia('(display-mode: standalone)').matches) {
            banner.style.display = 'flex';
        }
    }

    hideInstallBanner() {
        const banner = document.getElementById('installBanner');
        if (banner) {
            banner.style.display = 'none';
        }
    }

    showManualInstallInstructions() {
        const instructions = `
            <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 2000; display: flex; align-items: center; justify-content: center;">
                <div style="background: white; padding: 30px; border-radius: 12px; max-width: 500px; margin: 20px;">
                    <h3 style="margin-top: 0; color: #333;">Установка приложения</h3>
                    <div style="line-height: 1.6; color: #555;">
                        <p><strong>Chrome/Edge:</strong> Меню (⋮) → "Установить приложение"</p>
                        <p><strong>Firefox:</strong> Адресная строка → иконка "Установить"</p>
                        <p><strong>Safari (iOS):</strong> Поделиться → "На экран Домой"</p>
                        <p><strong>Samsung Internet:</strong> Меню → "Добавить страницу в"</p>
                        <p style="margin-top: 20px; padding: 10px; background: #f0f8ff; border-radius: 6px; font-size: 14px;">
                            💡 После установки приложение будет работать без браузерного интерфейса как обычная программа.
                        </p>
                    </div>
                    <button onclick="this.closest('div').remove()" style="
                        margin-top: 20px; padding: 10px 20px; background: #1f77b4; color: white; 
                        border: none; border-radius: 6px; cursor: pointer; font-size: 16px;
                    ">Понятно</button>
                </div>
            </div>
        `;
        
        const modal = document.createElement('div');
        modal.innerHTML = instructions;
        document.body.appendChild(modal);
    }

    showPyTorchInstallPrompt(errorData) {
        const instructions = `
            <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 2000; display: flex; align-items: center; justify-content: center;">
                <div style="background: white; padding: 30px; border-radius: 12px; max-width: 600px; margin: 20px;">
                    <h3 style="margin-top: 0; color: #333;">Установка PyTorch для транскрибации</h3>
                    <div style="line-height: 1.6; color: #555;">
                        <p>${errorData.error}</p>
                        <p style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 6px; font-size: 14px; border-left: 4px solid #ffc107;">
                            ⚠️ <strong>Внимание:</strong> Установка PyTorch займет несколько минут и потребует около 500MB места на диске.
                        </p>
                        <p style="padding: 10px; background: #f0f8ff; border-radius: 6px; font-size: 14px;">
                            После установки будет доступна транскрибация аудио с помощью русской модели Whisper.
                        </p>
                    </div>
                    <div style="margin-top: 20px;">
                        <button id="installPyTorchBtn" style="
                            padding: 12px 24px; background: #28a745; color: white; margin-right: 10px;
                            border: none; border-radius: 6px; cursor: pointer; font-size: 16px;
                        ">Установить PyTorch</button>
                        <button onclick="this.closest('div').remove()" style="
                            padding: 12px 24px; background: #6c757d; color: white; 
                            border: none; border-radius: 6px; cursor: pointer; font-size: 16px;
                        ">Отмена</button>
                    </div>
                </div>
            </div>
        `;
        
        const modal = document.createElement('div');
        modal.innerHTML = instructions;
        document.body.appendChild(modal);
        
        // Добавляем обработчик для кнопки установки
        modal.querySelector('#installPyTorchBtn').addEventListener('click', () => {
            this.installPyTorch(modal);
        });
    }

    async installPyTorch(modal) {
        const installBtn = modal.querySelector('#installPyTorchBtn');
        const originalText = installBtn.textContent;
        
        try {
            installBtn.disabled = true;
            installBtn.textContent = 'Установка...';
            
            const response = await fetch('/api/install-pytorch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showAlert(result.message, 'success');
                modal.remove();
                // Перезагружаем страницу для применения изменений
                setTimeout(() => window.location.reload(), 1000);
            } else {
                this.showAlert('Ошибка установки: ' + result.error, 'error');
                installBtn.disabled = false;
                installBtn.textContent = originalText;
            }
            
        } catch (error) {
            this.showAlert('Ошибка установки: ' + error.message, 'error');
            installBtn.disabled = false;
            installBtn.textContent = originalText;
        }
    }

    handleFolderSelect(event) {
        const files = Array.from(event.target.files);
        const audioExtensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac', '.wma', '.mp4'];
        
        this.audioFiles = files.filter(file => 
            audioExtensions.some(ext => file.name.toLowerCase().endsWith(ext))
        );

        this.displayAudioFiles(this.audioFiles);
    }

    displayAudioFiles(files) {
        const fileList = document.getElementById('audioFileList');
        const transcribeBtn = document.getElementById('transcribeBtn');

        if (files.length === 0) {
            fileList.innerHTML = '<p>Перетащите аудиофайлы сюда или выберите папку выше</p>';
            transcribeBtn.disabled = true;
            return;
        }

        fileList.innerHTML = `
            <h4>Найдено аудиофайлов: ${files.length}</h4>
            <ul class="file-list-items">
                ${files.map(file => `
                    <li class="file-item">
                        <span class="file-name">${file.name}</span>
                        <span class="file-size">${this.formatFileSize(file.size)}</span>
                    </li>
                `).join('')}
            </ul>
        `;

        transcribeBtn.disabled = false;
    }

    async startTranscription() {
        if (this.isTranscribing || this.audioFiles.length === 0) return;

        this.isTranscribing = true;
        const transcribeBtn = document.getElementById('transcribeBtn');
        const progressBar = document.getElementById('transcriptionProgress');
        const progressText = progressBar.querySelector('.progress-text');
        const progressFill = progressBar.querySelector('.progress-fill');
        const resultsDiv = document.getElementById('transcriptionResults');

        transcribeBtn.disabled = true;
        transcribeBtn.textContent = 'Транскрибация...';
        progressBar.style.display = 'block';
        progressText.textContent = '';
        progressFill.style.width = '0%';
        resultsDiv.innerHTML = '';

        const formData = new FormData();
        this.audioFiles.forEach(file => {
            formData.append('files', file);
        });

        try {
            const response = await fetch('/api/transcribe', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!result.success) {
                this.showAlert(result.error, 'error');
                progressBar.style.display = 'none';
                progressText.textContent = '';
                return;
            }

            // Polling для получения статуса
            const pollStatus = async () => {
                try {
                    const statusResponse = await fetch('/api/transcription-status');
                    const status = await statusResponse.json();

                    const progressFill = progressBar.querySelector('.progress-fill');
                    const progressText = progressBar.querySelector('.progress-text');
                    progressFill.style.width = status.progress + '%';
                    progressText.textContent = `${status.status} (${Math.round(status.progress)}%)`;

                    if (status.status === 'completed') {
                        this.displayTranscriptionResults(status.results);
                        this.updateStatus('Транскрибация завершена');
                        progressBar.style.display = 'none';
                        progressText.textContent = '';
                        // Показываем кнопку скачивания
                        document.getElementById('downloadTranscriptionBtn').style.display = 'inline-block';
                    } else if (status.status === 'error') {
                        this.showAlert(status.error || 'Ошибка транскрибации', 'error');
                        progressBar.style.display = 'none';
                        progressText.textContent = '';
                    } else if (status.status === 'processing') {
                        this.updateStatus(status.status || 'Обработка...');
                        setTimeout(pollStatus, 1000);
                    }
                } catch (error) {
                    this.showAlert('Ошибка получения статуса: ' + error.message, 'error');
                }
            };

            setTimeout(pollStatus, 1000);

        } catch (error) {
            const errorData = error.response?.data;
            if (errorData?.install_available) {
                this.showPyTorchInstallPrompt(errorData);
            } else {
                this.showAlert('Ошибка запуска транскрибации: ' + error.message, 'error');
            }
            progressBar.style.display = 'none';
            progressText.textContent = '';
        } finally {
            this.isTranscribing = false;
            transcribeBtn.disabled = false;
            transcribeBtn.textContent = '🚀 Начать транскрибацию';
        }
    }

    displayTranscriptionResults(results) {
        const resultsDiv = document.getElementById('transcriptionResults');

        resultsDiv.innerHTML = `
            <h3>Результаты транскрибации</h3>
            <div class="results-list">
                ${results.map((result, index) => `
                    <div class="result-item ${result.success ? 'success' : 'error'}">
                        <h4>${result.filename}</h4>
                        ${result.success ?
                            `<div class="transcription-text">${result.text}</div>
                             <button class="btn btn-outline download-txt" data-index="${index}">💾 Скачать TXT</button>` :
                            `<div class="error-text">Ошибка: ${result.error}</div>`
                        }
                    </div>
                `).join('')}
            </div>
        `;

        resultsDiv.querySelectorAll('.download-txt').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = btn.dataset.index;
                window.open('/api/download-transcription/' + idx, '_blank');
            });
        });
    }

    async handleTextFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (e) => {
            const text = e.target.result;
            await this.processText(text);
        };
        reader.readAsText(file);
    }

    async processText(text) {
        try {
            const response = await fetch('/api/process-text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    sentences_per_chunk: 30
                })
            });

            const result = await response.json();
            
            if (!result.success) {
                this.showAlert(result.error, 'error');
                return;
            }

            this.chunks = result.chunks;
            this.currentChunk = 0;
            this.translations = {};

            document.getElementById('textProcessingCard').style.display = 'block';
            this.updateChunkDisplay();
            this.updateOverallTranslationProgress();
            this.updateStatus(`Текст разделен на ${this.chunks.length} частей`);

        } catch (error) {
            this.showAlert('Ошибка обработки текста: ' + error.message, 'error');
        }
    }

    updateChunkDisplay() {
        if (this.chunks.length === 0) return;

        const chunkInfo = document.getElementById('chunkInfo');
        const originalText = document.getElementById('originalText');
        const translatedText = document.getElementById('translatedText');
        const prevBtn = document.getElementById('prevChunkBtn');
        const nextBtn = document.getElementById('nextChunkBtn');
        const translateBtn = document.getElementById('translateChunkBtn');
        const translateAllBtn = document.getElementById('translateAllBtn');
        const exportBtn = document.getElementById('exportBtn');

        chunkInfo.textContent = `Часть ${this.currentChunk + 1} из ${this.chunks.length}`;
        originalText.textContent = this.chunks[this.currentChunk];

        const translation = this.translations[this.currentChunk];
        translatedText.textContent = translation || 'Нажмите кнопку для перевода';

        prevBtn.disabled = this.currentChunk === 0;
        nextBtn.disabled = this.currentChunk === this.chunks.length - 1;
        translateBtn.disabled = false;
        translateAllBtn.disabled = false;
        exportBtn.disabled = Object.keys(this.translations).length === 0;

        this.updateOverallTranslationProgress();
    }

    navigateChunk(direction) {
        const newChunk = this.currentChunk + direction;
        if (newChunk >= 0 && newChunk < this.chunks.length) {
            this.currentChunk = newChunk;
            this.updateChunkDisplay();
        }
    }

    async translateCurrentChunk() {
        if (this.isTranslating) return;

        const settings = this.getApiSettings();
        if (!this.validateApiSettings(settings)) {
            this.showAlert('Настройте API в настройках', 'warning');
            return;
        }

        await this.translateText(this.currentChunk, false);
    }

    async translateAllChunks() {
        if (this.isTranslating) return;

        const settings = this.getApiSettings();
        if (!this.validateApiSettings(settings)) {
            this.showAlert('Настройте API в настройках', 'warning');
            return;
        }

        await this.translateText(null, true);
    }

    async translateText(chunkIndex, translateAll) {
        this.isTranslating = true;
        
        const translateBtn = document.getElementById('translateChunkBtn');
        const translateAllBtn = document.getElementById('translateAllBtn');
        
        translateBtn.disabled = true;
        translateAllBtn.disabled = true;
        translateAllBtn.textContent = translateAll ? 'Перевожу...' : 'Перевести все';

        const progressBar = document.getElementById('translationProgress');
        const progressTextElem = progressBar.querySelector('.progress-text');
        const progressFill = progressBar.querySelector('.progress-fill');
        progressBar.style.display = 'block';
        progressTextElem.textContent = '';
        progressFill.style.width = '0%';

        try {
            const settings = this.getApiSettings();
            const response = await fetch('/api/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    settings: settings,
                    chunk_index: chunkIndex,
                    translate_all: translateAll
                })
            });

            const result = await response.json();
            
            if (!result.success) {
                this.showAlert(result.error, 'error');
                return;
            }

            // Polling для получения статуса перевода
            const pollStatus = async () => {
                try {
                    const statusResponse = await fetch('/api/translation-status');
                    const status = await statusResponse.json();

                    if (status.status === 'completed') {
                        this.translations = { ...this.translations, ...status.translations };
                        this.updateChunkDisplay();
                        this.updateOverallTranslationProgress();
                        this.updateStatus(translateAll ? 'Все части переведены' : 'Часть переведена');
                        progressBar.style.display = 'none';
                        progressTextElem.textContent = '';
                    } else if (status.status === 'error') {
                        this.showAlert(status.error || 'Ошибка перевода', 'error');
                        progressBar.style.display = 'none';
                        progressTextElem.textContent = '';
                    } else if (status.status === 'processing') {
                        if (translateAll) {
                            progressFill.style.width = status.progress + '%';
                            progressTextElem.textContent = `${status.progress}%`;
                            this.updateOverallTranslationProgress();
                        }
                        setTimeout(pollStatus, 1000);
                    }
                } catch (error) {
                    this.showAlert('Ошибка получения статуса: ' + error.message, 'error');
                }
            };

            setTimeout(pollStatus, 1000);

        } catch (error) {
            this.showAlert('Ошибка перевода: ' + error.message, 'error');
        } finally {
            this.isTranslating = false;
            translateBtn.disabled = false;
            translateAllBtn.disabled = false;
            translateAllBtn.textContent = '🚀 Перевести все';
            progressBar.style.display = 'none';
            progressTextElem.textContent = '';
        }
    }

    exportTranslation() {
        fetch('/api/export-translation')
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    const blob = new Blob([result.translation], { type: 'text/plain;charset=utf-8' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = result.filename;
                    a.click();
                    URL.revokeObjectURL(url);
                    this.updateStatus('Файл сохранен');
                } else {
                    this.showAlert(result.error, 'error');
                }
            })
            .catch(error => {
                this.showAlert('Ошибка экспорта: ' + error.message, 'error');
            });
    }

    showSettingsModal() {
        document.getElementById('settingsModal').style.display = 'flex';
        this.loadSettingsInModal();
    }

    hideSettingsModal() {
        document.getElementById('settingsModal').style.display = 'none';
    }

    loadSettingsInModal() {
        const settings = this.getApiSettings();
        document.getElementById('apiEndpoint').value = settings.api_endpoint || '';
        document.getElementById('apiToken').value = settings.api_token || '';
        document.getElementById('apiModel').value = settings.api_model || 'gpt-3.5-turbo';
        document.getElementById('systemPrompt').value = settings.system_prompt || 'Переведи следующий текст на русский язык. Сохрани структуру и стиль оригинала.';
    }

    saveSettings() {
        const settings = {
            api_endpoint: document.getElementById('apiEndpoint').value,
            api_token: document.getElementById('apiToken').value,
            api_model: document.getElementById('apiModel').value,
            system_prompt: document.getElementById('systemPrompt').value
        };

        fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                // Сохраняем настройки локально
                localStorage.setItem('api_endpoint', settings.api_endpoint);
                localStorage.setItem('api_token', settings.api_token);
                localStorage.setItem('api_model', settings.api_model);
                localStorage.setItem('system_prompt', settings.system_prompt);
                this.showAlert('Настройки сохранены', 'success');
                this.hideSettingsModal();
            } else {
                this.showAlert(result.error, 'error');
            }
        })
        .catch(error => {
            this.showAlert('Ошибка сохранения: ' + error.message, 'error');
        });
    }

    loadSettings() {
        fetch('/api/settings')
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    const s = result.settings;
                    localStorage.setItem('api_endpoint', s.api_endpoint || '');
                    localStorage.setItem('api_token', s.api_token || '');
                    localStorage.setItem('api_model', s.api_model || 'gpt-3.5-turbo');
                    localStorage.setItem('system_prompt', s.system_prompt || '');
                }
            })
            .catch(error => {
                console.error('Ошибка загрузки настроек:', error);
            });
    }

    getApiSettings() {
        // Получаем настройки из формы или localStorage
        return {
            api_endpoint: document.getElementById('apiEndpoint')?.value || localStorage.getItem('api_endpoint') || '',
            api_token: document.getElementById('apiToken')?.value || localStorage.getItem('api_token') || '',
            api_model: document.getElementById('apiModel')?.value || localStorage.getItem('api_model') || 'gpt-3.5-turbo',
            system_prompt: document.getElementById('systemPrompt')?.value || localStorage.getItem('system_prompt') || 'Переведи следующий текст на русский язык.'
        };
    }

    validateApiSettings(settings) {
        return settings.api_endpoint && settings.api_token;
    }

    handleFileDrop(files, zone) {
        const fileArray = Array.from(files);
        
        if (zone === 'audio') {
            const audioExtensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac', '.wma', '.mp4'];
            this.audioFiles = fileArray.filter(file => 
                audioExtensions.some(ext => file.name.toLowerCase().endsWith(ext))
            );
            this.displayAudioFiles(this.audioFiles);
        } else if (zone === 'text') {
            const textFile = fileArray.find(file => 
                file.name.toLowerCase().endsWith('.txt') || 
                file.name.toLowerCase().endsWith('.md') ||
                file.name.toLowerCase().endsWith('.rtf') ||
                file.type.startsWith('text/')
            );
            
            if (textFile) {
                const reader = new FileReader();
                reader.onload = (e) => this.processText(e.target.result);
                reader.readAsText(textFile);
            }
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showAlert(message, type = 'info') {
        const alertsContainer = document.getElementById('alerts');
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">&times;</button>
        `;
        
        alertsContainer.appendChild(alert);
        
        // Автоматическое удаление через 5 секунд
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
            }
        }, 5000);
    }

    updateStatus(message) {
        document.getElementById('statusText').textContent = message;
    }

    updateOverallTranslationProgress() {
        const bar = document.getElementById('overallTranslationProgress');
        if (!bar) return;

        const fill = bar.querySelector('.progress-fill');
        const text = bar.querySelector('.progress-text');

        const total = this.chunks.length;
        const completed = Object.keys(this.translations).length;
        const percent = total ? Math.round((completed / total) * 100) : 0;

        bar.style.display = 'block';
        fill.style.width = percent + '%';
        text.textContent = percent + '%';
    }
}

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AudioTranslatorApp();
    window.app.init();
});