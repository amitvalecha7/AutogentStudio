from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import QuantumCircuit, db
from services.quantum_service import QuantumService
import uuid

quantum_bp = Blueprint('quantum', __name__, url_prefix='/quantum')

@quantum_bp.route('/')
@login_required
def index():
    # Get user's quantum circuits
    circuits = QuantumCircuit.query.filter_by(
        user_id=current_user.id
    ).order_by(QuantumCircuit.created_at.desc()).all()
    
    return render_template('quantum/index.html', circuits=circuits)

@quantum_bp.route('/algorithms')
@login_required
def algorithms():
    return render_template('quantum/algorithms.html')

@quantum_bp.route('/circuits')
@login_required
def circuits():
    circuits = QuantumCircuit.query.filter_by(
        user_id=current_user.id
    ).order_by(QuantumCircuit.created_at.desc()).all()
    
    return render_template('quantum/circuits.html', circuits=circuits)

@quantum_bp.route('/training')
@login_required
def training():
    return render_template('quantum/training.html')

@quantum_bp.route('/analysis')
@login_required
def analysis():
    return render_template('quantum/analysis.html')

@quantum_bp.route('/create-circuit', methods=['POST'])
@login_required
def create_circuit():
    data = request.get_json()
    
    name = data.get('name', '').strip()
    num_qubits = data.get('num_qubits', 2)
    provider = data.get('provider', 'ibm')
    
    if not name:
        return jsonify({'error': 'Circuit name is required'}), 400
    
    try:
        quantum_service = QuantumService()
        
        # Create basic circuit
        circuit_data = quantum_service.create_circuit(num_qubits, provider)
        
        circuit_id = str(uuid.uuid4())
        circuit = QuantumCircuit(
            id=circuit_id,
            user_id=current_user.id,
            name=name,
            description=data.get('description', ''),
            circuit_data=circuit_data,
            provider=provider,
            num_qubits=num_qubits,
            depth=0,
            gates_count=0
        )
        
        db.session.add(circuit)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'circuit_id': circuit_id,
            'circuit_data': circuit_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quantum_bp.route('/circuit/<circuit_id>')
@login_required
def view_circuit(circuit_id):
    circuit = QuantumCircuit.query.filter_by(
        id=circuit_id,
        user_id=current_user.id
    ).first_or_404()
    
    return render_template('quantum/circuit_detail.html', circuit=circuit)

@quantum_bp.route('/circuit/<circuit_id>/execute', methods=['POST'])
@login_required
def execute_circuit(circuit_id):
    circuit = QuantumCircuit.query.filter_by(
        id=circuit_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    backend = data.get('backend', 'qasm_simulator')
    shots = data.get('shots', 1024)
    
    try:
        quantum_service = QuantumService()
        
        # Execute circuit
        results = quantum_service.execute_circuit(
            circuit.circuit_data,
            backend=backend,
            shots=shots,
            provider=circuit.provider
        )
        
        # Update circuit with results
        circuit.execution_results = results
        db.session.commit()
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quantum_bp.route('/circuit/<circuit_id>/visualize', methods=['GET'])
@login_required
def visualize_circuit(circuit_id):
    circuit = QuantumCircuit.query.filter_by(
        id=circuit_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        quantum_service = QuantumService()
        
        # Generate circuit visualization
        visualization = quantum_service.visualize_circuit(circuit.circuit_data)
        
        return jsonify({
            'success': True,
            'visualization': visualization
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quantum_bp.route('/algorithms/grover', methods=['POST'])
@login_required
def grover_algorithm():
    data = request.get_json()
    
    marked_items = data.get('marked_items', [])
    num_qubits = data.get('num_qubits', 3)
    
    try:
        quantum_service = QuantumService()
        
        # Create Grover's algorithm circuit
        circuit_data = quantum_service.create_grover_circuit(marked_items, num_qubits)
        
        return jsonify({
            'success': True,
            'circuit_data': circuit_data,
            'algorithm': 'grover'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quantum_bp.route('/algorithms/shor', methods=['POST'])
@login_required
def shor_algorithm():
    data = request.get_json()
    
    number_to_factor = data.get('number', 15)
    
    try:
        quantum_service = QuantumService()
        
        # Create Shor's algorithm circuit
        circuit_data = quantum_service.create_shor_circuit(number_to_factor)
        
        return jsonify({
            'success': True,
            'circuit_data': circuit_data,
            'algorithm': 'shor',
            'number': number_to_factor
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quantum_bp.route('/algorithms/qft', methods=['POST'])
@login_required
def quantum_fourier_transform():
    data = request.get_json()
    
    num_qubits = data.get('num_qubits', 3)
    
    try:
        quantum_service = QuantumService()
        
        # Create QFT circuit
        circuit_data = quantum_service.create_qft_circuit(num_qubits)
        
        return jsonify({
            'success': True,
            'circuit_data': circuit_data,
            'algorithm': 'qft'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quantum_bp.route('/hybrid-classical', methods=['POST'])
@login_required
def hybrid_classical_quantum():
    data = request.get_json()
    
    problem_type = data.get('problem_type', 'optimization')
    parameters = data.get('parameters', {})
    
    try:
        quantum_service = QuantumService()
        
        # Create hybrid circuit
        circuit_data = quantum_service.create_hybrid_circuit(problem_type, parameters)
        
        return jsonify({
            'success': True,
            'circuit_data': circuit_data,
            'problem_type': problem_type
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quantum_bp.route('/providers', methods=['GET'])
@login_required
def quantum_providers():
    providers = {
        'ibm': {
            'name': 'IBM Quantum',
            'backends': ['qasm_simulator', 'ibmq_qasm_simulator', 'ibmq_lima'],
            'max_qubits': 65,
            'description': 'IBM Quantum cloud platform'
        },
        'google': {
            'name': 'Google Quantum AI',
            'backends': ['cirq_simulator', 'quantum_virtual_machine'],
            'max_qubits': 70,
            'description': 'Google Cirq quantum computing platform'
        },
        'amazon': {
            'name': 'Amazon Braket',
            'backends': ['sv1', 'tn1', 'dm1'],
            'max_qubits': 34,
            'description': 'Amazon Braket quantum computing service'
        }
    }
    
    return jsonify({
        'success': True,
        'providers': providers
    })

@quantum_bp.route('/simulate', methods=['POST'])
@login_required
def simulate_quantum():
    data = request.get_json()
    
    circuit_data = data.get('circuit_data')
    shots = data.get('shots', 1024)
    
    if not circuit_data:
        return jsonify({'error': 'Circuit data is required'}), 400
    
    try:
        quantum_service = QuantumService()
        
        # Run simulation
        results = quantum_service.simulate_circuit(circuit_data, shots)
        
        return jsonify({
            'success': True,
            'results': results,
            'shots': shots
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
