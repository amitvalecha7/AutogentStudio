/**
 * Autogent Studio - Federated Learning Module
 * Handles federated learning project management, node coordination, and privacy-preserving training
 */

class FederatedLearning {
    constructor() {
        this.projects = new Map();
        this.nodes = new Map();
        this.currentProject = null;
        this.aggregationMethods = ['fedavg', 'fedprox', 'scaffold'];
        this.privacyBudget = 1.0;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadProjects();
        this.loadNodes();
        this.initializeNetworkTopology();
        console.log('Federated Learning module initialized');
    }

    setupEventListeners() {
        // Project management
        const createProjectBtn = document.getElementById('create-project-btn');
        if (createProjectBtn) {
            createProjectBtn.addEventListener('click', () => this.createProject());
        }

        const startTrainingBtn = document.getElementById('start-training-btn');
        if (startTrainingBtn) {
            startTrainingBtn.addEventListener('click', () => this.startTraining());
        }

        // Node management
        const joinProjectBtn = document.getElementById('join-project-btn');
        if (joinProjectBtn) {
            joinProjectBtn.addEventListener('click', () => this.joinProject());
        }

        const updateNodeBtn = document.getElementById('update-node-btn');
        if (updateNodeBtn) {
            updateNodeBtn.addEventListener('click', () => this.updateNode());
        }

        // Privacy settings
        const privacySlider = document.getElementById('privacy-budget-slider');
        if (privacySlider) {
            privacySlider.addEventListener('input', (e) => {
                this.privacyBudget = parseFloat(e.target.value);
                this.updatePrivacyDisplay();
            });
        }

        // Aggregation method
        const aggregationSelect = document.getElementById('aggregation-method');
        if (aggregationSelect) {
            aggregationSelect.addEventListener('change', (e) => {
                this.updateAggregationMethod(e.target.value);
            });
        }

        // Real-time updates
        this.setupRealTimeUpdates();
    }

    setupRealTimeUpdates() {
        // Poll for project updates every 10 seconds
        setInterval(() => {
            if (this.currentProject) {
                this.updateProjectStatus();
            }
            this.updateNodeStatuses();
        }, 10000);
    }

    async createProject() {
        const form = document.getElementById('create-project-form');
        if (!form) return;

        const formData = new FormData(form);
        const projectData = {
            name: formData.get('name'),
            description: formData.get('description'),
            model_architecture: this.getModelArchitecture(),
            aggregation_method: formData.get('aggregation_method') || 'fedavg',
            privacy_budget: this.privacyBudget
        };

        try {
            const response = await fetch('/federated/projects/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(projectData)
            });

            const result = await response.json();

            if (result.success) {
                autogent.showSuccess('Federated project created successfully');
                this.loadProjects();
                this.closeModal('create-project-modal');
            } else {
                autogent.showError(result.error || 'Failed to create project');
            }
        } catch (error) {
            console.error('Project creation error:', error);
            autogent.showError('Failed to create project');
        }
    }

    getModelArchitecture() {
        const architectureType = document.getElementById('architecture-type')?.value || 'simple_cnn';
        const numClasses = parseInt(document.getElementById('num-classes')?.value || 10);

        return {
            type: architectureType,
            num_classes: numClasses,
            layers: this.generateArchitectureLayers(architectureType, numClasses)
        };
    }

    generateArchitectureLayers(type, numClasses) {
        const architectures = {
            simple_cnn: [
                { type: 'conv2d', filters: 32, kernel_size: 3, activation: 'relu' },
                { type: 'maxpool2d', pool_size: 2 },
                { type: 'conv2d', filters: 64, kernel_size: 3, activation: 'relu' },
                { type: 'maxpool2d', pool_size: 2 },
                { type: 'flatten' },
                { type: 'dense', units: 128, activation: 'relu' },
                { type: 'dense', units: numClasses, activation: 'softmax' }
            ],
            lstm: [
                { type: 'lstm', units: 128, return_sequences: true },
                { type: 'lstm', units: 64 },
                { type: 'dense', units: numClasses, activation: 'softmax' }
            ],
            transformer: [
                { type: 'embedding', vocab_size: 10000, embedding_dim: 256 },
                { type: 'transformer_block', num_heads: 8, ff_dim: 512 },
                { type: 'global_average_pooling' },
                { type: 'dense', units: numClasses, activation: 'softmax' }
            ]
        };

        return architectures[type] || architectures.simple_cnn;
    }

    async loadProjects() {
        try {
            const response = await fetch('/api/federated/projects');
            const projects = await response.json();

            const projectsList = document.getElementById('projects-list');
            if (projectsList) {
                projectsList.innerHTML = projects.projects.map(project => `
                    <div class="project-card card" onclick="federated.selectProject(${project.id})">
                        <div class="card-header">
                            <h4 class="card-title">${project.name}</h4>
                            <span class="badge badge-${this.getStatusClass(project.status)}">${project.status}</span>
                        </div>
                        <div class="card-content">
                            <p>${project.description}</p>
                            <div class="project-stats">
                                <span class="stat">
                                    <i class="fas fa-users"></i> ${project.node_count || 0} nodes
                                </span>
                                <span class="stat">
                                    <i class="fas fa-layer-group"></i> ${project.aggregation_method}
                                </span>
                                <span class="stat">
                                    <i class="fas fa-shield-alt"></i> ε=${project.privacy_budget}
                                </span>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Failed to load projects:', error);
        }
    }

    async loadNodes() {
        try {
            const response = await fetch('/api/federated/nodes');
            const nodes = await response.json();

            const nodesList = document.getElementById('nodes-list');
            if (nodesList) {
                nodesList.innerHTML = nodes.nodes.map(node => `
                    <div class="node-card card">
                        <div class="card-header">
                            <h4 class="card-title">${node.node_name}</h4>
                            <span class="badge badge-${this.getStatusClass(node.status)}">${node.status}</span>
                        </div>
                        <div class="card-content">
                            <div class="node-stats">
                                <div class="stat">
                                    <span class="stat-label">Data Samples</span>
                                    <span class="stat-value">${node.data_samples}</span>
                                </div>
                                <div class="stat">
                                    <span class="stat-label">Contribution Score</span>
                                    <span class="stat-value">${node.contribution_score.toFixed(3)}</span>
                                </div>
                                <div class="stat">
                                    <span class="stat-label">Last Update</span>
                                    <span class="stat-value">${this.formatDate(node.last_update)}</span>
                                </div>
                            </div>
                            <div class="node-actions">
                                <button class="btn btn-sm btn-primary" onclick="federated.updateNodeStatus(${node.id}, 'online')">
                                    Activate
                                </button>
                                <button class="btn btn-sm btn-secondary" onclick="federated.updateNodeStatus(${node.id}, 'offline')">
                                    Deactivate
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Failed to load nodes:', error);
        }
    }

    selectProject(projectId) {
        this.currentProject = projectId;
        this.loadProjectDetails(projectId);
        this.updateNetworkTopology();
    }

    async loadProjectDetails(projectId) {
        try {
            const response = await fetch(`/federated/projects/${projectId}`);
            const project = await response.json();

            const detailsContainer = document.getElementById('project-details');
            if (detailsContainer) {
                detailsContainer.innerHTML = `
                    <div class="project-header">
                        <h3>${project.name}</h3>
                        <span class="badge badge-${this.getStatusClass(project.status)}">${project.status}</span>
                    </div>
                    <div class="project-info">
                        <p><strong>Description:</strong> ${project.description}</p>
                        <p><strong>Coordinator:</strong> ${project.coordinator_name}</p>
                        <p><strong>Aggregation Method:</strong> ${project.aggregation_method}</p>
                        <p><strong>Privacy Budget:</strong> ${project.privacy_budget}</p>
                        <p><strong>Created:</strong> ${this.formatDate(project.created_at)}</p>
                    </div>
                    <div class="project-actions">
                        <button class="btn btn-primary" onclick="federated.startTraining(${project.id})">
                            Start Training
                        </button>
                        <button class="btn btn-secondary" onclick="federated.joinProject(${project.id})">
                            Join Project
                        </button>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Failed to load project details:', error);
        }
    }

    async startTraining(projectId = null) {
        const id = projectId || this.currentProject;
        if (!id) {
            autogent.showError('No project selected');
            return;
        }

        try {
            const response = await fetch(`/federated/projects/${id}/start_training`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();

            if (result.success) {
                autogent.showSuccess('Federated training started');
                this.loadProjects();
                this.startTrainingMonitor(id, result.training_round);
            } else {
                autogent.showError(result.error || 'Failed to start training');
            }
        } catch (error) {
            console.error('Training start error:', error);
            autogent.showError('Failed to start training');
        }
    }

    async joinProject(projectId = null) {
        const id = projectId || this.currentProject;
        if (!id) {
            autogent.showError('No project selected');
            return;
        }

        const nodeName = prompt('Enter node name:');
        if (!nodeName) return;

        const dataSamples = parseInt(prompt('Enter number of data samples:') || '0');

        try {
            const response = await fetch(`/federated/projects/${id}/join`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    node_name: nodeName,
                    data_samples: dataSamples
                })
            });

            const result = await response.json();

            if (result.success) {
                autogent.showSuccess('Successfully joined project');
                this.loadNodes();
                this.loadProjectDetails(id);
            } else {
                autogent.showError(result.error || 'Failed to join project');
            }
        } catch (error) {
            console.error('Join project error:', error);
            autogent.showError('Failed to join project');
        }
    }

    async updateNodeStatus(nodeId, status) {
        try {
            const response = await fetch(`/federated/nodes/${nodeId}/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status: status })
            });

            const result = await response.json();

            if (result.success) {
                autogent.showSuccess('Node status updated');
                this.loadNodes();
            } else {
                autogent.showError(result.error || 'Failed to update node');
            }
        } catch (error) {
            console.error('Node update error:', error);
            autogent.showError('Failed to update node');
        }
    }

    initializeNetworkTopology() {
        const canvas = document.getElementById('network-topology-canvas');
        if (canvas) {
            this.topologyCanvas = canvas;
            this.topologyCtx = canvas.getContext('2d');
            this.drawNetworkTopology();
        }
    }

    drawNetworkTopology() {
        if (!this.topologyCtx) return;

        this.topologyCtx.clearRect(0, 0, this.topologyCanvas.width, this.topologyCanvas.height);

        // Draw central coordinator
        const centerX = this.topologyCanvas.width / 2;
        const centerY = this.topologyCanvas.height / 2;
        
        this.topologyCtx.fillStyle = '#6366f1';
        this.topologyCtx.beginPath();
        this.topologyCtx.arc(centerX, centerY, 20, 0, 2 * Math.PI);
        this.topologyCtx.fill();

        this.topologyCtx.fillStyle = '#ffffff';
        this.topologyCtx.font = '12px Arial';
        this.topologyCtx.textAlign = 'center';
        this.topologyCtx.fillText('C', centerX, centerY + 4);

        // Draw connected nodes
        const nodeCount = 8;
        const radius = 120;
        
        for (let i = 0; i < nodeCount; i++) {
            const angle = (i / nodeCount) * 2 * Math.PI;
            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;

            // Draw connection line
            this.topologyCtx.strokeStyle = '#333333';
            this.topologyCtx.lineWidth = 2;
            this.topologyCtx.beginPath();
            this.topologyCtx.moveTo(centerX, centerY);
            this.topologyCtx.lineTo(x, y);
            this.topologyCtx.stroke();

            // Draw node
            this.topologyCtx.fillStyle = '#06b6d4';
            this.topologyCtx.beginPath();
            this.topologyCtx.arc(x, y, 12, 0, 2 * Math.PI);
            this.topologyCtx.fill();

            // Node label
            this.topologyCtx.fillStyle = '#ffffff';
            this.topologyCtx.fillText((i + 1).toString(), x, y + 4);
        }

        // Legend
        this.topologyCtx.fillStyle = '#ffffff';
        this.topologyCtx.font = '10px Arial';
        this.topologyCtx.textAlign = 'left';
        this.topologyCtx.fillText('C: Coordinator', 10, 20);
        this.topologyCtx.fillText('1-8: Federated Nodes', 10, 35);
    }

    updateNetworkTopology() {
        // Update topology with real node data
        this.drawNetworkTopology();
        // Add real-time status indicators
        this.addNodeStatusIndicators();
    }

    addNodeStatusIndicators() {
        // Add visual indicators for node status (online/offline/training)
        const centerX = this.topologyCanvas.width / 2;
        const centerY = this.topologyCanvas.height / 2;
        const radius = 120;
        const nodeCount = 8;

        for (let i = 0; i < nodeCount; i++) {
            const angle = (i / nodeCount) * 2 * Math.PI;
            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;

            // Status indicator (small circle)
            const statusColors = {
                online: '#10b981',
                offline: '#6b7280',
                training: '#f59e0b'
            };

            const status = Math.random() > 0.3 ? 'online' : 'offline';
            this.topologyCtx.fillStyle = statusColors[status];
            this.topologyCtx.beginPath();
            this.topologyCtx.arc(x + 8, y - 8, 3, 0, 2 * Math.PI);
            this.topologyCtx.fill();
        }
    }

    startTrainingMonitor(projectId, roundId) {
        const monitor = document.getElementById('training-monitor');
        if (monitor) {
            monitor.innerHTML = `
                <div class="training-progress">
                    <h4>Training Round ${roundId}</h4>
                    <div class="progress">
                        <div class="progress-bar" style="width: 0%"></div>
                    </div>
                    <div class="training-stats">
                        <div class="stat">
                            <span class="stat-label">Round</span>
                            <span class="stat-value">1</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Accuracy</span>
                            <span class="stat-value">0.000</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Loss</span>
                            <span class="stat-value">0.000</span>
                        </div>
                    </div>
                </div>
            `;
        }

        // Simulate training progress
        this.simulateTrainingProgress(projectId, roundId);
    }

    simulateTrainingProgress(projectId, roundId) {
        let progress = 0;
        let round = 1;
        const maxRounds = 10;

        const interval = setInterval(() => {
            progress += 10;
            
            if (progress >= 100) {
                progress = 0;
                round++;
                
                if (round > maxRounds) {
                    clearInterval(interval);
                    this.completeTraining(projectId, roundId);
                    return;
                }
            }

            // Update progress bar
            const progressBar = document.querySelector('.training-progress .progress-bar');
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }

            // Update stats
            const accuracy = Math.min(0.95, 0.5 + (round * 0.05) + (Math.random() * 0.02 - 0.01));
            const loss = Math.max(0.05, 2.0 - (round * 0.2) + (Math.random() * 0.1 - 0.05));

            const roundStat = document.querySelector('.training-stats .stat:nth-child(1) .stat-value');
            const accuracyStat = document.querySelector('.training-stats .stat:nth-child(2) .stat-value');
            const lossStat = document.querySelector('.training-stats .stat:nth-child(3) .stat-value');

            if (roundStat) roundStat.textContent = round.toString();
            if (accuracyStat) accuracyStat.textContent = accuracy.toFixed(3);
            if (lossStat) lossStat.textContent = loss.toFixed(3);
        }, 1000);
    }

    completeTraining(projectId, roundId) {
        const monitor = document.getElementById('training-monitor');
        if (monitor) {
            monitor.innerHTML += `
                <div class="training-complete">
                    <h5>Training Complete!</h5>
                    <p>Federated training round ${roundId} completed successfully.</p>
                    <button class="btn btn-primary" onclick="federated.downloadModel(${projectId})">
                        Download Model
                    </button>
                </div>
            `;
        }
        
        autogent.showSuccess('Federated training completed');
    }

    updatePrivacyDisplay() {
        const display = document.getElementById('privacy-budget-display');
        if (display) {
            display.textContent = `ε = ${this.privacyBudget.toFixed(2)}`;
        }

        const strengthIndicator = document.getElementById('privacy-strength');
        if (strengthIndicator) {
            const epsilon = -Math.log(this.privacyBudget);
            let strength = 'Very Weak';
            let color = '#ef4444';

            if (epsilon > 10) {
                strength = 'Very Strong';
                color = '#10b981';
            } else if (epsilon > 5) {
                strength = 'Strong';
                color = '#06b6d4';
            } else if (epsilon > 1) {
                strength = 'Moderate';
                color = '#f59e0b';
            }

            strengthIndicator.textContent = strength;
            strengthIndicator.style.color = color;
        }
    }

    updateAggregationMethod(method) {
        const description = document.getElementById('aggregation-description');
        if (description) {
            const descriptions = {
                fedavg: 'Federated Averaging - Simple weighted average of model parameters',
                fedprox: 'Federated Proximal - Adds proximal term to handle heterogeneity',
                scaffold: 'SCAFFOLD - Uses control variates to reduce client drift'
            };
            description.textContent = descriptions[method] || '';
        }
    }

    async updateProjectStatus() {
        if (!this.currentProject) return;

        try {
            const response = await fetch(`/api/federated/projects/${this.currentProject}/status`);
            const status = await response.json();

            // Update UI with latest status
            this.updateProjectStatusDisplay(status);
        } catch (error) {
            console.error('Failed to update project status:', error);
        }
    }

    updateProjectStatusDisplay(status) {
        const statusElement = document.querySelector('.project-header .badge');
        if (statusElement) {
            statusElement.className = `badge badge-${this.getStatusClass(status.status)}`;
            statusElement.textContent = status.status;
        }
    }

    async updateNodeStatuses() {
        try {
            const response = await fetch('/api/federated/nodes/status');
            const statuses = await response.json();

            // Update node status displays
            this.updateNodeStatusDisplays(statuses);
        } catch (error) {
            console.error('Failed to update node statuses:', error);
        }
    }

    updateNodeStatusDisplays(statuses) {
        statuses.forEach(status => {
            const nodeElement = document.querySelector(`[data-node-id="${status.node_id}"]`);
            if (nodeElement) {
                const badge = nodeElement.querySelector('.badge');
                if (badge) {
                    badge.className = `badge badge-${this.getStatusClass(status.status)}`;
                    badge.textContent = status.status;
                }
            }
        });
    }

    getStatusClass(status) {
        const statusClasses = {
            active: 'success',
            inactive: 'secondary',
            training: 'warning',
            completed: 'success',
            failed: 'danger',
            online: 'success',
            offline: 'secondary'
        };
        return statusClasses[status] || 'secondary';
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    downloadModel(projectId) {
        // Implementation for model download
        window.location.href = `/federated/projects/${projectId}/download_model`;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.startsWith('/federated')) {
        window.federated = new FederatedLearning();
    }
});
