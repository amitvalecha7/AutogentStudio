// Autogent Studio Drawflow Integration for AI Model Orchestration

class AutogentDrawflow {
    constructor(container) {
        this.container = container;
        this.editor = null;
        this.nodeId = 1;
        this.workflowData = null;
        this.executionResults = {};
        
        this.init();
    }

    init() {
        // Initialize Drawflow
        this.editor = new Drawflow(this.container);
        this.editor.reroute = true;
        this.editor.reroute_fix_curvature = true;
        this.editor.force_first_input = false;
        
        this.editor.start();
        
        this.setupNodeTypes();
        this.bindEvents();
        this.loadWorkflow();
    }

    setupNodeTypes() {
        // Define available AI model nodes
        this.nodeTypes = {
            'input': {
                name: 'Data Input',
                inputs: 0,
                outputs: 1,
                category: 'Data',
                icon: 'fas fa-play',
                color: '#10b981'
            },
            'llm': {
                name: 'Language Model',
                inputs: 1,
                outputs: 1,
                category: 'AI Models',
                icon: 'fas fa-brain',
                color: '#3b82f6',
                models: ['gpt-4o', 'claude-sonnet-4-20250514', 'gemini-pro']
            },
            'image-gen': {
                name: 'Image Generation',
                inputs: 1,
                outputs: 1,
                category: 'AI Models',
                icon: 'fas fa-image',
                color: '#8b5cf6',
                models: ['dall-e-3', 'midjourney', 'stable-diffusion']
            },
            'embedding': {
                name: 'Text Embedding',
                inputs: 1,
                outputs: 1,
                category: 'AI Models',
                icon: 'fas fa-vector-square',
                color: '#06b6d4'
            },
            'quantum': {
                name: 'Quantum Circuit',
                inputs: 1,
                outputs: 1,
                category: 'Quantum',
                icon: 'fas fa-atom',
                color: '#f59e0b'
            },
            'neuromorphic': {
                name: 'Neuromorphic Processing',
                inputs: 1,
                outputs: 1,
                category: 'Neuromorphic',
                icon: 'fas fa-project-diagram',
                color: '#ef4444'
            },
            'federated': {
                name: 'Federated Learning',
                inputs: 1,
                outputs: 1,
                category: 'Distributed',
                icon: 'fas fa-network-wired',
                color: '#84cc16'
            },
            'safety-check': {
                name: 'Safety Validation',
                inputs: 1,
                outputs: 2,
                category: 'Safety',
                icon: 'fas fa-shield-alt',
                color: '#f97316'
            },
            'data-transform': {
                name: 'Data Transform',
                inputs: 1,
                outputs: 1,
                category: 'Data',
                icon: 'fas fa-exchange-alt',
                color: '#6b7280'
            },
            'conditional': {
                name: 'Conditional Logic',
                inputs: 1,
                outputs: 2,
                category: 'Logic',
                icon: 'fas fa-code-branch',
                color: '#ec4899'
            },
            'output': {
                name: 'Output',
                inputs: 1,
                outputs: 0,
                category: 'Data',
                icon: 'fas fa-stop',
                color: '#dc2626'
            }
        };
        
        this.createNodePalette();
    }

    createNodePalette() {
        const palette = document.querySelector('.node-palette');
        if (!palette) return;

        const categories = {};
        Object.entries(this.nodeTypes).forEach(([type, config]) => {
            if (!categories[config.category]) {
                categories[config.category] = [];
            }
            categories[config.category].push({ type, config });
        });

        palette.innerHTML = '';
        Object.entries(categories).forEach(([category, nodes]) => {
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'node-category';
            categoryDiv.innerHTML = `
                <h6 class="category-title">${category}</h6>
                <div class="category-nodes">
                    ${nodes.map(({ type, config }) => `
                        <div class="node-item" draggable="true" data-node-type="${type}">
                            <i class="${config.icon}" style="color: ${config.color}"></i>
                            <span>${config.name}</span>
                        </div>
                    `).join('')}
                </div>
            `;
            
            palette.appendChild(categoryDiv);
        });

        // Add drag and drop functionality
        palette.querySelectorAll('.node-item').forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', e.target.dataset.nodeType);
            });
            
            item.addEventListener('click', () => {
                this.addNodeToCanvas(item.dataset.nodeType);
            });
        });
    }

    bindEvents() {
        // Canvas drop handling
        this.container.addEventListener('dragover', (e) => e.preventDefault());
        this.container.addEventListener('drop', (e) => {
            e.preventDefault();
            const nodeType = e.dataTransfer.getData('text/plain');
            if (nodeType) {
                const rect = this.container.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                this.addNodeToCanvas(nodeType, x, y);
            }
        });

        // Toolbar buttons
        const toolbar = document.querySelector('.workflow-toolbar');
        if (toolbar) {
            toolbar.querySelector('.save-workflow')?.addEventListener('click', () => this.saveWorkflow());
            toolbar.querySelector('.load-workflow')?.addEventListener('click', () => this.loadWorkflowDialog());
            toolbar.querySelector('.execute-workflow')?.addEventListener('click', () => this.executeWorkflow());
            toolbar.querySelector('.clear-workflow')?.addEventListener('click', () => this.clearWorkflow());
            toolbar.querySelector('.export-workflow')?.addEventListener('click', () => this.exportWorkflow());
        }

        // Editor events
        this.editor.on('nodeCreated', (id) => {
            this.onNodeCreated(id);
        });

        this.editor.on('nodeSelected', (id) => {
            this.onNodeSelected(id);
        });

        this.editor.on('connectionCreated', (connection) => {
            this.onConnectionCreated(connection);
        });
    }

    addNodeToCanvas(nodeType, x = 200, y = 200) {
        const config = this.nodeTypes[nodeType];
        if (!config) return;

        const nodeHTML = this.createNodeHTML(nodeType, config);
        const nodeId = this.nodeId++;

        this.editor.addNode(
            nodeType,
            config.inputs,
            config.outputs,
            x,
            y,
            nodeType,
            {},
            nodeHTML
        );

        return nodeId;
    }

    createNodeHTML(nodeType, config) {
        let settingsHTML = '';
        
        // Add model selector for AI model nodes
        if (config.models) {
            settingsHTML = `
                <div class="node-settings">
                    <select class="model-select">
                        ${config.models.map(model => `<option value="${model}">${model}</option>`).join('')}
                    </select>
                </div>
            `;
        }

        // Add configuration for specific node types
        switch (nodeType) {
            case 'input':
                settingsHTML = `
                    <div class="node-settings">
                        <input type="text" placeholder="Input data..." class="input-data">
                    </div>
                `;
                break;
            case 'conditional':
                settingsHTML = `
                    <div class="node-settings">
                        <input type="text" placeholder="Condition..." class="condition-text">
                    </div>
                `;
                break;
            case 'data-transform':
                settingsHTML = `
                    <div class="node-settings">
                        <select class="transform-type">
                            <option value="json">JSON Parse</option>
                            <option value="text">Text Extract</option>
                            <option value="filter">Filter</option>
                            <option value="map">Map</option>
                        </select>
                    </div>
                `;
                break;
            case 'safety-check':
                settingsHTML = `
                    <div class="node-settings">
                        <label><input type="checkbox" checked> Toxicity Check</label>
                        <label><input type="checkbox" checked> Bias Detection</label>
                        <label><input type="checkbox"> Privacy Check</label>
                    </div>
                `;
                break;
        }

        return `
            <div class="workflow-node" style="border-left: 4px solid ${config.color}">
                <div class="node-header">
                    <i class="${config.icon}"></i>
                    <span class="node-title">${config.name}</span>
                </div>
                ${settingsHTML}
                <div class="node-status">
                    <span class="status-indicator"></span>
                </div>
            </div>
        `;
    }

    onNodeCreated(id) {
        const nodeElement = this.container.querySelector(`#node-${id}`);
        if (nodeElement) {
            // Add event listeners to node controls
            const inputs = nodeElement.querySelectorAll('input, select');
            inputs.forEach(input => {
                input.addEventListener('change', () => {
                    this.updateNodeData(id, this.getNodeSettings(nodeElement));
                });
            });
        }
    }

    onNodeSelected(id) {
        this.showNodeProperties(id);
    }

    onConnectionCreated(connection) {
        // Validate connection compatibility
        const outputNode = this.editor.getNodeFromId(connection.output_id);
        const inputNode = this.editor.getNodeFromId(connection.input_id);
        
        if (!this.isConnectionValid(outputNode, inputNode)) {
            this.editor.removeSingleConnection(connection.output_id, connection.input_id, connection.output_class, connection.input_class);
            window.autogentStudio.showNotification('Invalid connection: incompatible node types', 'error');
        }
    }

    isConnectionValid(outputNode, inputNode) {
        // Define connection rules
        const rules = {
            'input': ['llm', 'image-gen', 'embedding', 'data-transform'],
            'llm': ['output', 'safety-check', 'conditional', 'data-transform'],
            'image-gen': ['output', 'safety-check'],
            'embedding': ['output', 'data-transform'],
            'quantum': ['output', 'data-transform'],
            'neuromorphic': ['output', 'data-transform'],
            'federated': ['output', 'data-transform'],
            'safety-check': ['output', 'conditional'],
            'data-transform': ['llm', 'output', 'conditional'],
            'conditional': ['llm', 'image-gen', 'output']
        };

        const allowedTargets = rules[outputNode.name] || [];
        return allowedTargets.includes(inputNode.name);
    }

    getNodeSettings(nodeElement) {
        const settings = {};
        
        const inputs = nodeElement.querySelectorAll('input, select');
        inputs.forEach(input => {
            if (input.type === 'checkbox') {
                settings[input.name || input.className] = input.checked;
            } else {
                settings[input.name || input.className] = input.value;
            }
        });
        
        return settings;
    }

    updateNodeData(id, settings) {
        const nodeData = this.editor.getNodeFromId(id);
        nodeData.data = { ...nodeData.data, ...settings };
    }

    showNodeProperties(id) {
        const nodeData = this.editor.getNodeFromId(id);
        const propertiesPanel = document.querySelector('.properties-panel');
        
        if (propertiesPanel) {
            propertiesPanel.innerHTML = `
                <h6>Node Properties</h6>
                <div class="property-item">
                    <label>Node ID:</label>
                    <span>${id}</span>
                </div>
                <div class="property-item">
                    <label>Type:</label>
                    <span>${nodeData.name}</span>
                </div>
                <div class="property-item">
                    <label>Position:</label>
                    <span>(${nodeData.pos_x}, ${nodeData.pos_y})</span>
                </div>
                <div class="property-item">
                    <label>Connections:</label>
                    <span>In: ${Object.keys(nodeData.inputs).length}, Out: ${Object.keys(nodeData.outputs).length}</span>
                </div>
            `;
        }
    }

    async saveWorkflow() {
        const workflowData = this.editor.export();
        
        try {
            const response = await fetch('/api/orchestration/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    workflow_name: prompt('Enter workflow name:') || 'Untitled Workflow',
                    workflow_data: workflowData
                })
            });

            if (response.ok) {
                window.autogentStudio.showNotification('Workflow saved successfully', 'success');
            } else {
                throw new Error('Save failed');
            }
        } catch (error) {
            window.autogentStudio.showNotification('Failed to save workflow', 'error');
        }
    }

    loadWorkflowDialog() {
        // Create load dialog
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content as-card">
                    <div class="modal-header">
                        <h5 class="modal-title">Load Workflow</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="workflow-list">
                            <div class="as-loading"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        // Load workflow list
        this.loadWorkflowList(modal.querySelector('.workflow-list'));
        
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    async loadWorkflowList(container) {
        try {
            const response = await fetch('/api/orchestration/list');
            const data = await response.json();
            
            if (data.success) {
                container.innerHTML = data.workflows.map(workflow => `
                    <div class="workflow-item as-card" data-workflow-id="${workflow.id}">
                        <h6>${workflow.workflow_name}</h6>
                        <p class="text-muted">${workflow.created_at}</p>
                        <button class="as-btn as-btn-primary load-workflow-btn">Load</button>
                    </div>
                `).join('');
                
                container.querySelectorAll('.load-workflow-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        const workflowId = e.target.closest('.workflow-item').dataset.workflowId;
                        this.loadWorkflow(workflowId);
                        bootstrap.Modal.getInstance(e.target.closest('.modal')).hide();
                    });
                });
            }
        } catch (error) {
            container.innerHTML = '<p class="text-danger">Failed to load workflows</p>';
        }
    }

    async loadWorkflow(workflowId) {
        try {
            const response = await fetch(`/api/orchestration/load/${workflowId}`);
            const data = await response.json();
            
            if (data.success) {
                this.editor.import(data.workflow_data);
                window.autogentStudio.showNotification('Workflow loaded successfully', 'success');
            }
        } catch (error) {
            window.autogentStudio.showNotification('Failed to load workflow', 'error');
        }
    }

    async executeWorkflow() {
        const workflowData = this.editor.export();
        
        if (Object.keys(workflowData.drawflow.Home.data).length === 0) {
            window.autogentStudio.showNotification('No workflow to execute', 'warning');
            return;
        }

        // Reset execution status
        this.executionResults = {};
        this.updateAllNodeStatus('pending');
        
        try {
            const response = await fetch('/api/orchestration/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ workflow_data: workflowData })
            });

            const data = await response.json();
            
            if (data.success) {
                window.autogentStudio.showNotification('Workflow execution started', 'success');
                this.pollExecutionStatus(data.execution_id);
            } else {
                throw new Error(data.error || 'Execution failed');
            }
        } catch (error) {
            window.autogentStudio.showNotification('Failed to execute workflow', 'error');
            this.updateAllNodeStatus('error');
        }
    }

    async pollExecutionStatus(executionId) {
        const poll = async () => {
            try {
                const response = await fetch(`/api/orchestration/status/${executionId}`);
                const data = await response.json();
                
                if (data.success) {
                    this.updateExecutionStatus(data.status);
                    
                    if (data.status.status === 'completed' || data.status.status === 'failed') {
                        clearInterval(pollInterval);
                        this.showExecutionResults(data.status);
                    }
                }
            } catch (error) {
                clearInterval(pollInterval);
                console.error('Failed to poll execution status:', error);
            }
        };
        
        const pollInterval = setInterval(poll, 1000);
        poll(); // Initial poll
    }

    updateExecutionStatus(status) {
        // Update node statuses based on execution progress
        Object.entries(status.node_results || {}).forEach(([nodeId, result]) => {
            this.updateNodeStatus(nodeId, result.status);
        });
    }

    updateNodeStatus(nodeId, status) {
        const nodeElement = this.container.querySelector(`#node-${nodeId}`);
        if (nodeElement) {
            const indicator = nodeElement.querySelector('.status-indicator');
            if (indicator) {
                indicator.className = `status-indicator status-${status}`;
                indicator.title = status.charAt(0).toUpperCase() + status.slice(1);
            }
        }
    }

    updateAllNodeStatus(status) {
        const indicators = this.container.querySelectorAll('.status-indicator');
        indicators.forEach(indicator => {
            indicator.className = `status-indicator status-${status}`;
        });
    }

    showExecutionResults(results) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content as-card">
                    <div class="modal-header">
                        <h5 class="modal-title">Execution Results</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="execution-summary">
                            <p><strong>Status:</strong> <span class="badge as-badge-${results.status}">${results.status}</span></p>
                            <p><strong>Duration:</strong> ${results.duration || 'N/A'}</p>
                            <p><strong>Nodes Executed:</strong> ${Object.keys(results.node_results || {}).length}</p>
                        </div>
                        <div class="node-results">
                            ${Object.entries(results.node_results || {}).map(([nodeId, result]) => `
                                <div class="result-item">
                                    <h6>Node ${nodeId}</h6>
                                    <pre>${JSON.stringify(result, null, 2)}</pre>
                                </div>
                            `).join('')}
                        </div>
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

    clearWorkflow() {
        if (confirm('Are you sure you want to clear the workflow? This action cannot be undone.')) {
            this.editor.clear();
            window.autogentStudio.showNotification('Workflow cleared', 'success');
        }
    }

    exportWorkflow() {
        const workflowData = this.editor.export();
        const blob = new Blob([JSON.stringify(workflowData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `autogent-workflow-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        window.autogentStudio.showNotification('Workflow exported successfully', 'success');
    }
}

// Initialize Drawflow when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const drawflowContainer = document.querySelector('#drawflow');
    if (drawflowContainer) {
        window.autogentDrawflow = new AutogentDrawflow(drawflowContainer);
    }
});
