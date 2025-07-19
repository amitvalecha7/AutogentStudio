import json
import os
from typing import Dict, List
from models import QuantumCircuit
from app import db

class QuantumService:
    def __init__(self):
        self.providers = {
            'qiskit': self._init_qiskit,
            'cirq': self._init_cirq,
            'braket': self._init_braket
        }
        self.available_providers = []
        self._check_available_providers()
    
    def _check_available_providers(self):
        """Check which quantum providers are available"""
        try:
            import qiskit
            self.available_providers.append('qiskit')
        except ImportError:
            pass
        
        try:
            import cirq
            self.available_providers.append('cirq')
        except ImportError:
            pass
        
        try:
            import boto3
            self.available_providers.append('braket')
        except ImportError:
            pass
    
    def _init_qiskit(self):
        """Initialize Qiskit provider"""
        try:
            from qiskit import QuantumCircuit as QiskitCircuit
            from qiskit import transpile, Aer
            from qiskit.visualization import circuit_drawer
            
            return {
                'QuantumCircuit': QiskitCircuit,
                'transpile': transpile,
                'Aer': Aer,
                'circuit_drawer': circuit_drawer
            }
        except ImportError:
            return None
    
    def _init_cirq(self):
        """Initialize Cirq provider"""
        try:
            import cirq
            return cirq
        except ImportError:
            return None
    
    def _init_braket(self):
        """Initialize AWS Braket provider"""
        try:
            from braket.circuits import Circuit
            from braket.devices import LocalSimulator
            return {
                'Circuit': Circuit,
                'LocalSimulator': LocalSimulator
            }
        except ImportError:
            return None
    
    def create_circuit(self, user_id: str, name: str, provider: str = 'qiskit', circuit_data: dict = None) -> str:
        """Create a new quantum circuit"""
        try:
            if provider not in self.available_providers:
                raise ValueError(f"Provider {provider} not available")
            
            if not circuit_data:
                circuit_data = self._create_default_circuit(provider)
            
            circuit = QuantumCircuit(
                user_id=user_id,
                name=name,
                circuit_data=circuit_data,
                provider=provider
            )
            
            db.session.add(circuit)
            db.session.commit()
            
            return str(circuit.id)
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create quantum circuit: {str(e)}")
    
    def _create_default_circuit(self, provider: str) -> dict:
        """Create a default quantum circuit for the provider"""
        if provider == 'qiskit':
            return {
                'num_qubits': 2,
                'gates': [
                    {'type': 'h', 'qubit': 0},
                    {'type': 'cx', 'control': 0, 'target': 1}
                ],
                'measurements': [0, 1]
            }
        elif provider == 'cirq':
            return {
                'num_qubits': 2,
                'gates': [
                    {'type': 'H', 'qubit': 0},
                    {'type': 'CNOT', 'control': 0, 'target': 1}
                ]
            }
        elif provider == 'braket':
            return {
                'num_qubits': 2,
                'instructions': [
                    {'gate': 'h', 'target': 0},
                    {'gate': 'cnot', 'control': 0, 'target': 1}
                ]
            }
        else:
            return {}
    
    def get_user_circuits(self, user_id: str) -> List[Dict]:
        """Get all quantum circuits for a user"""
        try:
            circuits = QuantumCircuit.query.filter_by(user_id=user_id).order_by(QuantumCircuit.created_at.desc()).all()
            
            return [
                {
                    'id': str(circuit.id),
                    'name': circuit.name,
                    'provider': circuit.provider,
                    'num_qubits': circuit.circuit_data.get('num_qubits', 0),
                    'created_at': circuit.created_at.isoformat()
                }
                for circuit in circuits
            ]
        except Exception as e:
            raise Exception(f"Failed to get quantum circuits: {str(e)}")
    
    def simulate_circuit(self, circuit_id: str, shots: int = 1024) -> Dict:
        """Simulate a quantum circuit"""
        try:
            circuit = QuantumCircuit.query.get(circuit_id)
            if not circuit:
                raise ValueError("Circuit not found")
            
            provider = circuit.provider
            circuit_data = circuit.circuit_data
            
            if provider == 'qiskit':
                return self._simulate_qiskit_circuit(circuit_data, shots)
            elif provider == 'cirq':
                return self._simulate_cirq_circuit(circuit_data, shots)
            elif provider == 'braket':
                return self._simulate_braket_circuit(circuit_data, shots)
            else:
                raise ValueError(f"Simulation not supported for provider: {provider}")
                
        except Exception as e:
            raise Exception(f"Circuit simulation failed: {str(e)}")
    
    def _simulate_qiskit_circuit(self, circuit_data: dict, shots: int) -> Dict:
        """Simulate circuit using Qiskit"""
        try:
            qiskit_modules = self._init_qiskit()
            if not qiskit_modules:
                raise ValueError("Qiskit not available")
            
            # Create circuit
            QuantumCircuit = qiskit_modules['QuantumCircuit']
            num_qubits = circuit_data.get('num_qubits', 2)
            qc = QuantumCircuit(num_qubits, num_qubits)
            
            # Add gates
            for gate in circuit_data.get('gates', []):
                gate_type = gate.get('type')
                if gate_type == 'h':
                    qc.h(gate['qubit'])
                elif gate_type == 'cx':
                    qc.cx(gate['control'], gate['target'])
                elif gate_type == 'x':
                    qc.x(gate['qubit'])
                elif gate_type == 'y':
                    qc.y(gate['qubit'])
                elif gate_type == 'z':
                    qc.z(gate['qubit'])
            
            # Add measurements
            measurements = circuit_data.get('measurements', list(range(num_qubits)))
            for i, qubit in enumerate(measurements):
                qc.measure(qubit, i)
            
            # Simulate
            simulator = qiskit_modules['Aer'].get_backend('qasm_simulator')
            job = simulator.run(qiskit_modules['transpile'](qc, simulator), shots=shots)
            result = job.result()
            counts = result.get_counts(qc)
            
            return {
                'counts': counts,
                'shots': shots,
                'success': True,
                'provider': 'qiskit'
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'success': False,
                'provider': 'qiskit'
            }
    
    def _simulate_cirq_circuit(self, circuit_data: dict, shots: int) -> Dict:
        """Simulate circuit using Cirq"""
        try:
            cirq = self._init_cirq()
            if not cirq:
                raise ValueError("Cirq not available")
            
            # Create qubits
            num_qubits = circuit_data.get('num_qubits', 2)
            qubits = [cirq.GridQubit(0, i) for i in range(num_qubits)]
            
            # Create circuit
            circuit = cirq.Circuit()
            
            # Add gates
            for gate in circuit_data.get('gates', []):
                gate_type = gate.get('type')
                if gate_type == 'H':
                    circuit.append(cirq.H(qubits[gate['qubit']]))
                elif gate_type == 'CNOT':
                    circuit.append(cirq.CNOT(qubits[gate['control']], qubits[gate['target']]))
                elif gate_type == 'X':
                    circuit.append(cirq.X(qubits[gate['qubit']]))
            
            # Add measurements
            circuit.append(cirq.measure(*qubits, key='result'))
            
            # Simulate
            simulator = cirq.Simulator()
            result = simulator.run(circuit, repetitions=shots)
            measurements = result.measurements['result']
            
            # Count results
            counts = {}
            for measurement in measurements:
                bit_string = ''.join(str(bit) for bit in measurement)
                counts[bit_string] = counts.get(bit_string, 0) + 1
            
            return {
                'counts': counts,
                'shots': shots,
                'success': True,
                'provider': 'cirq'
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'success': False,
                'provider': 'cirq'
            }
    
    def _simulate_braket_circuit(self, circuit_data: dict, shots: int) -> Dict:
        """Simulate circuit using AWS Braket"""
        try:
            braket_modules = self._init_braket()
            if not braket_modules:
                raise ValueError("Braket not available")
            
            # Create circuit
            Circuit = braket_modules['Circuit']
            circuit = Circuit()
            
            # Add instructions
            for instruction in circuit_data.get('instructions', []):
                gate = instruction.get('gate')
                if gate == 'h':
                    circuit.h(instruction['target'])
                elif gate == 'cnot':
                    circuit.cnot(instruction['control'], instruction['target'])
                elif gate == 'x':
                    circuit.x(instruction['target'])
            
            # Simulate
            device = braket_modules['LocalSimulator']()
            task = device.run(circuit, shots=shots)
            result = task.result()
            
            return {
                'counts': result.measurement_counts,
                'shots': shots,
                'success': True,
                'provider': 'braket'
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'success': False,
                'provider': 'braket'
            }
    
    def get_quantum_algorithms(self) -> List[Dict]:
        """Get available quantum algorithms"""
        return [
            {
                'name': 'Quantum Teleportation',
                'description': 'Transfer quantum state between qubits',
                'qubits_required': 3,
                'category': 'communication'
            },
            {
                'name': 'Grover\'s Algorithm',
                'description': 'Quantum search algorithm',
                'qubits_required': 4,
                'category': 'search'
            },
            {
                'name': 'Shor\'s Algorithm',
                'description': 'Quantum factoring algorithm',
                'qubits_required': 8,
                'category': 'cryptography'
            },
            {
                'name': 'Quantum Fourier Transform',
                'description': 'Quantum version of discrete Fourier transform',
                'qubits_required': 4,
                'category': 'mathematical'
            },
            {
                'name': 'Variational Quantum Eigensolver (VQE)',
                'description': 'Find ground state energies',
                'qubits_required': 6,
                'category': 'optimization'
            }
        ]

# Global instance
quantum_service = QuantumService()
