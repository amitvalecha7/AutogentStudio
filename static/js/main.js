// Autogent Studio Main JavaScript

class AutogentStudio {
    constructor() {
        this.init();
        this.bindEvents();
        this.initializeFeatures();
    }

    init() {
        // Initialize global variables
        this.sidebar = document.querySelector('.as-sidebar');
        this.main = document.querySelector('.as-main');
        this.currentUser = null;
        this.socket = null;
        this.notifications = [];
        
        // Initialize socket connection for real-time features
        this.initSocket();
        
        // Load user data
        this.loadUserData();
        
        // Initialize tooltips and other UI components
        this.initTooltips();
    }

    bindEvents() {
        // Mobile sidebar toggle
        const sidebarToggle = document.querySelector('.sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }

        // File upload drag and drop
        document.addEventListener('dragover', (e) => this.handleDragOver(e));
        document.addEventListener('drop', (e) => this.handleDrop(e));

        // Form validation
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        });

        // Navigation active state
        this.updateActiveNavigation();

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));

        // Auto-save functionality
        this.initAutoSave();
    }

    initSocket() {
        if (typeof io !== 'undefined') {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Connected to Autogent Studio server');
                this.showNotification('Connected to server', 'success');
            });

            this.socket.on('disconnect', () => {
                console.log('Disconnected from server');
                this.showNotification('Connection lost', 'warning');
            });

            this.socket.on('notification', (data) => {
                this.showNotification(data.message, data.type);
            });
        }
    }

    initializeFeatures() {
        // Initialize feature-specific modules
        this.initFileManager();
        this.initModelSelector();
        this.initQuantumInterface();
        this.initNeuromorphicDashboard();
        this.initSafetyMonitor();
        this.initBlockchainWallet();
    }

    toggleSidebar() {
        if (this.sidebar) {
            this.sidebar.classList.toggle('open');
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const dropZone = e.target.closest('.as-file-upload');
        if (dropZone) {
            dropZone.classList.add('dragover');
        }
    }

    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const dropZone = e.target.closest('.as-file-upload');
        if (dropZone) {
            dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            this.handleFileUpload(files, dropZone);
        }
    }

    handleFileUpload(files, container) {
        const maxSize = 100 * 1024 * 1024; // 100MB
        const allowedTypes = [
            'text/plain', 'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'image/jpeg', 'image/png', 'image/gif', 'audio/mpeg', 'video/mp4'
        ];

        Array.from(files).forEach((file, index) => {
            if (file.size > maxSize) {
                this.showNotification(`File ${file.name} is too large (max 100MB)`, 'error');
                return;
            }

            if (!allowedTypes.includes(file.type)) {
                this.showNotification(`File type ${file.type} is not supported`, 'error');
                return;
            }

            this.uploadFile(file, container);
        });
    }

    async uploadFile(file, container) {
        const formData = new FormData();
        formData.append('file', file);

        // Create progress element
        const progressElement = this.createProgressElement(file.name);
        container.appendChild(progressElement);

        try {
            const response = await fetch('/files/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                this.showNotification(`File ${file.name} uploaded successfully`, 'success');
                this.updateFileList();
            } else {
                throw new Error('Upload failed');
            }
        } catch (error) {
            this.showNotification(`Failed to upload ${file.name}`, 'error');
        } finally {
            progressElement.remove();
        }
    }

    createProgressElement(filename) {
        const element = document.createElement('div');
        element.className = 'as-file-item as-uploading';
        element.innerHTML = `
            <div class="as-file-icon">
                <i class="fas fa-file"></i>
            </div>
            <div class="as-file-info">
                <div class="as-file-name">${filename}</div>
                <div class="as-progress">
                    <div class="as-progress-bar" style="width: 0%"></div>
                </div>
            </div>
        `;
        return element;
    }

    handleFormSubmit(e) {
        const form = e.target;
        
        // Validate form
        if (!this.validateForm(form)) {
            e.preventDefault();
            return false;
        }

        // Show loading state
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            this.setButtonLoading(submitButton, true);
        }
    }

    validateForm(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            const value = field.value.trim();
            const errorElement = field.parentNode.querySelector('.error-message');
            
            if (!value) {
                this.showFieldError(field, 'This field is required');
                isValid = false;
            } else if (field.type === 'email' && !this.validateEmail(value)) {
                this.showFieldError(field, 'Please enter a valid email address');
                isValid = false;
            } else if (field.type === 'password' && value.length < 8) {
                this.showFieldError(field, 'Password must be at least 8 characters');
                isValid = false;
            } else {
                this.clearFieldError(field);
            }
        });

        return isValid;
    }

    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    showFieldError(field, message) {
        this.clearFieldError(field);
        
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message text-danger mt-1';
        errorElement.textContent = message;
        
        field.parentNode.appendChild(errorElement);
        field.classList.add('is-invalid');
    }

    clearFieldError(field) {
        const errorElement = field.parentNode.querySelector('.error-message');
        if (errorElement) {
            errorElement.remove();
        }
        field.classList.remove('is-invalid');
    }

    setButtonLoading(button, loading) {
        if (loading) {
            button.disabled = true;
            button.innerHTML = '<span class="as-loading"></span> Loading...';
        } else {
            button.disabled = false;
            button.innerHTML = button.dataset.originalText || 'Submit';
        }
    }

    updateActiveNavigation() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.as-nav-link');
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            
            const href = link.getAttribute('href');
            if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
                link.classList.add('active');
            }
        });
    }

    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            this.openSearch();
        }
        
        // Ctrl/Cmd + N for new chat
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            window.location.href = '/chat';
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            this.closeModals();
        }
    }

    openSearch() {
        // Implementation for global search
        console.log('Opening search...');
    }

    closeModals() {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }

    initAutoSave() {
        const autoSaveFields = document.querySelectorAll('[data-autosave]');
        
        autoSaveFields.forEach(field => {
            let timeout;
            
            field.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.autoSave(field);
                }, 2000); // Save after 2 seconds of inactivity
            });
        });
    }

    async autoSave(field) {
        const url = field.dataset.autosave;
        const data = { [field.name]: field.value };
        
        try {
            await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(data)
            });
            
            this.showAutoSaveIndicator(field);
        } catch (error) {
            console.error('Auto-save failed:', error);
        }
    }

    showAutoSaveIndicator(field) {
        const indicator = document.createElement('span');
        indicator.className = 'auto-save-indicator text-success';
        indicator.innerHTML = '<i class="fas fa-check"></i> Saved';
        
        field.parentNode.appendChild(indicator);
        
        setTimeout(() => {
            indicator.remove();
        }, 2000);
    }

    loadUserData() {
        // Load user preferences and settings
        const savedTheme = localStorage.getItem('as-theme');
        if (savedTheme) {
            this.setTheme(savedTheme);
        }

        const savedSidebarState = localStorage.getItem('as-sidebar-collapsed');
        if (savedSidebarState === 'true') {
            this.sidebar?.classList.add('collapsed');
        }
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('as-theme', theme);
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type} as-fade-in`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Add to notifications container or create one
        let container = document.querySelector('.notifications-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notifications-container';
            document.body.appendChild(container);
        }

        container.appendChild(notification);

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                notification.remove();
            }, duration);
        }

        // Add to notifications array
        this.notifications.push({
            message,
            type,
            timestamp: new Date()
        });
    }

    initTooltips() {
        // Initialize Bootstrap tooltips if available
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }

    // Feature-specific initialization methods
    initFileManager() {
        const fileUploadAreas = document.querySelectorAll('.as-file-upload');
        fileUploadAreas.forEach(area => {
            area.addEventListener('click', () => {
                const input = document.createElement('input');
                input.type = 'file';
                input.multiple = true;
                input.onchange = (e) => this.handleFileUpload(e.target.files, area);
                input.click();
            });
        });
    }

    initModelSelector() {
        const modelSelectors = document.querySelectorAll('.model-selector');
        modelSelectors.forEach(selector => {
            selector.addEventListener('change', (e) => {
                this.updateModelConfiguration(e.target.value);
            });
        });
    }

    async updateModelConfiguration(modelName) {
        try {
            const response = await fetch('/api/models/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ model: modelName })
            });

            if (response.ok) {
                this.showNotification(`Model updated to ${modelName}`, 'success');
            }
        } catch (error) {
            this.showNotification('Failed to update model', 'error');
        }
    }

    initQuantumInterface() {
        // Initialize quantum circuit visualization
        const quantumCanvas = document.querySelector('#quantum-canvas');
        if (quantumCanvas) {
            this.setupQuantumCircuitEditor(quantumCanvas);
        }
    }

    setupQuantumCircuitEditor(canvas) {
        // Placeholder for quantum circuit editor
        console.log('Initializing quantum circuit editor...');
    }

    initNeuromorphicDashboard() {
        // Initialize neuromorphic computing visualizations
        const neuromorphicContainers = document.querySelectorAll('.neuromorphic-viz');
        neuromorphicContainers.forEach(container => {
            this.createNeuromorphicVisualization(container);
        });
    }

    createNeuromorphicVisualization(container) {
        // Create animated neural network visualization
        container.innerHTML = `
            <div class="neural-network">
                <div class="neuron-layer input-layer">
                    ${Array(4).fill(0).map(() => '<div class="as-neuron"></div>').join('')}
                </div>
                <div class="neuron-layer hidden-layer">
                    ${Array(6).fill(0).map(() => '<div class="as-neuron"></div>').join('')}
                </div>
                <div class="neuron-layer output-layer">
                    ${Array(2).fill(0).map(() => '<div class="as-neuron"></div>').join('')}
                </div>
            </div>
        `;
    }

    initSafetyMonitor() {
        // Initialize AI safety monitoring
        this.startSafetyMonitoring();
    }

    async startSafetyMonitoring() {
        setInterval(async () => {
            try {
                const response = await fetch('/api/safety/status');
                const data = await response.json();
                this.updateSafetyStatus(data);
            } catch (error) {
                console.error('Safety monitoring failed:', error);
            }
        }, 30000); // Check every 30 seconds
    }

    updateSafetyStatus(data) {
        const statusElement = document.querySelector('.safety-status');
        if (statusElement) {
            statusElement.className = `safety-status ${data.status}`;
            statusElement.textContent = `Safety: ${data.status.toUpperCase()}`;
        }
    }

    initBlockchainWallet() {
        const walletButtons = document.querySelectorAll('.wallet-connect-btn');
        walletButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.connectWallet(button.dataset.provider);
            });
        });
    }

    async connectWallet(provider) {
        try {
            if (typeof window.ethereum !== 'undefined' && provider === 'metamask') {
                const accounts = await window.ethereum.request({
                    method: 'eth_requestAccounts'
                });
                
                if (accounts.length > 0) {
                    this.showNotification(`Connected to ${accounts[0]}`, 'success');
                    this.updateWalletStatus(accounts[0]);
                }
            } else {
                this.showNotification('MetaMask not detected', 'warning');
            }
        } catch (error) {
            this.showNotification('Failed to connect wallet', 'error');
        }
    }

    updateWalletStatus(address) {
        const walletStatus = document.querySelector('.wallet-status');
        if (walletStatus) {
            walletStatus.innerHTML = `
                <i class="fas fa-wallet"></i>
                ${address.substring(0, 6)}...${address.substring(address.length - 4)}
            `;
        }
    }

    async updateFileList() {
        try {
            const response = await fetch('/api/files');
            const files = await response.json();
            
            const fileList = document.querySelector('.file-list');
            if (fileList) {
                fileList.innerHTML = files.map(file => `
                    <div class="as-file-item">
                        <div class="as-file-icon">
                            <i class="fas fa-file"></i>
                        </div>
                        <div class="as-file-info">
                            <div class="as-file-name">${file.original_filename}</div>
                            <div class="as-file-meta">${this.formatFileSize(file.file_size)} • ${this.formatDate(file.created_at)}</div>
                        </div>
                        <div class="as-file-actions">
                            <button class="as-btn as-btn-sm" onclick="autogentStudio.previewFile(${file.id})">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="as-btn as-btn-sm as-btn-error" onclick="autogentStudio.deleteFile(${file.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Failed to update file list:', error);
        }
    }

    formatFileSize(bytes) {
        const sizes = ['B', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 B';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString();
    }

    async previewFile(fileId) {
        try {
            const response = await fetch(`/api/files/${fileId}/preview`);
            const data = await response.json();
            
            if (data.success) {
                this.showFilePreview(data);
            } else {
                this.showNotification('Failed to preview file', 'error');
            }
        } catch (error) {
            this.showNotification('Failed to preview file', 'error');
        }
    }

    showFilePreview(data) {
        // Create modal for file preview
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content as-card">
                    <div class="modal-header">
                        <h5 class="modal-title">File Preview</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${this.renderFilePreview(data)}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    renderFilePreview(data) {
        switch (data.type) {
            case 'text':
                return `<pre class="as-code">${data.content}</pre>`;
            case 'image':
                return `<img src="${data.url}" class="img-fluid" alt="File preview">`;
            case 'metadata':
                return `
                    <div class="file-metadata">
                        <p><strong>Filename:</strong> ${data.info.filename}</p>
                        <p><strong>Size:</strong> ${this.formatFileSize(data.info.size)}</p>
                        <p><strong>Type:</strong> ${data.info.type}</p>
                        <p><strong>Processed:</strong> ${data.info.processed ? 'Yes' : 'No'}</p>
                    </div>
                `;
            default:
                return '<p>Preview not available for this file type.</p>';
        }
    }

    async deleteFile(fileId) {
        if (!confirm('Are you sure you want to delete this file?')) {
            return;
        }

        try {
            const response = await fetch(`/api/files/${fileId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showNotification('File deleted successfully', 'success');
                this.updateFileList();
            } else {
                this.showNotification('Failed to delete file', 'error');
            }
        } catch (error) {
            this.showNotification('Failed to delete file', 'error');
        }
    }
}

// Initialize Autogent Studio when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.autogentStudio = new AutogentStudio();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AutogentStudio;
}
