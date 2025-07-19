/**
 * Autogent Studio - Main JavaScript Module
 * Enterprise-grade AI development platform
 */

class AutogentStudio {
    constructor() {
        this.sidebarCollapsed = false;
        this.currentUser = null;
        this.socket = null;
        this.notifications = [];
        this.darkMode = true;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeUI();
        this.loadUserPreferences();
        this.initializeWebSocket();
        this.startPerformanceMonitoring();
        
        console.log('🚀 Autogent Studio initialized');
    }
    
    setupEventListeners() {
        // Sidebar toggle
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-toggle="sidebar"]')) {
                this.toggleSidebar();
            }
        });
        
        // Modal handlers
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-toggle="modal"]')) {
                const target = e.target.dataset.target;
                this.showModal(target);
            }
            
            if (e.target.matches('.modal-overlay, .modal-close')) {
                this.hideModal();
            }
        });
        
        // Form handlers
        document.addEventListener('submit', (e) => {
            if (e.target.matches('.ajax-form')) {
                e.preventDefault();
                this.handleAjaxForm(e.target);
            }
        });
        
        // File upload handlers
        document.addEventListener('change', (e) => {
            if (e.target.matches('.file-input')) {
                this.handleFileSelect(e.target);
            }
        });
        
        // Drag and drop
        document.addEventListener('dragover', (e) => {
            if (e.target.matches('.file-upload-zone')) {
                e.preventDefault();
                e.target.classList.add('dragover');
            }
        });
        
        document.addEventListener('dragleave', (e) => {
            if (e.target.matches('.file-upload-zone')) {
                e.target.classList.remove('dragover');
            }
        });
        
        document.addEventListener('drop', (e) => {
            if (e.target.matches('.file-upload-zone')) {
                e.preventDefault();
                e.target.classList.remove('dragover');
                this.handleFileDrop(e.target, e.dataTransfer.files);
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
        
        // Real-time updates
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseRealTimeUpdates();
            } else {
                this.resumeRealTimeUpdates();
            }
        });
    }
    
    initializeUI() {
        // Set active navigation item
        this.updateActiveNavigation();
        
        // Initialize tooltips
        this.initializeTooltips();
        
        // Initialize progress bars
        this.animateProgressBars();
        
        // Initialize charts if present
        this.initializeCharts();
        
        // Initialize code editors
        this.initializeCodeEditors();
        
        // Initialize real-time components
        this.initializeRealTimeComponents();
    }
    
    updateActiveNavigation() {
        const currentPath = window.location.pathname;
        const navItems = document.querySelectorAll('.nav-item');
        
        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('href') === currentPath) {
                item.classList.add('active');
            }
        });
    }
    
    toggleSidebar() {
        const sidebar = document.querySelector('.autogent-sidebar');
        const main = document.querySelector('.autogent-main');
        
        if (this.sidebarCollapsed) {
            sidebar.classList.remove('collapsed');
            main.classList.remove('expanded');
            this.sidebarCollapsed = false;
        } else {
            sidebar.classList.add('collapsed');
            main.classList.add('expanded');
            this.sidebarCollapsed = true;
        }
        
        // Save preference
        localStorage.setItem('autogent_sidebar_collapsed', this.sidebarCollapsed);
    }
    
    showModal(modalId) {
        const modal = document.querySelector(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            
            // Focus first input
            const firstInput = modal.querySelector('input, textarea, select');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
        }
    }
    
    hideModal() {
        const activeModal = document.querySelector('.modal-overlay.active');
        if (activeModal) {
            activeModal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    async handleAjaxForm(form) {
        const formData = new FormData(form);
        const url = form.action || window.location.pathname;
        const method = form.method || 'POST';
        
        // Show loading state
        const submitBtn = form.querySelector('[type="submit"]');
        const originalText = submitBtn?.textContent;
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        }
        
        try {
            const response = await fetch(url, {
                method: method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Success!', result.message || 'Operation completed successfully', 'success');
                
                // Handle redirects
                if (result.redirect_url) {
                    window.location.href = result.redirect_url;
                    return;
                }
                
                // Reset form if specified
                if (form.dataset.reset === 'true') {
                    form.reset();
                }
                
                // Close modal if form is in modal
                const modal = form.closest('.modal-overlay');
                if (modal) {
                    this.hideModal();
                }
                
                // Trigger custom event
                const event = new CustomEvent('autogent:form-success', {
                    detail: { form, result }
                });
                document.dispatchEvent(event);
                
            } else {
                this.showNotification('Error', result.message || 'An error occurred', 'error');
                
                // Show field errors
                this.showFieldErrors(form, result.errors || {});
            }
            
        } catch (error) {
            console.error('Form submission error:', error);
            this.showNotification('Error', 'Network error occurred', 'error');
        } finally {
            // Restore button state
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        }
    }
    
    showFieldErrors(form, errors) {
        // Clear existing errors
        form.querySelectorAll('.form-error').forEach(el => el.remove());
        
        // Show new errors
        Object.entries(errors).forEach(([field, message]) => {
            const input = form.querySelector(`[name="${field}"]`);
            if (input) {
                const errorEl = document.createElement('div');
                errorEl.className = 'form-error';
                errorEl.textContent = message;
                input.parentNode.appendChild(errorEl);
            }
        });
    }
    
    handleFileSelect(input) {
        const files = Array.from(input.files);
        this.processFiles(files, input);
    }
    
    handleFileDrop(dropZone, files) {
        const fileArray = Array.from(files);
        const input = dropZone.querySelector('.file-input');
        this.processFiles(fileArray, input);
    }
    
    async processFiles(files, input) {
        if (files.length === 0) return;
        
        const container = input?.closest('.file-upload-container') || document.querySelector('.file-upload-container');
        
        for (const file of files) {
            if (!this.validateFile(file)) continue;
            
            const progressEl = this.createFileProgressElement(file);
            container?.appendChild(progressEl);
            
            try {
                await this.uploadFile(file, progressEl);
            } catch (error) {
                console.error('File upload error:', error);
                this.updateFileProgress(progressEl, 0, 'Upload failed', 'error');
            }
        }
    }
    
    validateFile(file) {
        const maxSize = 100 * 1024 * 1024; // 100MB
        const allowedTypes = [
            'text/plain', 'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'audio/mpeg', 'audio/wav', 'video/mp4', 'video/avi'
        ];
        
        if (file.size > maxSize) {
            this.showNotification('Error', `File "${file.name}" is too large (max 100MB)`, 'error');
            return false;
        }
        
        if (!allowedTypes.includes(file.type)) {
            this.showNotification('Error', `File type "${file.type}" is not supported`, 'error');
            return false;
        }
        
        return true;
    }
    
    createFileProgressElement(file) {
        const div = document.createElement('div');
        div.className = 'file-progress-item';
        div.innerHTML = `
            <div class="file-info">
                <i class="fas fa-file"></i>
                <span class="file-name">${file.name}</span>
                <span class="file-size">${this.formatFileSize(file.size)}</span>
            </div>
            <div class="progress">
                <div class="progress-bar" style="width: 0%"></div>
            </div>
            <div class="file-status">Uploading...</div>
        `;
        return div;
    }
    
    async uploadFile(file, progressEl) {
        const formData = new FormData();
        formData.append('files', file);
        
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentage = (e.loaded / e.total) * 100;
                    this.updateFileProgress(progressEl, percentage, 'Uploading...');
                }
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    try {
                        const result = JSON.parse(xhr.responseText);
                        if (result.success) {
                            this.updateFileProgress(progressEl, 100, 'Upload complete', 'success');
                            resolve(result);
                        } else {
                            reject(new Error(result.message || 'Upload failed'));
                        }
                    } catch (error) {
                        reject(new Error('Invalid response'));
                    }
                } else {
                    reject(new Error(`HTTP ${xhr.status}`));
                }
            });
            
            xhr.addEventListener('error', () => {
                reject(new Error('Network error'));
            });
            
            xhr.open('POST', '/files/upload');
            xhr.send(formData);
        });
    }
    
    updateFileProgress(progressEl, percentage, status, type = 'info') {
        const progressBar = progressEl.querySelector('.progress-bar');
        const statusEl = progressEl.querySelector('.file-status');
        
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
        }
        
        if (statusEl) {
            statusEl.textContent = status;
            statusEl.className = `file-status ${type}`;
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    showNotification(title, message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close">&times;</button>
        `;
        
        // Add to container
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        // Auto remove
        setTimeout(() => {
            notification.remove();
        }, duration);
        
        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
        
        // Add to notifications array
        this.notifications.push({
            id: Date.now(),
            title,
            message,
            type,
            timestamp: new Date()
        });
    }
    
    loadUserPreferences() {
        // Load sidebar state
        const sidebarCollapsed = localStorage.getItem('autogent_sidebar_collapsed');
        if (sidebarCollapsed === 'true') {
            this.toggleSidebar();
        }
        
        // Load theme preference
        const darkMode = localStorage.getItem('autogent_dark_mode');
        if (darkMode !== null) {
            this.darkMode = darkMode === 'true';
            this.applyTheme();
        }
        
        // Load other preferences
        this.loadEditorPreferences();
        this.loadDisplayPreferences();
    }
    
    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.darkMode ? 'dark' : 'light');
        localStorage.setItem('autogent_dark_mode', this.darkMode);
    }
    
    toggleTheme() {
        this.darkMode = !this.darkMode;
        this.applyTheme();
    }
    
    initializeWebSocket() {
        if (typeof io !== 'undefined') {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('🔌 WebSocket connected');
                this.updateConnectionStatus(true);
            });
            
            this.socket.on('disconnect', () => {
                console.log('🔌 WebSocket disconnected');
                this.updateConnectionStatus(false);
            });
            
            this.socket.on('notification', (data) => {
                this.showNotification(data.title, data.message, data.type);
            });
            
            this.socket.on('system_update', (data) => {
                this.handleSystemUpdate(data);
            });
        }
    }
    
    updateConnectionStatus(connected) {
        const indicator = document.querySelector('.connection-indicator');
        if (indicator) {
            indicator.className = `connection-indicator ${connected ? 'connected' : 'disconnected'}`;
            indicator.title = connected ? 'Connected' : 'Disconnected';
        }
    }
    
    handleSystemUpdate(data) {
        switch (data.type) {
            case 'workflow_complete':
                this.showNotification('Workflow Complete', data.message, 'success');
                break;
            case 'training_complete':
                this.showNotification('Training Complete', data.message, 'success');
                break;
            case 'error':
                this.showNotification('System Error', data.message, 'error');
                break;
            case 'maintenance':
                this.showNotification('Maintenance', data.message, 'warning');
                break;
        }
    }
    
    initializeTooltips() {
        document.querySelectorAll('[data-tooltip]').forEach(el => {
            el.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, e.target.dataset.tooltip);
            });
            
            el.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    }
    
    showTooltip(element, text) {
        let tooltip = document.querySelector('.tooltip');
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            document.body.appendChild(tooltip);
        }
        
        tooltip.textContent = text;
        tooltip.style.display = 'block';
        
        const rect = element.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        tooltip.style.left = `${rect.left + (rect.width - tooltipRect.width) / 2}px`;
        tooltip.style.top = `${rect.top - tooltipRect.height - 8}px`;
    }
    
    hideTooltip() {
        const tooltip = document.querySelector('.tooltip');
        if (tooltip) {
            tooltip.style.display = 'none';
        }
    }
    
    animateProgressBars() {
        document.querySelectorAll('.progress-bar').forEach(bar => {
            const width = bar.dataset.width || bar.style.width;
            if (width) {
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = width;
                }, 100);
            }
        });
    }
    
    initializeCharts() {
        // Initialize Chart.js charts if present
        if (typeof Chart !== 'undefined') {
            document.querySelectorAll('.chart-canvas').forEach(canvas => {
                this.createChart(canvas);
            });
        }
    }
    
    createChart(canvas) {
        const type = canvas.dataset.chartType || 'line';
        const data = JSON.parse(canvas.dataset.chartData || '{}');
        const options = JSON.parse(canvas.dataset.chartOptions || '{}');
        
        // Default dark theme options
        const defaultOptions = {
            responsive: true,
            plugins: {
                legend: {
                    labels: {
                        color: 'rgb(203, 213, 225)'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: 'rgb(100, 116, 139)'
                    },
                    grid: {
                        color: 'rgb(51, 65, 85)'
                    }
                },
                y: {
                    ticks: {
                        color: 'rgb(100, 116, 139)'
                    },
                    grid: {
                        color: 'rgb(51, 65, 85)'
                    }
                }
            }
        };
        
        const mergedOptions = this.deepMerge(defaultOptions, options);
        
        new Chart(canvas, {
            type: type,
            data: data,
            options: mergedOptions
        });
    }
    
    initializeCodeEditors() {
        // Initialize CodeMirror editors if present
        if (typeof CodeMirror !== 'undefined') {
            document.querySelectorAll('.code-editor').forEach(textarea => {
                this.createCodeEditor(textarea);
            });
        }
    }
    
    createCodeEditor(textarea) {
        const mode = textarea.dataset.mode || 'javascript';
        const theme = 'dracula'; // Dark theme
        
        const editor = CodeMirror.fromTextArea(textarea, {
            lineNumbers: true,
            mode: mode,
            theme: theme,
            autoCloseBrackets: true,
            matchBrackets: true,
            indentUnit: 2,
            tabSize: 2,
            indentWithTabs: false,
            styleActiveLine: true,
            foldGutter: true,
            gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter']
        });
        
        // Store reference
        textarea.codeMirror = editor;
        
        return editor;
    }
    
    initializeRealTimeComponents() {
        // Initialize real-time metrics
        this.startMetricsUpdates();
        
        // Initialize activity feeds
        this.startActivityFeed();
        
        // Initialize status indicators
        this.startStatusUpdates();
    }
    
    startMetricsUpdates() {
        // Update metrics every 30 seconds
        this.metricsInterval = setInterval(() => {
            this.updateMetrics();
        }, 30000);
    }
    
    async updateMetrics() {
        try {
            const response = await fetch('/api/analytics/usage');
            const data = await response.json();
            
            if (data.success) {
                this.updateMetricElements(data.analytics);
            }
        } catch (error) {
            console.error('Metrics update error:', error);
        }
    }
    
    updateMetricElements(metrics) {
        Object.entries(metrics).forEach(([key, value]) => {
            const element = document.querySelector(`[data-metric="${key}"]`);
            if (element) {
                element.textContent = value;
                element.classList.add('updated');
                setTimeout(() => element.classList.remove('updated'), 500);
            }
        });
    }
    
    startActivityFeed() {
        if (this.socket) {
            this.socket.on('activity', (activity) => {
                this.addActivityItem(activity);
            });
        }
    }
    
    addActivityItem(activity) {
        const feed = document.querySelector('.activity-feed');
        if (!feed) return;
        
        const item = document.createElement('div');
        item.className = 'activity-item';
        item.innerHTML = `
            <div class="activity-icon">
                <i class="fas fa-${activity.icon || 'info-circle'}"></i>
            </div>
            <div class="activity-content">
                <div class="activity-message">${activity.message}</div>
                <div class="activity-time">${this.formatTime(activity.timestamp)}</div>
            </div>
        `;
        
        feed.insertBefore(item, feed.firstChild);
        
        // Limit items
        const items = feed.querySelectorAll('.activity-item');
        if (items.length > 20) {
            items[items.length - 1].remove();
        }
    }
    
    startStatusUpdates() {
        // Update status indicators every 60 seconds
        this.statusInterval = setInterval(() => {
            this.updateSystemStatus();
        }, 60000);
    }
    
    async updateSystemStatus() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            this.updateStatusIndicators(data);
        } catch (error) {
            console.error('Status update error:', error);
            this.updateStatusIndicators({ status: 'error' });
        }
    }
    
    updateStatusIndicators(status) {
        const indicators = document.querySelectorAll('.status-indicator');
        indicators.forEach(indicator => {
            const service = indicator.dataset.service;
            const serviceStatus = status[service] || status.status;
            
            indicator.className = `status-indicator ${serviceStatus}`;
            indicator.textContent = serviceStatus.charAt(0).toUpperCase() + serviceStatus.slice(1);
        });
    }
    
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + K - Quick search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            this.openQuickSearch();
        }
        
        // Ctrl/Cmd + / - Toggle sidebar
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            this.toggleSidebar();
        }
        
        // Escape - Close modals
        if (e.key === 'Escape') {
            this.hideModal();
        }
        
        // Ctrl/Cmd + S - Save (prevent default)
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            this.triggerSave();
        }
    }
    
    openQuickSearch() {
        // Implementation for quick search modal
        this.showModal('#quick-search-modal');
    }
    
    triggerSave() {
        // Trigger save for current context
        const saveBtn = document.querySelector('.btn-save, [data-action="save"]');
        if (saveBtn) {
            saveBtn.click();
        }
    }
    
    startPerformanceMonitoring() {
        // Monitor page load performance
        window.addEventListener('load', () => {
            setTimeout(() => {
                this.logPerformanceMetrics();
            }, 0);
        });
    }
    
    logPerformanceMetrics() {
        if ('performance' in window) {
            const navigation = performance.getEntriesByType('navigation')[0];
            const paint = performance.getEntriesByType('paint');
            
            const metrics = {
                loadTime: navigation.loadEventEnd - navigation.fetchStart,
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
                firstPaint: paint.find(p => p.name === 'first-paint')?.startTime,
                firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime
            };
            
            console.log('📊 Performance Metrics:', metrics);
            
            // Send to analytics if needed
            this.sendAnalytics('performance', metrics);
        }
    }
    
    sendAnalytics(event, data) {
        // Send analytics data to backend
        if (navigator.sendBeacon) {
            navigator.sendBeacon('/api/analytics/events', JSON.stringify({
                event: event,
                data: data,
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                url: window.location.href
            }));
        }
    }
    
    pauseRealTimeUpdates() {
        clearInterval(this.metricsInterval);
        clearInterval(this.statusInterval);
    }
    
    resumeRealTimeUpdates() {
        this.startMetricsUpdates();
        this.startStatusUpdates();
    }
    
    loadEditorPreferences() {
        const prefs = JSON.parse(localStorage.getItem('autogent_editor_prefs') || '{}');
        
        // Apply editor preferences
        if (prefs.fontSize) {
            document.documentElement.style.setProperty('--editor-font-size', prefs.fontSize + 'px');
        }
        
        if (prefs.tabSize) {
            document.documentElement.style.setProperty('--editor-tab-size', prefs.tabSize);
        }
    }
    
    loadDisplayPreferences() {
        const prefs = JSON.parse(localStorage.getItem('autogent_display_prefs') || '{}');
        
        // Apply display preferences
        if (prefs.density) {
            document.documentElement.setAttribute('data-density', prefs.density);
        }
        
        if (prefs.animations === false) {
            document.documentElement.style.setProperty('--transition-normal', '0s');
            document.documentElement.style.setProperty('--transition-fast', '0s');
        }
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) { // Less than 1 minute
            return 'Just now';
        } else if (diff < 3600000) { // Less than 1 hour
            return `${Math.floor(diff / 60000)}m ago`;
        } else if (diff < 86400000) { // Less than 1 day
            return `${Math.floor(diff / 3600000)}h ago`;
        } else {
            return date.toLocaleDateString();
        }
    }
    
    deepMerge(target, source) {
        const result = { ...target };
        
        for (const key in source) {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                result[key] = this.deepMerge(result[key] || {}, source[key]);
            } else {
                result[key] = source[key];
            }
        }
        
        return result;
    }
    
    // Public API methods
    showLoading() {
        let loader = document.querySelector('.global-loader');
        if (!loader) {
            loader = document.createElement('div');
            loader.className = 'global-loader';
            loader.innerHTML = '<div class="spinner"></div>';
            document.body.appendChild(loader);
        }
        loader.style.display = 'flex';
    }
    
    hideLoading() {
        const loader = document.querySelector('.global-loader');
        if (loader) {
            loader.style.display = 'none';
        }
    }
    
    confirm(message, callback) {
        const confirmed = window.confirm(message);
        if (callback) {
            callback(confirmed);
        }
        return confirmed;
    }
    
    prompt(message, defaultValue, callback) {
        const result = window.prompt(message, defaultValue);
        if (callback) {
            callback(result);
        }
        return result;
    }
    
    refresh() {
        window.location.reload();
    }
    
    navigate(url) {
        window.location.href = url;
    }
    
    openInNewTab(url) {
        window.open(url, '_blank');
    }
    
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showNotification('Copied', 'Text copied to clipboard', 'success', 2000);
        }).catch(err => {
            console.error('Copy failed:', err);
            this.showNotification('Error', 'Failed to copy text', 'error');
        });
    }
    
    downloadFile(url, filename) {
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || '';
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
    
    // Cleanup
    destroy() {
        clearInterval(this.metricsInterval);
        clearInterval(this.statusInterval);
        
        if (this.socket) {
            this.socket.disconnect();
        }
        
        // Remove event listeners
        document.removeEventListener('click', this.handleClicks);
        document.removeEventListener('keydown', this.handleKeyboardShortcuts);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.autogent = new AutogentStudio();
});

// Add notification styles
const notificationStyles = `
.notification-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10000;
    pointer-events: none;
}

.notification {
    background: var(--bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: var(--space-md);
    margin-bottom: var(--space-sm);
    box-shadow: var(--shadow-xl);
    max-width: 400px;
    pointer-events: all;
    animation: slideIn 0.3s ease-out;
    display: flex;
    align-items: flex-start;
    gap: var(--space-sm);
}

.notification-success {
    border-left: 4px solid var(--autogent-success);
}

.notification-error {
    border-left: 4px solid var(--autogent-error);
}

.notification-warning {
    border-left: 4px solid var(--autogent-warning);
}

.notification-info {
    border-left: 4px solid var(--autogent-accent);
}

.notification-content {
    flex: 1;
}

.notification-title {
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--space-xs);
}

.notification-message {
    color: var(--text-secondary);
    font-size: 0.875rem;
}

.notification-close {
    background: none;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 0;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-sm);
}

.notification-close:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.tooltip {
    position: absolute;
    background: var(--bg-tertiary);
    color: var(--text-primary);
    padding: var(--space-xs) var(--space-sm);
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    border: 1px solid var(--border-primary);
    box-shadow: var(--shadow-lg);
    z-index: 10000;
    pointer-events: none;
    white-space: nowrap;
}

.global-loader {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(15, 15, 35, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    backdrop-filter: blur(4px);
}

.connection-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: var(--space-xs);
}

.connection-indicator.connected {
    background: var(--autogent-success);
}

.connection-indicator.disconnected {
    background: var(--autogent-error);
}

.status-indicator {
    padding: 0.125rem 0.375rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 500;
}

.status-indicator.healthy {
    background: rgb(16 185 129 / 0.2);
    color: var(--autogent-success);
}

.status-indicator.warning {
    background: rgb(245 158 11 / 0.2);
    color: var(--autogent-warning);
}

.status-indicator.error {
    background: rgb(239 68 68 / 0.2);
    color: var(--autogent-error);
}

.activity-feed {
    max-height: 400px;
    overflow-y: auto;
}

.activity-item {
    display: flex;
    gap: var(--space-sm);
    padding: var(--space-sm) 0;
    border-bottom: 1px solid var(--border-primary);
}

.activity-item:last-child {
    border-bottom: none;
}

.activity-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--autogent-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 0.875rem;
    flex-shrink: 0;
}

.activity-content {
    flex: 1;
}

.activity-message {
    color: var(--text-primary);
    font-size: 0.875rem;
    margin-bottom: var(--space-xs);
}

.activity-time {
    color: var(--text-muted);
    font-size: 0.75rem;
}

.file-progress-item {
    background: var(--bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--space-md);
    margin-bottom: var(--space-sm);
}

.file-info {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    margin-bottom: var(--space-sm);
}

.file-name {
    font-weight: 500;
    color: var(--text-primary);
}

.file-size {
    color: var(--text-muted);
    font-size: 0.875rem;
}

.file-status {
    margin-top: var(--space-sm);
    font-size: 0.875rem;
}

.file-status.success {
    color: var(--autogent-success);
}

.file-status.error {
    color: var(--autogent-error);
}

[data-metric].updated {
    animation: pulse 0.5s ease-in-out;
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);
