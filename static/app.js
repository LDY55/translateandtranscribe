// PWA JavaScript функциональность
class AudioTranslatorApp {
    constructor() {
        this.currentTab = 'transcription';
        this.textChunks = [];
        this.currentChunkIndex = 0;
        this.translations = {};
        this.settings = this.loadSettings();
        this.init();
    }

    init() {
        this.setupTabs();
        this.setupEventListeners();
        this.setupPWA();
        this.updateStatus('Приложение готово к работе');
    }

    setupTabs() {
        const tabs = document.querySelectorAll('.tab');
        const tabContents = document.querySelectorAll('.tab-content');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const tabId = tab.dataset.tab;
                
                // Удаляем активные классы
                tabs.forEach(t => t.classList.remove('active'));
                tabContents.forEach(tc => tc.classList.remove('active'));
                
                // Добавляем активные классы
                tab.classList.add('active');
                document.getElementById(tabId).classList.add('active');
                
                this.currentTab = tabId;
            });
        });
    }

    setupEventListeners() {
        // Настройки API
        document.getElementById('settingsBtn').addEventListener('click', () => {
            this.showSettingsModal();
        });

        // Выбор папки для аудио
        document.getElementById('folderInput').addEventListener('change', (e) => {
            this.handleFolderSelect(e);
        });

        // Запуск транскрибации
        document.getElementById('transcribeBtn').addEventListener('click', () => {
            this.startTranscription();
        });

        // Загрузка текстового файла
        document.getElementById('textFileInput').addEventListener('change', (e) => {
            this.handleTextFileSelect(e);
        });

        // Навигация по чанкам
        document.getElementById('prevChunkBtn').addEventListener('click', () => {
            this.navigateChunk(-1);
        });

        document.getElementById('nextChunkBtn').addEventListener('click', () => {
            this.navigateChunk(1);
        });

        // Перевод
        document.getElementById('translateChunkBtn').addEventListener('click', () => {
            this.translateCurrentChunk();
        });

        document.getElementById('translateAllBtn').addEventListener('click', () => {
            this.translateAllChunks();
        });

        // Экспорт
        document.getElementById('exportBtn').addEventListener('click', () => {
            this.exportTranslation();
        });

        // Drag & Drop для файлов
        this.setupDragAndDrop();
    }

    setupDragAndDrop() {
        const dropZones = document.querySelectorAll('.file-list, .form-input[type="file"]');
        
        dropZones.forEach(zone => {
            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                zone.classList.add('dragover');
            });

            zone.addEventListener('dragleave', () => {
                zone.classList.remove('dragover');
            });

            zone.addEventListener('drop', (e) => {
                e.preventDefault();
                zone.classList.remove('dragover');
                
                const files = Array.from(e.dataTransfer.files);
                this.handleFileDrop(files, zone);
            });
        });
    }

    setupPWA() {
        // Регистрация Service Worker
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/static/service-worker.js')
                    .then(registration => {
                        console.log('SW зарегистрирован: ', registration);
                    })
                    .catch(registrationError => {
                        console.log('SW ошибка регистрации: ', registrationError);
                    });
            });
        }

        // Установка PWA
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            this.showInstallBanner();
        });

        // Обработка установки
        document.getElementById('installBtn')?.addEventListener('click', () => {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('Пользователь принял установку');
                        this.hideInstallBanner();
                    }
                    deferredPrompt = null;
                });
            }
        });
    }

    showInstallBanner() {
        const banner = document.getElementById('installBanner');
        if (banner) {
            banner.classList.add('show');
        }
    }

    hideInstallBanner() {
        const banner = document.getElementById('installBanner');
        if (banner) {
            banner.classList.remove('show');
        }
    }

    handleFolderSelect(event) {
        const files = Array.from(event.target.files);
        const audioFiles = files.filter(file => 
            file.type.startsWith('audio/') || 
            ['.mp3', '.wav', '.flac', '.m4a', '.ogg'].some(ext => 
                file.name.toLowerCase().endsWith(ext)
            )
        );

        this.displayAudioFiles(audioFiles);
        this.updateStatus(`Найдено ${audioFiles.length} аудиофайлов`);
    }

    displayAudioFiles(files) {
        const fileList = document.getElementById('audioFileList');
        fileList.innerHTML = '';

        files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <span>${file.name}</span>
                <span>${this.formatFileSize(file.size)}</span>
            `;
            fileList.appendChild(fileItem);
        });

        document.getElementById('transcribeBtn').disabled = files.length === 0;
    }

    async startTranscription() {
        const folderInput = document.getElementById('folderInput');
        const files = Array.from(folderInput.files).filter(file => 
            file.type.startsWith('audio/') || 
            ['.mp3', '.wav', '.flac', '.m4a', '.ogg'].some(ext => 
                file.name.toLowerCase().endsWith(ext)
            )
        );

        if (files.length === 0) {
            this.showAlert('Выберите аудиофайлы', 'warning');
            return;
        }

        const transcribeBtn = document.getElementById('transcribeBtn');
        const progressBar = document.getElementById('transcriptionProgress');
        const resultsArea = document.getElementById('transcriptionResults');

        transcribeBtn.disabled = true;
        transcribeBtn.innerHTML = '<span class="loading"></span> Обработка...';
        
        progressBar.style.display = 'block';
        resultsArea.innerHTML = '';

        try {
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                this.updateStatus(`Обработка: ${file.name}`);
                
                // Обновляем прогресс
                const progress = ((i + 1) / files.length) * 100;
                document.querySelector('.progress-fill').style.width = `${progress}%`;

                // Здесь будет вызов API для транскрибации
                const result = await this.transcribeFile(file);
                
                // Добавляем результат
                const resultDiv = document.createElement('div');
                resultDiv.className = 'card';
                resultDiv.innerHTML = `
                    <h3>${file.name}</h3>
                    <p>${result.text || 'Ошибка транскрибации'}</p>
                `;
                resultsArea.appendChild(resultDiv);
            }

            this.showAlert('Транскрибация завершена!', 'success');

        } catch (error) {
            this.showAlert(`Ошибка: ${error.message}`, 'danger');
        } finally {
            transcribeBtn.disabled = false;
            transcribeBtn.innerHTML = '🚀 Начать транскрибацию';
            progressBar.style.display = 'none';
            this.updateStatus('Готов к работе');
        }
    }

    async transcribeFile(file) {
        // Mock функция для демонстрации
        // В реальном приложении здесь будет API вызов
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({
                    text: `Транскрипция файла ${file.name} (демо версия)`
                });
            }, 1000);
        });
    }

    handleTextFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target.result;
            this.processText(text);
        };
        reader.readAsText(file);
    }

    processText(text) {
        // Разбиваем текст на чанки по 30 предложений
        const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
        this.textChunks = [];
        
        for (let i = 0; i < sentences.length; i += 30) {
            const chunk = sentences.slice(i, i + 30).join('. ') + '.';
            this.textChunks.push(chunk);
        }

        this.currentChunkIndex = 0;
        this.translations = {};
        this.updateChunkDisplay();
        this.updateStatus(`Загружен текст: ${this.textChunks.length} чанков`);
    }

    updateChunkDisplay() {
        if (this.textChunks.length === 0) return;

        const chunkInfo = document.getElementById('chunkInfo');
        const originalText = document.getElementById('originalText');
        const translatedText = document.getElementById('translatedText');
        const prevBtn = document.getElementById('prevChunkBtn');
        const nextBtn = document.getElementById('nextChunkBtn');

        chunkInfo.textContent = `Чанк ${this.currentChunkIndex + 1} из ${this.textChunks.length}`;
        originalText.textContent = this.textChunks[this.currentChunkIndex];
        
        const translation = this.translations[this.currentChunkIndex];
        translatedText.textContent = translation || 'Нажмите кнопку для перевода';

        prevBtn.disabled = this.currentChunkIndex === 0;
        nextBtn.disabled = this.currentChunkIndex >= this.textChunks.length - 1;

        // Обновляем кнопку экспорта
        const hasTranslations = Object.keys(this.translations).length > 0;
        document.getElementById('exportBtn').disabled = !hasTranslations;
    }

    navigateChunk(direction) {
        const newIndex = this.currentChunkIndex + direction;
        if (newIndex >= 0 && newIndex < this.textChunks.length) {
            this.currentChunkIndex = newIndex;
            this.updateChunkDisplay();
        }
    }

    async translateCurrentChunk() {
        if (this.textChunks.length === 0) return;

        if (!this.validateApiSettings()) {
            this.showSettingsModal();
            return;
        }

        const translateBtn = document.getElementById('translateChunkBtn');
        const originalBtn = translateBtn.innerHTML;
        
        translateBtn.disabled = true;
        translateBtn.innerHTML = '<span class="loading"></span> Перевод...';

        try {
            const text = this.textChunks[this.currentChunkIndex];
            const translation = await this.translateText(text);
            
            this.translations[this.currentChunkIndex] = translation;
            this.updateChunkDisplay();
            this.showAlert('Перевод завершен!', 'success');

        } catch (error) {
            this.showAlert(`Ошибка перевода: ${error.message}`, 'danger');
        } finally {
            translateBtn.disabled = false;
            translateBtn.innerHTML = originalBtn;
        }
    }

    async translateAllChunks() {
        if (this.textChunks.length === 0) return;

        if (!this.validateApiSettings()) {
            this.showSettingsModal();
            return;
        }

        const translateAllBtn = document.getElementById('translateAllBtn');
        const originalBtn = translateAllBtn.innerHTML;
        
        translateAllBtn.disabled = true;
        translateAllBtn.innerHTML = '<span class="loading"></span> Перевод всех...';

        try {
            for (let i = 0; i < this.textChunks.length; i++) {
                this.updateStatus(`Перевод чанка ${i + 1} из ${this.textChunks.length}`);
                
                const text = this.textChunks[i];
                const translation = await this.translateText(text);
                
                this.translations[i] = translation;
                
                if (i === this.currentChunkIndex) {
                    this.updateChunkDisplay();
                }
            }

            this.showAlert('Перевод всех чанков завершен!', 'success');

        } catch (error) {
            this.showAlert(`Ошибка перевода: ${error.message}`, 'danger');
        } finally {
            translateAllBtn.disabled = false;
            translateAllBtn.innerHTML = originalBtn;
            this.updateStatus('Готов к работе');
        }
    }

    async translateText(text) {
        // Mock функция для демонстрации
        // В реальном приложении здесь будет API вызов
        return new Promise(resolve => {
            setTimeout(() => {
                resolve(`Перевод: ${text.substring(0, 100)}... (демо версия)`);
            }, 1000);
        });
    }

    exportTranslation() {
        if (Object.keys(this.translations).length === 0) {
            this.showAlert('Нет переводов для экспорта', 'warning');
            return;
        }

        const translatedChunks = [];
        for (let i = 0; i < this.textChunks.length; i++) {
            const translation = this.translations[i] || `[Чанк ${i + 1} не переведен]`;
            translatedChunks.push(translation);
        }

        const fullTranslation = translatedChunks.join('\n\n');
        const blob = new Blob([fullTranslation], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'translation.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showAlert('Перевод экспортирован!', 'success');
    }

    showSettingsModal() {
        const modal = document.getElementById('settingsModal');
        modal.style.display = 'block';
        
        // Заполняем текущие настройки
        document.getElementById('apiEndpoint').value = this.settings.apiEndpoint || '';
        document.getElementById('apiToken').value = this.settings.apiToken || '';
        document.getElementById('apiModel').value = this.settings.apiModel || 'gpt-3.5-turbo';
        document.getElementById('systemPrompt').value = this.settings.systemPrompt || 
            'Переведи следующий текст на русский язык. Сохрани структуру и стиль оригинала.';
    }

    hideSettingsModal() {
        document.getElementById('settingsModal').style.display = 'none';
    }

    saveSettings() {
        this.settings = {
            apiEndpoint: document.getElementById('apiEndpoint').value,
            apiToken: document.getElementById('apiToken').value,
            apiModel: document.getElementById('apiModel').value,
            systemPrompt: document.getElementById('systemPrompt').value
        };

        localStorage.setItem('audioTranslatorSettings', JSON.stringify(this.settings));
        this.hideSettingsModal();
        this.showAlert('Настройки сохранены!', 'success');
    }

    loadSettings() {
        const saved = localStorage.getItem('audioTranslatorSettings');
        return saved ? JSON.parse(saved) : {};
    }

    validateApiSettings() {
        return this.settings.apiEndpoint && this.settings.apiToken;
    }

    handleFileDrop(files, zone) {
        if (zone.closest('#transcription')) {
            // Обработка аудиофайлов
            const audioFiles = files.filter(file => 
                file.type.startsWith('audio/') || 
                ['.mp3', '.wav', '.flac', '.m4a', '.ogg'].some(ext => 
                    file.name.toLowerCase().endsWith(ext)
                )
            );
            this.displayAudioFiles(audioFiles);
        } else if (zone.closest('#translation')) {
            // Обработка текстовых файлов
            const textFile = files.find(file => 
                file.type.startsWith('text/') || 
                ['.txt', '.md', '.rtf'].some(ext => 
                    file.name.toLowerCase().endsWith(ext)
                )
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
        alert.textContent = message;
        
        alertsContainer.appendChild(alert);
        
        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }

    updateStatus(message) {
        document.getElementById('statusText').textContent = message;
    }
}

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
    new AudioTranslatorApp();
});