class PresentationGenerator {
    constructor() {
        // Since both frontend and backend are on same domain, use relative URLs
        this.apiBaseUrl = '';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupCharacterCounter();
        this.setupDropZone();
    }

    setupEventListeners() {
        document.getElementById('presentationForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.generatePresentation();
        });

        document.getElementById('templateFile').addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });

        document.getElementById('llmProvider').addEventListener('change', () => {
            this.updateApiKeyPlaceholder();
        });
    }

    setupCharacterCounter() {
        const textArea = document.getElementById('inputText');
        const counter = document.getElementById('charCount');

        textArea.addEventListener('input', () => {
            const count = textArea.value.length;
            counter.textContent = `${count.toLocaleString()} characters`;
            
            if (count < 500) {
                counter.className = 'mt-2 text-sm text-gray-500';
            } else if (count < 2000) {
                counter.className = 'mt-2 text-sm text-green-600';
            } else if (count < 5000) {
                counter.className = 'mt-2 text-sm text-blue-600';
            } else {
                counter.className = 'mt-2 text-sm text-orange-600';
            }
        });
    }

    setupDropZone() {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('templateFile');

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
                fileInput.files = files;
            }
        });

        dropZone.addEventListener('click', () => {
            fileInput.click();
        });
    }

    handleFileSelect(file) {
        if (!file) return;

        const dropZoneContent = document.getElementById('dropZoneContent');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');

        const validTypes = ['.pptx', '.potx'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!validTypes.includes(fileExtension)) {
            this.showError('Please upload a valid PowerPoint file (.pptx or .potx)');
            return;
        }

        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showError('File size must be less than 10MB');
            return;
        }

        dropZoneContent.classList.add('hidden');
        fileInfo.classList.remove('hidden');
        fileName.textContent = file.name;
        fileSize.textContent = this.formatFileSize(file.size);

        this.hideMessages();
    }

    updateApiKeyPlaceholder() {
        const provider = document.getElementById('llmProvider').value;
        const apiKeyInput = document.getElementById('apiKey');
        
        const placeholders = {
            openai: 'sk-...',
            anthropic: 'sk-ant-...',
            gemini: 'Your Gemini API key'
        };

        apiKeyInput.placeholder = placeholders[provider] || 'Enter your API key';
    }

    async generatePresentation() {
        const formData = new FormData();
        
        const text = document.getElementById('inputText').value.trim();
        const guidance = document.getElementById('guidance').value.trim();
        const llmProvider = document.getElementById('llmProvider').value;
        const apiKey = document.getElementById('apiKey').value.trim();
        const templateFile = document.getElementById('templateFile').files[0];

        if (!text) {
            this.showError('Please enter some text content');
            return;
        }

        if (!llmProvider) {
            this.showError('Please select an LLM provider');
            return;
        }

        if (!apiKey) {
            this.showError('Please enter your API key');
            return;
        }

        if (!templateFile) {
            this.showError('Please upload a PowerPoint template');
            return;
        }

        formData.append('text', text);
        formData.append('guidance', guidance);
        formData.append('llm_provider', llmProvider);
        formData.append('api_key', apiKey);
        formData.append('template_file', templateFile);

        this.showLoading(true);
        this.hideMessages();

        try {
            this.simulateProgress();

            const response = await axios.post('/api/generate', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                responseType: 'blob',
                timeout: 120000,
            });

            this.downloadFile(response.data, 'generated_presentation.pptx');
            this.showSuccess('Your presentation has been generated and downloaded successfully!');
            
        } catch (error) {
            console.error('Generation error:', error);
            
            if (error.response?.data) {
                try {
                    const text = await error.response.data.text();
                    const errorData = JSON.parse(text);
                    this.showError(errorData.detail || 'An error occurred while generating the presentation');
                } catch {
                    this.showError('An error occurred while generating the presentation');
                }
            } else if (error.code === 'ECONNABORTED') {
                this.showError('Request timed out. Please try again with shorter content or check your connection.');
            } else {
                this.showError('Network error. Please check your connection and try again.');
            }
        } finally {
            this.showLoading(false);
        }
    }

    simulateProgress() {
        const progressSection = document.getElementById('progressSection');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const progressPercent = document.getElementById('progressPercent');
        
        progressSection.classList.remove('hidden');
        
        const stages = [
            { percent: 20, text: 'Analyzing your content...' },
            { percent: 40, text: 'Generating slide structure...' },
            { percent: 60, text: 'Processing template...' },
            { percent: 80, text: 'Creating presentation...' },
            { percent: 95, text: 'Finalizing...' }
        ];

        let currentStage = 0;
        
        const updateProgress = () => {
            if (currentStage < stages.length) {
                const stage = stages[currentStage];
                progressBar.style.width = `${stage.percent}%`;
                progressText.textContent = stage.text;
                progressPercent.textContent = `${stage.percent}%`;
                currentStage++;
                setTimeout(updateProgress, 2000);
            }
        };

        updateProgress();
    }

    downloadFile(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    showLoading(show) {
        const btn = document.getElementById('generateBtn');
        const btnText = document.getElementById('generateBtnText');
        const btnSpinner = document.getElementById('generateBtnSpinner');
        const progressSection = document.getElementById('progressSection');

        btn.disabled = show;
        
        if (show) {
            btnText.textContent = 'Generating...';
            btnSpinner.classList.remove('hidden');
            progressSection.classList.remove('hidden');
        } else {
            btnText.textContent = 'Generate Presentation';
            btnSpinner.classList.add('hidden');
            progressSection.classList.add('hidden');
            
            document.getElementById('progressBar').style.width = '0%';
            document.getElementById('progressText').textContent = 'Processing...';
            document.getElementById('progressPercent').textContent = '0%';
        }
    }

    showError(message) {
        const container = document.getElementById('messageContainer');
        const errorDiv = document.getElementById('errorMessage');
        const errorText = document.getElementById('errorText');
        const successDiv = document.getElementById('successMessage');

        container.classList.remove('hidden');
        errorDiv.classList.remove('hidden');
        successDiv.classList.add('hidden');
        errorText.textContent = message;

        container.scrollIntoView({ behavior: 'smooth' });
    }

    showSuccess(message) {
        const container = document.getElementById('messageContainer');
        const errorDiv = document.getElementById('errorMessage');
        const successDiv = document.getElementById('successMessage');
        const successText = document.getElementById('successText');

        container.classList.remove('hidden');
        errorDiv.classList.add('hidden');
        successDiv.classList.remove('hidden');
        successText.textContent = message;

        container.scrollIntoView({ behavior: 'smooth' });
    }

    hideMessages() {
        const container = document.getElementById('messageContainer');
        const errorDiv = document.getElementById('errorMessage');
        const successDiv = document.getElementById('successMessage');

        container.classList.add('hidden');
        errorDiv.classList.add('hidden');
        successDiv.classList.add('hidden');
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

function setSuggestion(text) {
    document.getElementById('guidance').value = text;
}

function updateApiKeyPlaceholder() {
    if (window.app) {
        window.app.updateApiKeyPlaceholder();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new PresentationGenerator();
});

window.addEventListener('error', (e) => {
    console.error('Application error:', e);
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e);
});
