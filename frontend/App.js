// Text to PowerPoint Generator App
class TextToPPTApp {
    constructor() {
        this.apiUrl = this.getApiUrl();
        this.state = {
            textContent: '',
            guidance: '',
            apiProvider: 'openai',
            apiKey: '',
            templateFile: null,
            loading: false,
            error: null,
            success: false
        };
        this.init();
    }

    getApiUrl() {
        // Detect environment and set API URL accordingly
        const hostname = window.location.hostname;
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:5000';
        } else {
            // Replace with your deployed backend URL
            return 'https://your-backend-url.onrender.com';
        }
    }

    init() {
        this.render();
        this.attachEventListeners();
    }

    render() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="container mx-auto px-4 py-8 max-w-4xl">
                <!-- Header -->
                <div class="text-center mb-8">
                    <h1 class="text-4xl font-bold text-gray-900 mb-2">
                        <i class="fas fa-presentation mr-3 text-blue-600"></i>
                        Text to PowerPoint Generator
                    </h1>
                    <p class="text-gray-600 text-lg">Transform your text into professional presentations</p>
                </div>

                <!-- Main Form -->
                <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
                    ${this.state.error ? `
                        <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                            <i class="fas fa-exclamation-triangle mr-2"></i>
                            ${this.state.error}
                        </div>
                    ` : ''}
                    
                    ${this.state.success ? `
                        <div class="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4">
                            <i class="fas fa-check-circle mr-2"></i>
                            Presentation generated successfully!
                        </div>
                    ` : ''}

                    <form id="ppt-form" class="space-y-6">
                        <!-- Text Content -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                <i class="fas fa-file-text mr-2"></i>
                                Your Text Content *
                            </label>
                            <textarea
                                id="textContent"
                                rows="8"
                                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                placeholder="Paste your text, markdown, or long-form content here..."
                                required
                            >${this.state.textContent}</textarea>
                            <p class="text-sm text-gray-500 mt-1">Supports plain text, markdown, and formatted content</p>
                        </div>

                        <!-- Guidance -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                <i class="fas fa-lightbulb mr-2"></i>
                                Presentation Guidance (Optional)
                            </label>
                            <input
                                type="text"
                                id="guidance"
                                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                placeholder="e.g., 'turn into an investor pitch deck', 'make it technical', 'focus on key insights'"
                                value="${this.state.guidance}"
                            >
                        </div>

                        <!-- API Provider Selection -->
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                    <i class="fas fa-robot mr-2"></i>
                                    AI Provider *
                                </label>
                                <select
                                    id="apiProvider"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    required
                                >
                                    <option value="openai" ${this.state.apiProvider === 'openai' ? 'selected' : ''}>OpenAI (GPT)</option>
                                    <option value="anthropic" ${this.state.apiProvider === 'anthropic' ? 'selected' : ''}>Anthropic (Claude)</option>
                                    <option value="google" ${this.state.apiProvider === 'google' ? 'selected' : ''}>Google (Gemini)</option>
                                </select>
                            </div>

                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                    <i class="fas fa-key mr-2"></i>
                                    API Key *
                                </label>
                                <input
                                    type="password"
                                    id="apiKey"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    placeholder="Your API key (not stored)"
                                    value="${this.state.apiKey}"
                                    required
                                >
                            </div>
                        </div>

                        <!-- Template Upload -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                <i class="fas fa-upload mr-2"></i>
                                PowerPoint Template *
                            </label>
                            <div id="fileUploadZone" class="file-upload-zone rounded-lg p-6 text-center cursor-pointer">
                                <input type="file" id="templateFile" accept=".pptx,.potx" class="hidden" required>
                                <i class="fas fa-cloud-upload-alt text-4xl text-gray-400 mb-4"></i>
                                <p class="text-gray-600">
                                    <span class="font-medium text-blue-600">Click to upload</span> or drag and drop
                                </p>
                                <p class="text-sm text-gray-500 mt-2">PPTX or POTX files up to 50MB</p>
                                <div id="fileInfo" class="mt-4 hidden">
                                    <p class="text-sm font-medium text-gray-700"></p>
                                </div>
                            </div>
                        </div>

                        <!-- Submit Button -->
                        <div class="text-center">
                            <button
                                type="submit"
                                id="generateBtn"
                                class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-8 rounded-lg transition duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                                ${this.state.loading ? 'disabled' : ''}
                            >
                                ${this.state.loading ? `
                                    <i class="fas fa-spinner loading-spinner mr-2"></i>
                                    Generating Presentation...
                                ` : `
                                    <i class="fas fa-magic mr-2"></i>
                                    Generate Presentation
                                `}
                            </button>
                        </div>
                    </form>
                </div>

                <!-- Features Section -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div class="bg-white rounded-lg shadow p-6 text-center">
                        <i class="fas fa-brain text-3xl text-blue-600 mb-4"></i>
                        <h3 class="text-lg font-semibold mb-2">Smart Text Analysis</h3>
                        <p class="text-gray-600 text-sm">AI analyzes your content and creates logical slide structure</p>
                    </div>
                    <div class="bg-white rounded-lg shadow p-6 text-center">
                        <i class="fas fa-palette text-3xl text-green-600 mb-4"></i>
                        <h3 class="text-lg font-semibold mb-2">Template Matching</h3>
                        <p class="text-gray-600 text-sm">Preserves your template's fonts, colors, and layout style</p>
                    </div>
                    <div class="bg-white rounded-lg shadow p-6 text-center">
                        <i class="fas fa-download text-3xl text-purple-600 mb-4"></i>
                        <h3 class="text-lg font-semibold mb-2">Ready to Use</h3>
                        <p class="text-gray-600 text-sm">Download your formatted PowerPoint presentation instantly</p>
                    </div>
                </div>

                <!-- Footer -->
                <div class="text-center text-gray-500 text-sm">
                    <p>&copy; 2024 Text to PowerPoint Generator. Your API keys are never stored or logged.</p>
                </div>
            </div>
        `;
    }

    attachEventListeners() {
        // Form submission
        document.getElementById('ppt-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.generatePresentation();
        });

        // File upload handling
        const fileInput = document.getElementById('templateFile');
        const uploadZone = document.getElementById('fileUploadZone');
        
        uploadZone.addEventListener('click', () => fileInput.click());
        
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Drag and drop
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });
        
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });
        
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                this.handleFileSelect({ target: { files: files } });
            }
        });

        // Input change handlers
        document.getElementById('textContent').addEventListener('input', (e) => {
            this.state.textContent = e.target.value;
        });
        
        document.getElementById('guidance').addEventListener('input', (e) => {
            this.state.guidance = e.target.value;
        });
        
        document.getElementById('apiProvider').addEventListener('change', (e) => {
            this.state.apiProvider = e.target.value;
        });
        
        document.getElementById('apiKey').addEventListener('input', (e) => {
            this.state.apiKey = e.target.value;
        });
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.state.templateFile = file;
            const fileInfo = document.getElementById('fileInfo');
            fileInfo.querySelector('p').textContent = `Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`;
            fileInfo.classList.remove('hidden');
        }
    }

    async generatePresentation() {
        try {
            this.setState({ loading: true, error: null, success: false });

            // Validate inputs
            if (!this.state.textContent.trim()) {
                throw new Error('Please enter your text content');
            }
            if (!this.state.apiKey.trim()) {
                throw new Error('Please enter your API key');
            }
            if (!this.state.templateFile) {
                throw new Error('Please upload a PowerPoint template');
            }

            // Prepare form data
            const formData = new FormData();
            formData.append('text_content', this.state.textContent);
            formData.append('guidance', this.state.guidance);
            formData.append('api_provider', this.state.apiProvider);
            formData.append('api_key', this.state.apiKey);
            formData.append('template_file', this.state.templateFile);

            // Make API request
            const response = await fetch(`${this.apiUrl}/generate-presentation`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to generate presentation');
            }

            // Download file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'generated_presentation.pptx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            this.setState({ success: true });
        } catch (error) {
            console.error('Error:', error);
            this.setState({ error: error.message });
        } finally {
            this.setState({ loading: false });
        }
    }

    setState(newState) {
        this.state = { ...this.state, ...newState };
        this.render();
        this.attachEventListeners();
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TextToPPTApp();
});
