// Autogent Studio - Main JavaScript
class AutogentStudio {
    constructor() {
        this.socket = null;
        this.currentUser = null;
        this.notifications = [];
        this.isConnected = false;
        this.init();
    }

    init() {
        this.initializeWebSocket();
        this.setupEventListeners();
        this.loadUserData();
        this.initializeComponents();
    }

    // WebSocket Connection
    initializeWebSocket() {
        if (typeof io !== 'undefined') {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Connected to Autogent Studio');
                this.isConnected = true;
                this.updateConnectionStatus(true);
            });

            this.socket.on('disconnect', () => {
                console.log('Disconnected from Autogent Studio');
                this.isConnected = false;
                this.updateConnectionStatus(false);
            });

            this.socket.on('system_notification', (data) => {
                this.showNotification(data.message, data.type, data.priority);
            });

            this.socket.on('error', (error) => {
                console.error('WebSocket error:', error);
                this.showNotification('Connection error occurred', 'danger');
            });
        }
    }

    // Event Listeners
    setupEventListeners() {
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'k':
                        e.preventDefault();
                        this.openGlobalSearch();
                        break;
                    case 'n':
                        e.preventDefault();
                        this.createNewChat();
                        break;
                    case '/':
                        e.preventDefault();
                        this.openCommandPalette();
                        break;
                }
            }
        });

        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }

        // Global search
        const searchInput = document.getElementById('globalSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.debounce(this.performGlobalSearch.bind(this), 300)(e.target.value);
            });
        }

        // Notification cleanup
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('notification-close')) {
                this.closeNotification(e.target.closest('.notification'));
            }
        });

        // Auto-save functionality
        const autoSaveElements = document.querySelectorAll('[data-autosave]');
        autoSaveElements.forEach(element => {
            element.addEventListener('input', () => {
                this.debounce(this.autoSave.bind(this), 1000)(element);
            });
        });
    }

    // Load user data
    loadUserData() {
        const userDataElement = document.getElementById('userData');
        if (userDataElement) {
            try {
                this.currentUser = JSON.parse(userDataElement.textContent);
            } catch (e) {
                console.error('Error parsing user data:', e);
            }
        }
    }

    // Initialize components
    initializeComponents() {
        this.initializeTooltips();
        this.initializePopovers();
        this.initializeScrollspy();
        this.initializeFileUpload();
        this.initializeDragDrop();
        this.initializeCharts();
        this.initializeProgressBars();
    }

    // Initialize tooltips
    initializeTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Initialize popovers
    initializePopovers() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(popoverTriggerEl => {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }

    // Initialize scrollspy
    initializeScrollspy() {
        const scrollSpyElements = document.querySelectorAll('[data-bs-spy="scroll"]');
        scrollSpyElements.forEach(element => {
            new bootstrap.ScrollSpy(element);
        });
    }

    // Initialize file upload
    initializeFileUpload() {
        const fileUploadAreas = document.querySelectorAll('.file-upload-area');
        fileUploadAreas.forEach(area => {
            this.setupFileUpload(area);
        });
    }

    // Setup file upload
    setupFileUpload(area) {
        const input = area.querySelector('input[type="file"]');
        if (!input) return;

        // Click to upload
        area.addEventListener('click', () => {
            input.click();
        });

        // Drag and drop
        area.addEventListener('dragover', (e) => {
            e.preventDefault();
            area.classList.add('dragover');
        });

        area.addEventListener('dragleave', () => {
            area.classList.remove('dragover');
        });

        area.addEventListener('drop', (e) => {
            e.preventDefault();
            area.classList.remove('dragover');
            const files = e.dataTransfer.files;
            this.handleFiles(files);
        });

        // File input change
        input.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });
    }

    // Handle files
    handleFiles(files) {
        Array.from(files).forEach(file => {
            this.uploadFile(file);
        });
    }

    // Upload file
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                this.showNotification(`File "${file.name}" uploaded successfully`, 'success');
                this.updateFileList(result);
            } else {
                throw new Error('Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showNotification(`Failed to upload "${file.name}"`, 'danger');
        }
    }

    // Initialize drag and drop
    initializeDragDrop() {
        const draggableElements = document.querySelectorAll('[draggable="true"]');
        const dropZones = document.querySelectorAll('[data-drop-zone]');

        draggableElements.forEach(element => {
            element.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', element.id);
                element.classList.add('dragging');
            });

            element.addEventListener('dragend', () => {
                element.classList.remove('dragging');
            });
        });

        dropZones.forEach(zone => {
            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                zone.classList.add('drag-over');
            });

            zone.addEventListener('dragleave', () => {
                zone.classList.remove('drag-over');
            });

            zone.addEventListener('drop', (e) => {
                e.preventDefault();
                zone.classList.remove('drag-over');
                const draggedId = e.dataTransfer.getData('text/plain');
                const draggedElement = document.getElementById(draggedId);
                if (draggedElement) {
                    this.handleDrop(draggedElement, zone);
                }
            });
        });
    }

    // Handle drop
    handleDrop(draggedElement, dropZone) {
        const dropType = dropZone.dataset.dropZone;
        const draggedType = draggedElement.dataset.type;

        console.log(`Dropped ${draggedType} onto ${dropType}`);
        
        // Emit drop event for specific handling
        this.emit('drop', {
            draggedElement,
            dropZone,
            draggedType,
            dropType
        });
    }

    // Initialize charts
    initializeCharts() {
        const chartElements = document.querySelectorAll('[data-chart]');
        chartElements.forEach(element => {
            this.createChart(element);
        });
    }

    // Create chart
    createChart(element) {
        const chartType = element.dataset.chart;
        const chartData = element.dataset.chartData;
        
        if (!chartData) return;

        try {
            const data = JSON.parse(chartData);
            const ctx = element.getContext('2d');
            
            new Chart(ctx, {
                type: chartType,
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: element.dataset.chartTitle || 'Chart'
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Chart creation error:', error);
        }
    }

    // Initialize progress bars
    initializeProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar[data-progress]');
        progressBars.forEach(bar => {
            const targetProgress = parseInt(bar.dataset.progress);
            this.animateProgressBar(bar, targetProgress);
        });
    }

    // Animate progress bar
    animateProgressBar(bar, targetProgress) {
        let currentProgress = 0;
        const increment = targetProgress / 100;
        
        const animate = () => {
            currentProgress += increment;
            if (currentProgress >= targetProgress) {
                currentProgress = targetProgress;
            }
            
            bar.style.width = currentProgress + '%';
            bar.setAttribute('aria-valuenow', currentProgress);
            
            if (currentProgress < targetProgress) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    // Notification system
    showNotification(message, type = 'info', priority = 'normal') {
        const notification = this.createNotification(message, type, priority);
        const container = document.getElementById('notificationContainer');
        
        if (container) {
            container.appendChild(notification);
            
            // Auto-remove after delay
            const delay = priority === 'high' ? 8000 : 5000;
            setTimeout(() => {
                this.closeNotification(notification);
            }, delay);
        }
    }

    // Create notification
    createNotification(message, type, priority) {
        const notification = document.createElement('div');
        notification.className = `notification alert alert-${type} alert-dismissible fade show`;
        notification.setAttribute('role', 'alert');
        
        if (priority === 'high') {
            notification.classList.add('notification-high-priority');
        }
        
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas ${this.getNotificationIcon(type)} me-2"></i>
                <div class="flex-grow-1">${message}</div>
                <button type="button" class="btn-close notification-close" aria-label="Close"></button>
            </div>
        `;
        
        return notification;
    }

    // Get notification icon
    getNotificationIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            danger: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    // Close notification
    closeNotification(notification) {
        if (notification) {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }
    }

    // Connection status
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.className = connected ? 'status-online' : 'status-offline';
            statusElement.innerHTML = connected ? 
                '<i class="fas fa-circle"></i> Online' : 
                '<i class="fas fa-circle"></i> Offline';
        }
    }

    // Theme toggle
    toggleTheme() {
        const body = document.body;
        const isDark = body.classList.contains('dark-theme');
        
        if (isDark) {
            body.classList.remove('dark-theme');
            localStorage.setItem('theme', 'light');
        } else {
            body.classList.add('dark-theme');
            localStorage.setItem('theme', 'dark');
        }
    }

    // Global search
    openGlobalSearch() {
        const searchModal = document.getElementById('globalSearchModal');
        if (searchModal) {
            const modal = new bootstrap.Modal(searchModal);
            modal.show();
            
            // Focus on search input
            setTimeout(() => {
                const searchInput = searchModal.querySelector('input[type="search"]');
                if (searchInput) {
                    searchInput.focus();
                }
            }, 300);
        }
    }

    // Perform global search
    async performGlobalSearch(query) {
        if (!query.trim()) return;

        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const results = await response.json();
            this.displaySearchResults(results);
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    // Display search results
    displaySearchResults(results) {
        const resultsContainer = document.getElementById('searchResults');
        if (!resultsContainer) return;

        resultsContainer.innerHTML = '';

        if (results.length === 0) {
            resultsContainer.innerHTML = '<p class="text-muted">No results found</p>';
            return;
        }

        results.forEach(result => {
            const resultElement = document.createElement('div');
            resultElement.className = 'search-result p-3 border-bottom';
            resultElement.innerHTML = `
                <h6><a href="${result.url}" class="text-decoration-none">${result.title}</a></h6>
                <p class="text-muted mb-1">${result.description}</p>
                <small class="text-muted">${result.type}</small>
            `;
            resultsContainer.appendChild(resultElement);
        });
    }

    // Command palette
    openCommandPalette() {
        const commandModal = document.getElementById('commandPaletteModal');
        if (commandModal) {
            const modal = new bootstrap.Modal(commandModal);
            modal.show();
        }
    }

    // Create new chat
    createNewChat() {
        window.location.href = '/chat';
    }

    // Auto-save
    autoSave(element) {
        const data = {
            field: element.name,
            value: element.value,
            timestamp: new Date().toISOString()
        };

        fetch('/api/autosave', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        }).catch(error => {
            console.error('Auto-save error:', error);
        });
    }

    // Utility functions
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Event emitter
    emit(event, data) {
        const customEvent = new CustomEvent(event, { detail: data });
        document.dispatchEvent(customEvent);
    }

    // API helper
    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const mergedOptions = { ...defaultOptions, ...options };

        try {
            const response = await fetch(endpoint, mergedOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call error:', error);
            throw error;
        }
    }

    // Format date
    formatDate(date, format = 'short') {
        const d = new Date(date);
        
        if (format === 'short') {
            return d.toLocaleDateString();
        } else if (format === 'long') {
            return d.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } else if (format === 'relative') {
            return this.getRelativeTime(d);
        }
        
        return d.toLocaleDateString();
    }

    // Get relative time
    getRelativeTime(date) {
        const now = new Date();
        const diff = now - date;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) {
            return `${days} day${days > 1 ? 's' : ''} ago`;
        } else if (hours > 0) {
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else if (minutes > 0) {
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else {
            return 'Just now';
        }
    }

    // Escape HTML
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    // Generate UUID
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    // Copy to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showNotification('Copied to clipboard', 'success');
        } catch (error) {
            console.error('Copy error:', error);
            this.showNotification('Failed to copy to clipboard', 'danger');
        }
    }

    // Download file
    downloadFile(url, filename) {
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    // Get file size
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Validate email
    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    // Validate URL
    validateUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    // Storage helpers
    setStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Storage error:', error);
        }
    }

    getStorage(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Storage error:', error);
            return null;
        }
    }

    removeStorage(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('Storage error:', error);
        }
    }
}

// Initialize Autogent Studio
document.addEventListener('DOMContentLoaded', function() {
    window.autogentStudio = new AutogentStudio();
    
    // Apply saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
});

// Global utility functions
function showNotification(message, type = 'info', priority = 'normal') {
    if (window.autogentStudio) {
        window.autogentStudio.showNotification(message, type, priority);
    }
}

function formatDate(date, format = 'short') {
    if (window.autogentStudio) {
        return window.autogentStudio.formatDate(date, format);
    }
    return new Date(date).toLocaleDateString();
}

function copyToClipboard(text) {
    if (window.autogentStudio) {
        window.autogentStudio.copyToClipboard(text);
    }
}

function downloadFile(url, filename) {
    if (window.autogentStudio) {
        window.autogentStudio.downloadFile(url, filename);
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AutogentStudio;
}
