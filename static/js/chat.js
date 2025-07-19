// Autogent Studio Chat Interface

class AutogentChat {
    constructor() {
        this.messageContainer = document.querySelector('.as-chat-messages');
        this.messageForm = document.querySelector('.as-chat-form');
        this.messageInput = document.querySelector('.as-chat-textarea');
        this.sendButton = document.querySelector('.send-button');
        this.sessionId = this.getSessionId();
        this.isTyping = false;
        this.messageHistory = [];
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadChatHistory();
        this.initAutoResize();
        this.initModelSelector();
        this.focusInput();
    }

    bindEvents() {
        if (this.messageForm) {
            this.messageForm.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        if (this.messageInput) {
            this.messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
            this.messageInput.addEventListener('input', () => this.handleTyping());
        }

        // File attachment
        const attachButton = document.querySelector('.attach-button');
        if (attachButton) {
            attachButton.addEventListener('click', () => this.handleFileAttach());
        }

        // Model selector
        const modelSelector = document.querySelector('.model-selector');
        if (modelSelector) {
            modelSelector.addEventListener('change', (e) => this.changeModel(e.target.value));
        }

        // Clear chat
        const clearButton = document.querySelector('.clear-chat');
        if (clearButton) {
            clearButton.addEventListener('click', () => this.clearChat());
        }

        // Export chat
        const exportButton = document.querySelector('.export-chat');
        if (exportButton) {
            exportButton.addEventListener('click', () => this.exportChat());
        }
    }

    getSessionId() {
        const path = window.location.pathname;
        const match = path.match(/\/chat\/(\d+)/);
        return match ? match[1] : null;
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        const message = this.messageInput.value.trim();
        if (!message || this.isTyping) return;

        this.addMessage('user', message);
        this.messageInput.value = '';
        this.resizeTextarea();
        this.setTyping(true);

        try {
            const response = await fetch('/api/chat/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: message
                })
            });

            const data = await response.json();

            if (data.success) {
                this.addMessage('assistant', data.response, data.metadata);
            } else {
                this.addMessage('assistant', 'I apologize, but I encountered an error. Please try again.', { error: true });
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.addMessage('assistant', 'I apologize, but I encountered a connection error. Please try again.', { error: true });
        } finally {
            this.setTyping(false);
        }
    }

    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.handleSubmit(e);
        }
    }

    handleTyping() {
        this.resizeTextarea();
        
        // Send typing indicator to other users via socket
        if (window.autogentStudio.socket && this.sessionId) {
            window.autogentStudio.socket.emit('typing', {
                session_id: this.sessionId
            });
        }
    }

    addMessage(role, content, metadata = {}) {
        const messageElement = this.createMessageElement(role, content, metadata);
        this.messageContainer.appendChild(messageElement);
        this.scrollToBottom();
        
        // Add to message history
        this.messageHistory.push({ role, content, metadata, timestamp: new Date() });
        
        // Update session title if this is the first user message
        if (role === 'user' && this.messageHistory.filter(m => m.role === 'user').length === 1) {
            this.updateSessionTitle(content);
        }
    }

    createMessageElement(role, content, metadata = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `as-message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'as-message-avatar';
        
        if (role === 'user') {
            avatar.innerHTML = '<i class="fas fa-user"></i>';
        } else {
            avatar.innerHTML = '<i class="fas fa-robot"></i>';
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'as-message-content';
        
        // Process markdown and code blocks
        const processedContent = this.processMessageContent(content);
        contentDiv.innerHTML = processedContent;
        
        // Add metadata if present
        if (metadata.model) {
            const metaDiv = document.createElement('div');
            metaDiv.className = 'message-metadata';
            metaDiv.innerHTML = `
                <small class="text-muted">
                    <i class="fas fa-brain"></i> ${metadata.model}
                    ${metadata.usage ? `• ${metadata.usage.total_tokens} tokens` : ''}
                </small>
            `;
            contentDiv.appendChild(metaDiv);
        }
        
        // Add copy button
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button as-btn as-btn-sm';
        copyButton.innerHTML = '<i class="fas fa-copy"></i>';
        copyButton.title = 'Copy message';
        copyButton.onclick = () => this.copyMessage(content);
        contentDiv.appendChild(copyButton);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        
        // Add fade-in animation
        messageDiv.classList.add('as-fade-in');
        
        return messageDiv;
    }

    processMessageContent(content) {
        // Convert markdown to HTML (simplified)
        let processed = content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');

        // Process code blocks
        processed = processed.replace(/```(\w+)?\n([\s\S]*?)\n```/g, (match, language, code) => {
            const lang = language || 'text';
            return `
                <div class="code-block">
                    <div class="code-header">
                        <span class="code-language">${lang}</span>
                        <button class="copy-code as-btn as-btn-sm" onclick="autogentChat.copyCode(this)">
                            <i class="fas fa-copy"></i> Copy
                        </button>
                    </div>
                    <pre><code class="language-${lang}">${code.trim()}</code></pre>
                </div>
            `;
        });

        return processed;
    }

    copyMessage(content) {
        navigator.clipboard.writeText(content).then(() => {
            window.autogentStudio.showNotification('Message copied to clipboard', 'success');
        });
    }

    copyCode(button) {
        const codeBlock = button.closest('.code-block');
        const code = codeBlock.querySelector('code').textContent;
        navigator.clipboard.writeText(code).then(() => {
            window.autogentStudio.showNotification('Code copied to clipboard', 'success');
        });
    }

    setTyping(typing) {
        this.isTyping = typing;
        
        if (typing) {
            this.sendButton.disabled = true;
            this.sendButton.innerHTML = '<span class="as-loading"></span>';
            this.showTypingIndicator();
        } else {
            this.sendButton.disabled = false;
            this.sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
            this.hideTypingIndicator();
        }
    }

    showTypingIndicator() {
        // Remove existing typing indicator
        this.hideTypingIndicator();
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'as-message assistant typing-indicator';
        typingDiv.innerHTML = `
            <div class="as-message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="as-message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        this.messageContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = this.messageContainer.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    scrollToBottom() {
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }

    resizeTextarea() {
        if (this.messageInput) {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 150) + 'px';
        }
    }

    initAutoResize() {
        if (this.messageInput) {
            this.resizeTextarea();
        }
    }

    focusInput() {
        if (this.messageInput) {
            this.messageInput.focus();
        }
    }

    async loadChatHistory() {
        if (!this.sessionId) return;

        try {
            const response = await fetch(`/api/chat/${this.sessionId}/messages`);
            const data = await response.json();

            if (data.success && data.messages) {
                data.messages.forEach(message => {
                    this.addMessage(message.role, message.content, message.metadata || {});
                });
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }

    async updateSessionTitle(firstMessage) {
        if (!this.sessionId) return;

        try {
            const title = firstMessage.length > 50 ? firstMessage.substring(0, 50) + '...' : firstMessage;
            
            await fetch(`/api/chat/${this.sessionId}/title`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title })
            });
            
            // Update page title
            document.title = `${title} - Autogent Studio`;
            
        } catch (error) {
            console.error('Failed to update session title:', error);
        }
    }

    async changeModel(modelName) {
        if (!this.sessionId) return;

        try {
            await fetch(`/api/chat/${this.sessionId}/model`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ model: modelName })
            });
            
            window.autogentStudio.showNotification(`Model changed to ${modelName}`, 'success');
        } catch (error) {
            window.autogentStudio.showNotification('Failed to change model', 'error');
        }
    }

    async clearChat() {
        if (!confirm('Are you sure you want to clear this chat? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/chat/${this.sessionId}/clear`, {
                method: 'POST'
            });

            if (response.ok) {
                this.messageContainer.innerHTML = '';
                this.messageHistory = [];
                window.autogentStudio.showNotification('Chat cleared successfully', 'success');
            }
        } catch (error) {
            window.autogentStudio.showNotification('Failed to clear chat', 'error');
        }
    }

    exportChat() {
        const chatData = {
            session_id: this.sessionId,
            messages: this.messageHistory,
            exported_at: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `autogent-chat-${this.sessionId}-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        window.autogentStudio.showNotification('Chat exported successfully', 'success');
    }

    handleFileAttach() {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.accept = '.txt,.pdf,.doc,.docx,.md,.json';
        
        input.onchange = async (e) => {
            const files = Array.from(e.target.files);
            
            for (const file of files) {
                try {
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('session_id', this.sessionId);
                    
                    const response = await fetch('/api/chat/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        this.addMessage('system', `📎 Attached file: ${file.name}`);
                        window.autogentStudio.showNotification(`File ${file.name} attached successfully`, 'success');
                    } else {
                        throw new Error('Upload failed');
                    }
                } catch (error) {
                    window.autogentStudio.showNotification(`Failed to attach ${file.name}`, 'error');
                }
            }
        };
        
        input.click();
    }

    initModelSelector() {
        const modelSelector = document.querySelector('.model-selector');
        if (modelSelector) {
            // Load available models
            this.loadAvailableModels();
        }
    }

    async loadAvailableModels() {
        try {
            const response = await fetch('/api/models/available');
            const data = await response.json();
            
            const modelSelector = document.querySelector('.model-selector');
            if (modelSelector && data.success) {
                modelSelector.innerHTML = '';
                
                Object.entries(data.models).forEach(([provider, models]) => {
                    const optgroup = document.createElement('optgroup');
                    optgroup.label = provider.toUpperCase();
                    
                    models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model;
                        option.textContent = model;
                        optgroup.appendChild(option);
                    });
                    
                    modelSelector.appendChild(optgroup);
                });
            }
        } catch (error) {
            console.error('Failed to load available models:', error);
        }
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.as-chat-container')) {
        window.autogentChat = new AutogentChat();
    }
});
