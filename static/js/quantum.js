/**
 * Autogent Studio - Quantum Computing Module
 * Handles quantum circuit visualization, execution, and quantum algorithm design
 */

class QuantumComputing {
    constructor() {
        this.circuits = new Map();
        this.currentCircuit = null;
        this.qubits = 2;
        this.providers = ['qiskit', 'cirq', 'braket'];
        this.currentProvider = 'qiskit';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeCircuitDesigner();
        this.loadCircuits();
        console.log('Quantum Computing module initialized');
    }

    setupEventListeners() {
        // Circuit creation
        const createCircuitBtn = document.getElementById('create-circuit-btn');
        if (createCircuitBtn) {
            createCircuitBtn.addEventListener('click', () => this.createNewCircuit());
        }

        // Execute circuit
        const executeBtn = document.getElementById('execute-circuit-btn');
        if (executeBtn) {
            executeBtn.addEventListener('click', () => this.executeCircuit());
        }

        // Provider selection
        const providerSelect = document.getElementById('quantum-provider');
        if (providerSelect) {
            providerSelect.addEventListener('change', (e) => {
                this.currentProvider = e.target.value;
                this.updateCircuitProvider();
            });
        }

        // Qubit count change
        const qubitInput = document.getElementById('qubit-count');
        if (qubitInput) {
            qubitInput.addEventListener('change', (e) => {
                this.qubits = parseInt(e.target.value);
                this.updateCircuitQubits();
            });
        }

        // Gate palette
        this.setupGatePalette();

        // Algorithm templates
        this.setupAlgorithmTemplates();
    }

    setupGatePalette() {
        const gates = ['H', 'X', 'Y', 'Z', 'CNOT', 'RZ', 'RY', 'RX'];
        const palette = document.getElementById('gate-palette');
        
        if (palette) {
            gates.forEach(gate => {
                const gateBtn = document.createElement('button');
                gateBtn.className = 'btn btn-secondary gate-btn';
                gateBtn.textContent = gate;
                gateBtn.dataset.gate = gate.toLowerCase();
                gateBtn.addEventListener('click', () => this.selectGate(gate));
                palette.appendChild(gateBtn);
            });
        }
    }

    setupAlgorithmTemplates() {
        const templates = {
            'bell_state': 'Bell State',
            'grover_search': 'Grover Search',
            'quantum_fourier_transform': 'Quantum Fourier Transform',
            'deutsch_jozsa': 'Deutsch-Jozsa',
            'shor_algorithm': 'Shor\'s Algorithm'
        };

        const templateSelect = document.getElementById('algorithm-template');
        if (templateSelect) {
            Object.entries(templates).forEach(([key, value]) => {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = value;
                templateSelect.appendChild(option);
            });

            templateSelect.addEventListener('change', (e) => {
                if (e.target.value) {
                    this.loadAlgorithmTemplate(e.target.value);
                }
            });
        }
    }

    initializeCircuitDesigner() {
        const canvas = document.getElementById('quantum-circuit-canvas');
        if (canvas) {
            this.canvas = canvas;
            this.ctx = canvas.getContext('2d');
            this.setupCanvasEvents();
            this.drawEmptyCircuit();
        }
    }

    setupCanvasEvents() {
        this.canvas.addEventListener('click', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            this.handleCanvasClick(x, y);
        });

        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            this.handleCanvasHover(x, y);
        });
    }

    drawEmptyCircuit() {
        if (!this.ctx) return;

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.strokeStyle = '#06b6d4';
        this.ctx.lineWidth = 2;

        // Draw qubit lines
        for (let i = 0; i < this.qubits; i++) {
            const y = 50 + i * 60;
            this.ctx.beginPath();
            this.ctx.moveTo(50, y);
            this.ctx.lineTo(this.canvas.width - 50, y);
            this.ctx.stroke();

            // Draw qubit labels
            this.ctx.fillStyle = '#ffffff';
            this.ctx.font = '14px Arial';
            this.ctx.fillText(`|${i}⟩`, 10, y + 5);
        }

        // Draw time steps
        this.ctx.strokeStyle = '#333333';
        this.ctx.lineWidth = 1;
        for (let i = 0; i < 10; i++) {
            const x = 100 + i * 60;
            this.ctx.beginPath();
            this.ctx.moveTo(x, 30);
            this.ctx.lineTo(x, 50 + (this.qubits - 1) * 60 + 20);
            this.ctx.stroke();
        }
    }

    handleCanvasClick(x, y) {
        const qubitIndex = Math.floor((y - 20) / 60);
        const timeStep = Math.floor((x - 70) / 60);

        if (qubitIndex >= 0 && qubitIndex < this.qubits && timeStep >= 0) {
            this.addGateToCircuit(qubitIndex, timeStep);
        }
    }

    handleCanvasHover(x, y) {
        // Show gate preview on hover
        const qubitIndex = Math.floor((y - 20) / 60);
        const timeStep = Math.floor((x - 70) / 60);

        if (qubitIndex >= 0 && qubitIndex < this.qubits && timeStep >= 0) {
            this.canvas.style.cursor = 'pointer';
        } else {
            this.canvas.style.cursor = 'default';
        }
    }

    addGateToCircuit(qubitIndex, timeStep) {
        if (!this.currentCircuit) {
            this.currentCircuit = {
                qubits: this.qubits,
                gates: [],
                provider: this.currentProvider
            };
        }

        const selectedGate = this.getSelectedGate();
        if (selectedGate) {
            const gate = {
                type: selectedGate.toLowerCase(),
                qubits: [qubitIndex],
                timeStep: timeStep,
                params: []
            };

            // Handle two-qubit gates
            if (selectedGate === 'CNOT') {
                if (qubitIndex < this.qubits - 1) {
                    gate.qubits = [qubitIndex, qubitIndex + 1];
                } else {
                    gate.qubits = [qubitIndex - 1, qubitIndex];
                }
            }

            // Handle parametric gates
            if (['RZ', 'RY', 'RX'].includes(selectedGate)) {
                const angle = prompt('Enter rotation angle (in radians):');
                if (angle !== null) {
                    gate.params = [parseFloat(angle) || 0];
                }
            }

            this.currentCircuit.gates.push(gate);
            this.redrawCircuit();
        }
    }

    getSelectedGate() {
        const selectedBtn = document.querySelector('.gate-btn.selected');
        return selectedBtn ? selectedBtn.textContent : 'H';
    }

    selectGate(gate) {
        // Remove previous selection
        document.querySelectorAll('.gate-btn').forEach(btn => {
            btn.classList.remove('selected');
        });

        // Select new gate
        const gateBtn = document.querySelector(`[data-gate="${gate.toLowerCase()}"]`);
        if (gateBtn) {
            gateBtn.classList.add('selected');
        }
    }

    redrawCircuit() {
        this.drawEmptyCircuit();
        
        if (!this.currentCircuit) return;

        this.currentCircuit.gates.forEach(gate => {
            this.drawGate(gate);
        });
    }

    drawGate(gate) {
        const x = 100 + gate.timeStep * 60;
        const y = 50 + gate.qubits[0] * 60;

        this.ctx.fillStyle = '#6366f1';
        this.ctx.strokeStyle = '#ffffff';
        this.ctx.lineWidth = 2;

        if (gate.type === 'cnot' || gate.type === 'cx') {
            // Draw CNOT gate
            const controlY = 50 + gate.qubits[0] * 60;
            const targetY = 50 + gate.qubits[1] * 60;

            // Control qubit (filled circle)
            this.ctx.beginPath();
            this.ctx.arc(x, controlY, 8, 0, 2 * Math.PI);
            this.ctx.fill();

            // Connection line
            this.ctx.beginPath();
            this.ctx.moveTo(x, controlY);
            this.ctx.lineTo(x, targetY);
            this.ctx.stroke();

            // Target qubit (circle with cross)
            this.ctx.beginPath();
            this.ctx.arc(x, targetY, 15, 0, 2 * Math.PI);
            this.ctx.stroke();
            this.ctx.beginPath();
            this.ctx.moveTo(x - 10, targetY);
            this.ctx.lineTo(x + 10, targetY);
            this.ctx.moveTo(x, targetY - 10);
            this.ctx.lineTo(x, targetY + 10);
            this.ctx.stroke();
        } else {
            // Draw single-qubit gate
            this.ctx.fillRect(x - 15, y - 15, 30, 30);
            this.ctx.strokeRect(x - 15, y - 15, 30, 30);

            // Gate label
            this.ctx.fillStyle = '#ffffff';
            this.ctx.font = '12px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(gate.type.toUpperCase(), x, y + 4);
        }
    }

    async createNewCircuit() {
        const name = prompt('Enter circuit name:');
        if (!name) return;

        const circuitData = {
            name: name,
            description: '',
            qubits: this.qubits,
            provider: this.currentProvider,
            circuit_data: this.currentCircuit || {
                qubits: this.qubits,
                gates: [],
                provider: this.currentProvider
            }
        };

        try {
            const response = await fetch('/quantum/circuits/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(circuitData)
            });

            const result = await response.json();

            if (result.success) {
                autogent.showSuccess('Circuit created successfully');
                this.loadCircuits();
            } else {
                autogent.showError(result.error || 'Failed to create circuit');
            }
        } catch (error) {
            console.error('Circuit creation error:', error);
            autogent.showError('Failed to create circuit');
        }
    }

    async executeCircuit() {
        if (!this.currentCircuit) {
            autogent.showError('No circuit to execute');
            return;
        }

        const shots = parseInt(document.getElementById('shots-input')?.value || 1024);

        try {
            const response = await fetch('/quantum/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    circuit_id: this.currentCircuit.id,
                    shots: shots
                })
            });

            const result = await response.json();

            if (result.success) {
                this.displayResults(result.results);
                autogent.showSuccess('Circuit executed successfully');
            } else {
                autogent.showError(result.error || 'Execution failed');
            }
        } catch (error) {
            console.error('Execution error:', error);
            autogent.showError('Failed to execute circuit');
        }
    }

    displayResults(results) {
        const resultsContainer = document.getElementById('quantum-results');
        if (!resultsContainer) return;

        resultsContainer.innerHTML = `
            <h4>Execution Results</h4>
            <div class="results-summary">
                <p><strong>Shots:</strong> ${results.shots}</p>
                <p><strong>Provider:</strong> ${results.provider}</p>
                <p><strong>Success:</strong> ${results.success ? 'Yes' : 'No'}</p>
            </div>
            <div class="measurement-counts">
                <h5>Measurement Counts:</h5>
                ${this.renderMeasurementCounts(results.counts)}
            </div>
        `;

        // Create histogram
        this.createHistogram(results.counts);
    }

    renderMeasurementCounts(counts) {
        if (!counts) return '<p>No measurement data available</p>';

        const total = Object.values(counts).reduce((sum, count) => sum + count, 0);
        
        return Object.entries(counts)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([state, count]) => {
                const percentage = ((count / total) * 100).toFixed(1);
                return `
                    <div class="measurement-bar">
                        <span class="state-label">${state}</span>
                        <div class="bar-container">
                            <div class="bar" style="width: ${percentage}%"></div>
                        </div>
                        <span class="count-label">${count} (${percentage}%)</span>
                    </div>
                `;
            })
            .join('');
    }

    createHistogram(counts) {
        const canvas = document.getElementById('results-histogram');
        if (!canvas || !counts) return;

        const ctx = canvas.getContext('2d');
        const entries = Object.entries(counts).sort(([a], [b]) => a.localeCompare(b));
        
        if (entries.length === 0) return;

        const maxCount = Math.max(...Object.values(counts));
        const barWidth = canvas.width / entries.length;
        const barMaxHeight = canvas.height - 40;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        entries.forEach(([state, count], index) => {
            const barHeight = (count / maxCount) * barMaxHeight;
            const x = index * barWidth;
            const y = canvas.height - barHeight - 20;

            // Draw bar
            ctx.fillStyle = '#6366f1';
            ctx.fillRect(x + 10, y, barWidth - 20, barHeight);

            // Draw state label
            ctx.fillStyle = '#ffffff';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(state, x + barWidth / 2, canvas.height - 5);

            // Draw count label
            ctx.fillText(count.toString(), x + barWidth / 2, y - 5);
        });
    }

    async loadAlgorithmTemplate(templateName) {
        try {
            const response = await fetch(`/quantum/algorithms/${templateName}/template`);
            const template = await response.json();

            if (template.success) {
                this.currentCircuit = template.template;
                this.qubits = template.template.qubits;
                document.getElementById('qubit-count').value = this.qubits;
                this.redrawCircuit();
                autogent.showSuccess(`Loaded ${templateName} template`);
            } else {
                autogent.showError('Failed to load template');
            }
        } catch (error) {
            console.error('Template loading error:', error);
            autogent.showError('Failed to load template');
        }
    }

    async loadCircuits() {
        try {
            const response = await fetch('/api/quantum/circuits');
            const circuits = await response.json();

            const circuitsList = document.getElementById('circuits-list');
            if (circuitsList) {
                circuitsList.innerHTML = circuits.circuits.map(circuit => `
                    <div class="circuit-item" onclick="quantum.loadCircuit(${circuit.id})">
                        <h4>${circuit.name}</h4>
                        <p class="text-muted">${circuit.qubits} qubits • ${circuit.provider}</p>
                        <p class="text-muted">${circuit.description}</p>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Failed to load circuits:', error);
        }
    }

    async loadCircuit(circuitId) {
        try {
            const response = await fetch(`/quantum/circuits/${circuitId}`);
            const circuit = await response.json();

            if (circuit) {
                this.currentCircuit = circuit;
                this.qubits = circuit.qubits;
                document.getElementById('qubit-count').value = this.qubits;
                this.redrawCircuit();
                autogent.showSuccess(`Loaded circuit: ${circuit.name}`);
            }
        } catch (error) {
            console.error('Failed to load circuit:', error);
            autogent.showError('Failed to load circuit');
        }
    }

    updateCircuitProvider() {
        if (this.currentCircuit) {
            this.currentCircuit.provider = this.currentProvider;
        }
    }

    updateCircuitQubits() {
        if (this.currentCircuit) {
            this.currentCircuit.qubits = this.qubits;
        }
        this.redrawCircuit();
    }

    clearCircuit() {
        this.currentCircuit = null;
        this.drawEmptyCircuit();
    }

    saveCircuit() {
        if (!this.currentCircuit) {
            autogent.showError('No circuit to save');
            return;
        }

        // Implementation for saving circuit
        this.createNewCircuit();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.startsWith('/quantum')) {
        window.quantum = new QuantumComputing();
    }
});
