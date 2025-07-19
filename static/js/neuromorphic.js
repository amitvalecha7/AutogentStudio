/**
 * Autogent Studio - Neuromorphic Computing Module
 * Handles spiking neural networks, edge AI deployment, and neuromorphic hardware integration
 */

class NeuromorphicComputing {
    constructor() {
        this.models = new Map();
        this.currentModel = null;
        this.spikingData = [];
        this.hardwareTargets = ['loihi', 'truenorth', 'spinnaker'];
        this.currentTarget = 'loihi';
        this.simulationRunning = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeSpikeVisualization();
        this.loadModels();
        this.setupHardwareIntegration();
        console.log('Neuromorphic Computing module initialized');
    }

    setupEventListeners() {
        // Model management
        const createModelBtn = document.getElementById('create-model-btn');
        if (createModelBtn) {
            createModelBtn.addEventListener('click', () => this.createModel());
        }

        const simulateBtn = document.getElementById('simulate-btn');
        if (simulateBtn) {
            simulateBtn.addEventListener('click', () => this.runSimulation());
        }

        const deployBtn = document.getElementById('deploy-btn');
        if (deployBtn) {
            deployBtn.addEventListener('click', () => this.deployToHardware());
        }

        // Hardware target selection
        const hardwareSelect = document.getElementById('hardware-target');
        if (hardwareSelect) {
            hardwareSelect.addEventListener('change', (e) => {
                this.currentTarget = e.target.value;
                this.updateHardwareSpecs();
            });
        }

        // SNN parameter controls
        const spikeThreshold = document.getElementById('spike-threshold');
        if (spikeThreshold) {
            spikeThreshold.addEventListener('input', (e) => {
                this.updateSpikeThreshold(parseFloat(e.target.value));
            });
        }

        const refractoryPeriod = document.getElementById('refractory-period');
        if (refractoryPeriod) {
            refractoryPeriod.addEventListener('input', (e) => {
                this.updateRefractoryPeriod(parseInt(e.target.value));
            });
        }

        // Architecture builder
        this.setupArchitectureBuilder();
    }

    setupArchitectureBuilder() {
        const architectureTypes = ['feedforward', 'convolutional', 'recurrent'];
        const typeSelect = document.getElementById('architecture-type');
        
        if (typeSelect) {
            architectureTypes.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type.charAt(0).toUpperCase() + type.slice(1);
                typeSelect.appendChild(option);
            });

            typeSelect.addEventListener('change', (e) => {
                this.updateArchitectureType(e.target.value);
            });
        }
    }

    initializeSpikeVisualization() {
        const canvas = document.getElementById('spike-visualization-canvas');
        if (canvas) {
            this.spikeCanvas = canvas;
            this.spikeCtx = canvas.getContext('2d');
            this.startSpikeVisualization();
        }
    }

    startSpikeVisualization() {
        if (!this.spikeCtx) return;

        this.spikeVisualizationLoop = setInterval(() => {
            this.updateSpikeVisualization();
        }, 100);
    }

    updateSpikeVisualization() {
        if (!this.spikeCtx || !this.simulationRunning) return;

        const canvas = this.spikeCanvas;
        const ctx = this.spikeCtx;

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Generate random spike data for visualization
        const numNeurons = 20;
        const currentTime = Date.now();
        
        // Draw neuron lines
        ctx.strokeStyle = '#333333';
        ctx.lineWidth = 1;
        
        for (let i = 0; i < numNeurons; i++) {
            const y = (i + 1) * (canvas.height / (numNeurons + 1));
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }

        // Draw spikes
        ctx.strokeStyle = '#06b6d4';
        ctx.lineWidth = 2;
        
        this.spikingData.forEach(spike => {
            const age = currentTime - spike.timestamp;
            if (age < 1000) { // Show spikes for 1 second
                const x = canvas.width - (age / 1000) * canvas.width;
                const y = (spike.neuron + 1) * (canvas.height / (numNeurons + 1));
                const height = spike.magnitude * 20;
                
                ctx.beginPath();
                ctx.moveTo(x, y);
                ctx.lineTo(x, y - height);
                ctx.stroke();
            }
        });

        // Clean old spikes
        this.spikingData = this.spikingData.filter(spike => 
            currentTime - spike.timestamp < 1000
        );
    }

    generateSpike(neuronId, magnitude = 1.0) {
        this.spikingData.push({
            neuron: neuronId,
            magnitude: magnitude,
            timestamp: Date.now()
        });
    }

    async createModel() {
        const form = document.getElementById('create-model-form');
        if (!form) return;

        const formData = new FormData(form);
        const modelData = {
            name: formData.get('name'),
            description: formData.get('description'),
            architecture: this.getCurrentArchitecture(),
            hardware_target: this.currentTarget,
            spike_threshold: parseFloat(formData.get('spike_threshold') || 1.0),
            refractory_period: parseInt(formData.get('refractory_period') || 2)
        };

        try {
            const response = await fetch('/neuromorphic/models/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(modelData)
            });

            const result = await response.json();

            if (result.success) {
                autogent.showSuccess('Neuromorphic model created successfully');
                this.loadModels();
                this.closeModal('create-model-modal');
            } else {
                autogent.showError(result.error || 'Failed to create model');
            }
        } catch (error) {
            console.error('Model creation error:', error);
            autogent.showError('Failed to create model');
        }
    }

    getCurrentArchitecture() {
        const type = document.getElementById('architecture-type')?.value || 'feedforward';
        const inputSize = parseInt(document.getElementById('input-size')?.value || 28);
        const outputSize = parseInt(document.getElementById('output-size')?.value || 10);
        const hiddenLayers = parseInt(document.getElementById('hidden-layers')?.value || 2);
        const neuronsPerLayer = parseInt(document.getElementById('neurons-per-layer')?.value || 128);

        return {
            type: type,
            input_size: inputSize,
            output_size: outputSize,
            hidden_layers: hiddenLayers,
            neurons_per_layer: neuronsPerLayer,
            layers: this.generateLayers(type, inputSize, outputSize, hiddenLayers, neuronsPerLayer)
        };
    }

    generateLayers(type, inputSize, outputSize, hiddenLayers, neuronsPerLayer) {
        const layers = [];

        if (type === 'feedforward') {
            layers.push({ type: 'input', size: inputSize });
            for (let i = 0; i < hiddenLayers; i++) {
                layers.push({ type: 'hidden', size: neuronsPerLayer, neuron_type: 'lif' });
            }
            layers.push({ type: 'output', size: outputSize, neuron_type: 'lif' });
        } else if (type === 'convolutional') {
            layers.push({ type: 'conv', filters: 32, kernel_size: 5, neuron_type: 'lif' });
            layers.push({ type: 'pool', pool_size: 2 });
            layers.push({ type: 'conv', filters: 64, kernel_size: 5, neuron_type: 'lif' });
            layers.push({ type: 'pool', pool_size: 2 });
            layers.push({ type: 'flatten' });
            layers.push({ type: 'dense', size: outputSize, neuron_type: 'lif' });
        } else if (type === 'recurrent') {
            layers.push({ type: 'input', size: inputSize });
            layers.push({ type: 'lstm_snn', size: neuronsPerLayer, neuron_type: 'lif' });
            layers.push({ type: 'output', size: outputSize, neuron_type: 'lif' });
        }

        return layers;
    }

    async loadModels() {
        try {
            const response = await fetch('/api/neuromorphic/models');
            const models = await response.json();

            const modelsList = document.getElementById('models-list');
            if (modelsList) {
                modelsList.innerHTML = models.models.map(model => `
                    <div class="model-card card" onclick="neuromorphic.selectModel(${model.id})">
                        <div class="card-header">
                            <h4 class="card-title">${model.name}</h4>
                            <span class="badge badge-primary">${model.hardware_target}</span>
                        </div>
                        <div class="card-content">
                            <p>${model.description}</p>
                            <div class="model-stats">
                                <span class="stat">
                                    <i class="fas fa-microchip"></i> ${model.hardware_target}
                                </span>
                                <span class="stat">
                                    <i class="fas fa-bolt"></i> ${model.spike_threshold}V
                                </span>
                                <span class="stat">
                                    <i class="fas fa-clock"></i> ${model.refractory_period}ms
                                </span>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Failed to load models:', error);
        }
    }

    selectModel(modelId) {
        this.currentModel = modelId;
        this.loadModelDetails(modelId);
    }

    async loadModelDetails(modelId) {
        try {
            const response = await fetch(`/neuromorphic/models/${modelId}`);
            const model = await response.json();

            const detailsContainer = document.getElementById('model-details');
            if (detailsContainer) {
                detailsContainer.innerHTML = `
                    <div class="model-header">
                        <h3>${model.name}</h3>
                        <span class="badge badge-primary">${model.hardware_target}</span>
                    </div>
                    <div class="model-info">
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="label">Architecture</span>
                                <span class="value">${model.architecture.type}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">Spike Threshold</span>
                                <span class="value">${model.spike_threshold}V</span>
                            </div>
                            <div class="info-item">
                                <span class="label">Refractory Period</span>
                                <span class="value">${model.refractory_period}ms</span>
                            </div>
                            <div class="info-item">
                                <span class="label">Total Neurons</span>
                                <span class="value">${this.calculateTotalNeurons(model.architecture)}</span>
                            </div>
                        </div>
                    </div>
                    <div class="model-actions">
                        <button class="btn btn-primary" onclick="neuromorphic.runSimulation(${model.id})">
                            <i class="fas fa-play"></i> Simulate
                        </button>
                        <button class="btn btn-secondary" onclick="neuromorphic.deployToHardware(${model.id})">
                            <i class="fas fa-microchip"></i> Deploy
                        </button>
                        <button class="btn btn-warning" onclick="neuromorphic.optimizeForEdge(${model.id})">
                            <i class="fas fa-compress"></i> Optimize
                        </button>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Failed to load model details:', error);
        }
    }

    calculateTotalNeurons(architecture) {
        return architecture.layers.reduce((total, layer) => {
            return total + (layer.size || 0);
        }, 0);
    }

    async runSimulation(modelId = null) {
        const id = modelId || this.currentModel;
        if (!id) {
            autogent.showError('No model selected');
            return;
        }

        const simulationTime = parseInt(document.getElementById('simulation-time')?.value || 1000);
        const inputSpikes = this.generateInputSpikes();

        try {
            this.simulationRunning = true;
            this.updateSimulationStatus('Running simulation...');

            const response = await fetch(`/neuromorphic/models/${id}/simulate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    simulation_time: simulationTime,
                    input_spikes: inputSpikes
                })
            });

            const result = await response.json();

            if (result.success) {
                this.displaySimulationResults(result.results);
                autogent.showSuccess('Simulation completed successfully');
            } else {
                autogent.showError(result.error || 'Simulation failed');
            }
        } catch (error) {
            console.error('Simulation error:', error);
            autogent.showError('Failed to run simulation');
        } finally {
            this.simulationRunning = false;
            this.updateSimulationStatus('Ready');
        }
    }

    generateInputSpikes() {
        const inputSpikes = [];
        const numInputs = 10;
        const simulationTime = 1000;

        for (let i = 0; i < numInputs; i++) {
            const spikes = [];
            const spikeRate = Math.random() * 50; // Random firing rate
            
            for (let t = 0; t < simulationTime; t += 10) {
                if (Math.random() < spikeRate / 1000) {
                    spikes.push(t);
                }
            }
            
            inputSpikes.push(spikes);
        }

        return inputSpikes;
    }

    displaySimulationResults(results) {
        const resultsContainer = document.getElementById('simulation-results');
        if (!resultsContainer) return;

        resultsContainer.innerHTML = `
            <div class="results-header">
                <h4>Simulation Results</h4>
                <span class="badge badge-${results.success ? 'success' : 'danger'}">
                    ${results.success ? 'Success' : 'Failed'}
                </span>
            </div>
            <div class="results-stats">
                <div class="stat">
                    <span class="stat-label">Simulation Time</span>
                    <span class="stat-value">${results.simulation_time}ms</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Total Spikes</span>
                    <span class="stat-value">${results.num_spikes}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Firing Rate</span>
                    <span class="stat-value">${results.firing_rate.toFixed(2)} Hz</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Simulator</span>
                    <span class="stat-value">${results.simulator}</span>
                </div>
            </div>
            <div class="spike-data">
                <h5>Spike Pattern Analysis</h5>
                <div class="spike-stats">
                    ${this.renderSpikeStats(results)}
                </div>
            </div>
        `;

        // Update visualization with real data
        this.updateSpikeVisualizationWithData(results);
    }

    renderSpikeStats(results) {
        if (!results.spike_times || results.spike_times.length === 0) {
            return '<p>No spikes detected</p>';
        }

        const spikesByNeuron = this.groupSpikesByNeuron(results.spike_times, results.spike_neurons);
        
        return Object.entries(spikesByNeuron)
            .slice(0, 10) // Show top 10 neurons
            .map(([neuron, spikes]) => `
                <div class="neuron-activity">
                    <span class="neuron-label">Neuron ${neuron}</span>
                    <div class="activity-bar">
                        <div class="bar" style="width: ${(spikes.length / Math.max(...Object.values(spikesByNeuron))) * 100}%"></div>
                    </div>
                    <span class="spike-count">${spikes.length}</span>
                </div>
            `).join('');
    }

    groupSpikesByNeuron(spikeTimes, spikeNeurons) {
        const groups = {};
        
        for (let i = 0; i < spikeTimes.length; i++) {
            const neuron = spikeNeurons[i] || 0;
            if (!groups[neuron]) {
                groups[neuron] = [];
            }
            groups[neuron].push(spikeTimes[i]);
        }
        
        return groups;
    }

    updateSpikeVisualizationWithData(results) {
        // Add real spike data to visualization
        if (results.spike_times && results.spike_neurons) {
            const currentTime = Date.now();
            
            for (let i = 0; i < results.spike_times.length; i++) {
                const neuronId = results.spike_neurons[i] || 0;
                const magnitude = 1.0;
                
                // Add with slight delay to show progression
                setTimeout(() => {
                    this.generateSpike(neuronId % 20, magnitude);
                }, i * 10);
            }
        }
    }

    async deployToHardware(modelId = null) {
        const id = modelId || this.currentModel;
        if (!id) {
            autogent.showError('No model selected');
            return;
        }

        const targetHardware = document.getElementById('hardware-target')?.value || this.currentTarget;

        try {
            const response = await fetch(`/neuromorphic/models/${id}/deploy`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    target_hardware: targetHardware
                })
            });

            const result = await response.json();

            if (result.success) {
                autogent.showSuccess(`Model deployed to ${targetHardware} successfully`);
                this.displayDeploymentInfo(result.deployment_id, targetHardware);
            } else {
                autogent.showError(result.error || 'Deployment failed');
            }
        } catch (error) {
            console.error('Deployment error:', error);
            autogent.showError('Failed to deploy model');
        }
    }

    displayDeploymentInfo(deploymentId, hardware) {
        const deploymentContainer = document.getElementById('deployment-info');
        if (deploymentContainer) {
            deploymentContainer.innerHTML = `
                <div class="deployment-success">
                    <h4>Deployment Successful</h4>
                    <p><strong>Deployment ID:</strong> ${deploymentId}</p>
                    <p><strong>Hardware Target:</strong> ${hardware}</p>
                    <p><strong>Status:</strong> <span class="badge badge-success">Active</span></p>
                    <div class="deployment-actions">
                        <button class="btn btn-primary" onclick="neuromorphic.monitorDeployment('${deploymentId}')">
                            Monitor
                        </button>
                        <button class="btn btn-secondary" onclick="neuromorphic.stopDeployment('${deploymentId}')">
                            Stop
                        </button>
                    </div>
                </div>
            `;
        }
    }

    async optimizeForEdge(modelId = null) {
        const id = modelId || this.currentModel;
        if (!id) {
            autogent.showError('No model selected');
            return;
        }

        const constraints = {
            max_power: parseFloat(document.getElementById('max-power')?.value || 1.0),
            max_latency: parseFloat(document.getElementById('max-latency')?.value || 10.0),
            min_accuracy: parseFloat(document.getElementById('min-accuracy')?.value || 0.8)
        };

        try {
            const response = await fetch('/neuromorphic/optimize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model_id: id,
                    constraints: constraints
                })
            });

            const result = await response.json();

            if (result.success) {
                this.displayOptimizationResults(result);
                autogent.showSuccess('Model optimization completed');
            } else {
                autogent.showError(result.error || 'Optimization failed');
            }
        } catch (error) {
            console.error('Optimization error:', error);
            autogent.showError('Failed to optimize model');
        }
    }

    displayOptimizationResults(results) {
        const optimizationContainer = document.getElementById('optimization-results');
        if (!optimizationContainer) return;

        optimizationContainer.innerHTML = `
            <div class="optimization-summary">
                <h4>Edge Optimization Results</h4>
                <div class="optimization-stats">
                    <div class="stat">
                        <span class="stat-label">Original Neurons</span>
                        <span class="stat-value">${results.original_neurons}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Optimized Neurons</span>
                        <span class="stat-value">${results.optimized_neurons}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Estimated Power</span>
                        <span class="stat-value">${results.estimated_power.toFixed(2)}W</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Estimated Latency</span>
                        <span class="stat-value">${results.estimated_latency.toFixed(2)}ms</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Estimated Accuracy</span>
                        <span class="stat-value">${(results.estimated_accuracy * 100).toFixed(1)}%</span>
                    </div>
                </div>
                <div class="optimization-status">
                    <span class="badge badge-${results.meets_constraints ? 'success' : 'warning'}">
                        ${results.meets_constraints ? 'Constraints Met' : 'Constraints Not Met'}
                    </span>
                </div>
                <div class="optimizations-applied">
                    <h5>Optimizations Applied:</h5>
                    <ul>
                        ${results.optimizations_applied.map(opt => `<li>${opt}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }

    setupHardwareIntegration() {
        this.hardwareSpecs = {
            loihi: {
                neurons: 131072,
                synapses: 131000000,
                power: 0.001,
                description: 'Intel Loihi neuromorphic chip'
            },
            truenorth: {
                neurons: 1000000,
                synapses: 256000000,
                power: 0.07,
                description: 'IBM TrueNorth brain-inspired chip'
            },
            spinnaker: {
                neurons: 1000000000,
                synapses: 1000000000000,
                power: 1000,
                description: 'SpiNNaker million-core architecture'
            }
        };

        this.updateHardwareSpecs();
    }

    updateHardwareSpecs() {
        const specs = this.hardwareSpecs[this.currentTarget];
        if (!specs) return;

        const specsContainer = document.getElementById('hardware-specs');
        if (specsContainer) {
            specsContainer.innerHTML = `
                <div class="hardware-info">
                    <h4>${this.currentTarget.toUpperCase()}</h4>
                    <p>${specs.description}</p>
                    <div class="specs-grid">
                        <div class="spec-item">
                            <span class="spec-label">Neurons</span>
                            <span class="spec-value">${specs.neurons.toLocaleString()}</span>
                        </div>
                        <div class="spec-item">
                            <span class="spec-label">Synapses</span>
                            <span class="spec-value">${specs.synapses.toLocaleString()}</span>
                        </div>
                        <div class="spec-item">
                            <span class="spec-label">Power</span>
                            <span class="spec-value">${specs.power < 1 ? (specs.power * 1000) + 'mW' : specs.power + 'W'}</span>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    updateSpikeThreshold(threshold) {
        if (this.currentModel) {
            // Update model threshold
            const display = document.getElementById('spike-threshold-display');
            if (display) {
                display.textContent = `${threshold.toFixed(2)}V`;
            }
        }
    }

    updateRefractoryPeriod(period) {
        if (this.currentModel) {
            // Update model refractory period
            const display = document.getElementById('refractory-period-display');
            if (display) {
                display.textContent = `${period}ms`;
            }
        }
    }

    updateArchitectureType(type) {
        const architecturePreview = document.getElementById('architecture-preview');
        if (architecturePreview) {
            const descriptions = {
                feedforward: 'Standard feedforward SNN with multiple hidden layers',
                convolutional: 'Convolutional SNN for spatial pattern recognition',
                recurrent: 'Recurrent SNN with temporal dynamics and memory'
            };
            
            architecturePreview.innerHTML = `
                <div class="architecture-description">
                    <h5>${type.charAt(0).toUpperCase() + type.slice(1)} Architecture</h5>
                    <p>${descriptions[type]}</p>
                </div>
            `;
        }
    }

    updateSimulationStatus(status) {
        const statusElement = document.getElementById('simulation-status');
        if (statusElement) {
            statusElement.textContent = status;
        }
    }

    monitorDeployment(deploymentId) {
        // Implementation for deployment monitoring
        console.log('Monitoring deployment:', deploymentId);
    }

    stopDeployment(deploymentId) {
        // Implementation for stopping deployment
        console.log('Stopping deployment:', deploymentId);
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.startsWith('/neuromorphic')) {
        window.neuromorphic = new NeuromorphicComputing();
    }
});
