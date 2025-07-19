// Autogent Studio - WebSocket Module
// Real-time communication for chat, collaboration, and system updates

class WebSocketService extends BaseModule {
    constructor(app) {
        super(app);
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.messageHandlers = new Map();
        this.connectionStatus = 'disconnected';
        this.heartbeatInterval = null;
        this.init();
    }
    
    init() {
        super.init();
        this.initializeSocketIO();
        this.setupConnectionHandlers();
        this.setupStatusIndicator();
    }
    
    initializeSocketIO() {
        // Initialize Socket.IO connection
        try {
            this.socket = io(this.app.config.websocketUrl, {
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true,
                autoConnect: true,
                reconnection: true,
                reconnectionAttempts: this.maxReconnectAttempts,
                reconnectionDelay: this.reconnectDelay,
                timeout: 20000
            });
            
            this.setupSocketEvents();
            
        } catch (error) {
            console.error('Failed to initialize WebSocket connection:', error);
            this.handleConnectionError(error);
        }
    }
    
    setupSocketEvents() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('🔗 WebSocket connected');
            this.connectionStatus = 'connected';
            this.reconnectAttempts = 0;
            this.updateConnectionStatus();
            this.startHeartbeat();
            this.onConnected();
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('🔌 WebSocket disconnected:', reason);
            this.connectionStatus = 'disconnected';
            this.updateConnectionStatus();
            this.stopHeartbeat();
            this.onDisconnected(reason);
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.connectionStatus = 'error';
            this.updateConnectionStatus();
            this.handleConnectionError(error);
        });
        
        this.socket.on('reconnect', (attemptNumber) => {
            console.log('🔄 WebSocket reconnected after', attemptNumber, 'attempts');
            this.connectionStatus = 'connected';
            this.updateConnectionStatus();
        });
        
        this.socket.on('reconnect_attempt', (attemptNumber) => {
            console.log('🔄 WebSocket reconnection attempt', attemptNumber);
            this.connectionStatus = 'reconnecting';
            this.updateConnectionStatus();
        });
        
        this.socket.on('reconnect_failed', () => {
            console.error('❌ WebSocket reconnection failed');
            this.connectionStatus = 'failed';
            this.updateConnectionStatus();
            this.app.showNotification('Connection lost. Please refresh the page.', 'error', 10000);
        });
        
        // Custom application events
        this.setupApplicationEvents();
    }
    
    setupApplicationEvents() {
        // Chat events
        this.socket.on('new_message', (data) => {
            this.handleMessage('new_message', data);
        });
        
        this.socket.on('user_typing', (data) => {
            this.handleMessage('user_typing', data);
        });
        
        // Workflow orchestration events
        this.socket.on('workflow_updated', (data) => {
            this.handleMessage('workflow_updated', data);
        });
        
        this.socket.on('workflow_execution_status', (data) => {
            this.handleMessage('workflow_execution_status', data);
        });
        
        // Quantum computing events
        this.socket.on('quantum_circuit_updated', (data) => {
            this.handleMessage('quantum_circuit_updated', data);
        });
        
        this.socket.on('quantum_execution_complete', (data) => {
            this.handleMessage('quantum_execution_complete', data);
        });
        
        // Federated learning events
        this.socket.on('training_status_updated', (data) => {
            this.handleMessage('training_status_updated', data);
        });
        
        this.socket.on('federated_node_status', (data) => {
            this.handleMessage('federated_node_status', data);
        });
        
        // Neuromorphic computing events
        this.socket.on('spike_data_received', (data) => {
            this.handleMessage('spike_data_received', data);
        });
        
        this.socket.on('neuromorphic_device_status', (data) => {
            this.handleMessage('neuromorphic_device_status', data);
        });
        
        // AI safety events
        this.socket.on('safety_alert_broadcast', (data) => {
            this.handleMessage('safety_alert_broadcast', data);
            this.handleSafetyAlert(data);
        });
        
        this.socket.on('alignment_test_result', (data) => {
            this.handleMessage('alignment_test_result', data);
        });
        
        // Self-improving AI events
        this.socket.on('research_progress_updated', (data) => {
            this.handleMessage('research_progress_updated', data);
        });
        
        this.socket.on('discovery_made', (data) => {
            this.handleMessage('discovery_made', data);
            this.handleDiscoveryNotification(data);
        });
        
        // Blockchain events
        this.socket.on('transaction_confirmed', (data) => {
            this.handleMessage('transaction_confirmed', data);
        });
        
        this.socket.on('nft_minted', (data) => {
            this.handleMessage('nft_minted', data);
        });
        
        // System events
        this.socket.on('system_message', (data) => {
            this.handleSystemMessage(data);
        });
        
        this.socket.on('notification', (data) => {
            this.handleNotification(data);
        });
        
        // File processing events
        this.socket.on('file_processed', (data) => {
            this.handleMessage('file_processed', data);
        });
        
        this.socket.on('knowledge_base_updated', (data) => {
            this.handleMessage('knowledge_base_updated', data);
        });
    }
    
    setupConnectionHandlers() {
        // Handle authentication after connection
        this.onMessage('connected', (data) => {
            if (this.app.state.authenticated) {
                this.authenticateConnection();
            }
        });
    }
    
    setupStatusIndicator() {
        // Create connection status indicator
        const statusIndicator = document.createElement('div');
        statusIndicator.className = 'as-connection-status';
        statusIndicator.innerHTML = `
            <div class="as-status-dot"></div>
            <span class="as-status-text">Connecting...</span>
        `;
        
        // Add to header or sidebar
        const header = document.querySelector('.as-header');
        if (header) {
            header.appendChild(statusIndicator);
        }
        
        this.statusIndicator = statusIndicator;
    }
    
    updateConnectionStatus() {
        if (!this.statusIndicator) return;
        
        const dot = this.statusIndicator.querySelector('.as-status-dot');
        const text = this.statusIndicator.querySelector('.as-status-text');
        
        switch (this.connectionStatus) {
            case 'connected':
                dot.className = 'as-status-dot as-status-connected';
                text.textContent = 'Connected';
                break;
            case 'disconnected':
                dot.className = 'as-status-dot as-status-disconnected';
                text.textContent = 'Disconnected';
                break;
            case 'reconnecting':
                dot.className = 'as-status-dot as-status-reconnecting';
                text.textContent = 'Reconnecting...';
                break;
            case 'error':
                dot.className = 'as-status-dot as-status-error';
                text.textContent = 'Connection Error';
                break;
            case 'failed':
                dot.className = 'as-status-dot as-status-failed';
                text.textContent = 'Connection Failed';
                break;
        }
    }
    
    // Public API methods
    emit(event, data) {
        if (this.socket && this.socket.connected) {
            this.socket.emit(event, data);
        } else {
            console.warn('Cannot emit event: WebSocket not connected');
        }
    }
    
    onMessage(event, handler) {
        if (!this.messageHandlers.has(event)) {
            this.messageHandlers.set(event, []);
        }
        this.messageHandlers.get(event).push(handler);
    }
    
    offMessage(event, handler) {
        if (this.messageHandlers.has(event)) {
            const handlers = this.messageHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }
    
    handleMessage(event, data) {
        if (this.messageHandlers.has(event)) {
            this.messageHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in message handler for ${event}:`, error);
                }
            });
        }
    }
    
    // Room management
    joinRoom(roomId) {
        this.emit('join_room', { room_id: roomId });
    }
    
    leaveRoom(roomId) {
        this.emit('leave_room', { room_id: roomId });
    }
    
    joinChatRoom(roomId) {
        this.emit('join_chat_room', { room_id: roomId });
    }
    
    leaveChatRoom(roomId) {
        this.emit('leave_chat_room', { room_id: roomId });
    }
    
    // Chat-specific methods
    sendChatMessage(roomId, message) {
        this.emit('send_message', {
            room_id: roomId,
            message: message,
            timestamp: new Date().toISOString()
        });
    }
    
    startTyping(roomId) {
        this.emit('typing_start', { room_id: roomId });
    }
    
    stopTyping(roomId) {
        this.emit('typing_stop', { room_id: roomId });
    }
    
    // Workflow orchestration methods
    updateWorkflow(workflowId, data) {
        this.emit('workflow_update', {
            workflow_id: workflowId,
            data: data,
            timestamp: new Date().toISOString()
        });
    }
    
    executeWorkflow(workflowId) {
        this.emit('execute_workflow', {
            workflow_id: workflowId,
            timestamp: new Date().toISOString()
        });
    }
    
    // Quantum computing methods
    updateQuantumCircuit(circuitId, circuitData) {
        this.emit('quantum_circuit_update', {
            circuit_id: circuitId,
            circuit_data: circuitData,
            timestamp: new Date().toISOString()
        });
    }
    
    executeQuantumCircuit(circuitId, parameters) {
        this.emit('execute_quantum_circuit', {
            circuit_id: circuitId,
            parameters: parameters,
            timestamp: new Date().toISOString()
        });
    }
    
    // Federated learning methods
    updateTrainingStatus(trainingId, status, progress) {
        this.emit('federated_training_status', {
            training_id: trainingId,
            status: status,
            progress: progress,
            timestamp: new Date().toISOString()
        });
    }
    
    registerFederatedNode(nodeId, nodeInfo) {
        this.emit('register_federated_node', {
            node_id: nodeId,
            node_info: nodeInfo,
            timestamp: new Date().toISOString()
        });
    }
    
    // Neuromorphic computing methods
    sendSpikeData(deviceId, spikeData) {
        this.emit('neuromorphic_spike_data', {
            device_id: deviceId,
            spike_data: spikeData,
            timestamp: new Date().toISOString()
        });
    }
    
    updateNeuromorphicDevice(deviceId, status) {
        this.emit('neuromorphic_device_update', {
            device_id: deviceId,
            status: status,
            timestamp: new Date().toISOString()
        });
    }
    
    // AI safety methods
    reportSafetyAlert(alertType, severity, message) {
        this.emit('safety_alert', {
            alert_type: alertType,
            severity: severity,
            message: message,
            timestamp: new Date().toISOString()
        });
    }
    
    requestAlignmentTest(modelId, testType) {
        this.emit('request_alignment_test', {
            model_id: modelId,
            test_type: testType,
            timestamp: new Date().toISOString()
        });
    }
    
    // Research and discovery methods
    updateResearchProgress(projectId, progress, discovery) {
        this.emit('research_progress', {
            project_id: projectId,
            progress: progress,
            discovery: discovery,
            timestamp: new Date().toISOString()
        });
    }
    
    reportDiscovery(projectId, discovery) {
        this.emit('report_discovery', {
            project_id: projectId,
            discovery: discovery,
            timestamp: new Date().toISOString()
        });
    }
    
    // Blockchain methods
    broadcastTransaction(transactionData) {
        this.emit('blockchain_transaction', {
            transaction_data: transactionData,
            timestamp: new Date().toISOString()
        });
    }
    
    mintNFT(nftData) {
        this.emit('mint_nft', {
            nft_data: nftData,
            timestamp: new Date().toISOString()
        });
    }
    
    // Event handlers
    onConnected() {
        this.app.showNotification('Connected to Autogent Studio', 'success', 3000);
        
        // Restore user sessions and subscriptions
        if (this.app.state.authenticated) {
            this.authenticateConnection();
        }
    }
    
    onDisconnected(reason) {
        if (reason === 'io server disconnect') {
            // Server initiated disconnect
            this.app.showNotification('Server disconnected. Reconnecting...', 'warning', 5000);
        }
    }
    
    authenticateConnection() {
        this.emit('authenticate', {
            user_id: this.app.state.user?.id,
            session_token: localStorage.getItem('session_token')
        });
    }
    
    handleConnectionError(error) {
        console.error('WebSocket connection error:', error);
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                this.socket.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        }
    }
    
    handleSystemMessage(data) {
        this.app.showNotification(data.message, 'info', 5000);
    }
    
    handleNotification(data) {
        this.app.showNotification(data.message, data.type || 'info', 5000);
    }
    
    handleSafetyAlert(data) {
        const severityIcon = {
            low: '⚠️',
            medium: '🚨',
            high: '🔴',
            critical: '💀'
        };
        
        const icon = severityIcon[data.severity] || '⚠️';
        this.app.showNotification(
            `${icon} Safety Alert: ${data.message}`,
            'error',
            10000
        );
        
        // Update safety dashboard if visible
        const safetyModule = this.app.getModule('safety');
        if (safetyModule) {
            safetyModule.handleSafetyAlert(data);
        }
    }
    
    handleDiscoveryNotification(data) {
        this.app.showNotification(
            `🔬 New Discovery: ${data.discovery?.title || 'Research breakthrough'}`,
            'success',
            8000
        );
        
        // Update research dashboard if visible
        const researchModule = this.app.getModule('selfImproving');
        if (researchModule) {
            researchModule.handleDiscovery(data);
        }
    }
    
    // Heartbeat to keep connection alive
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.socket && this.socket.connected) {
                this.emit('heartbeat', { timestamp: new Date().toISOString() });
            }
        }, 30000); // Every 30 seconds
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    // Connection info
    getConnectionInfo() {
        return {
            status: this.connectionStatus,
            reconnectAttempts: this.reconnectAttempts,
            connected: this.socket ? this.socket.connected : false,
            transport: this.socket ? this.socket.io.engine.transport.name : null
        };
    }
    
    // Cleanup
    destroy() {
        super.destroy();
        
        this.stopHeartbeat();
        
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        
        if (this.statusIndicator && this.statusIndicator.parentNode) {
            this.statusIndicator.parentNode.removeChild(this.statusIndicator);
        }
        
        this.messageHandlers.clear();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketService;
}
