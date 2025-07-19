from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from app import db
from models import User, QuantumCircuit
from services.quantum_service import QuantumService
import logging

quantum_bp = Blueprint('quantum', __name__)

@quantum_bp.route('/quantum')
def quantum_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    circuits = QuantumCircuit.query.filter_by(user_id=user.id).order_by(QuantumCircuit.created_at.desc()).limit(10).all()
    
    return render_template('quantum/quantum.html', user=user, circuits=circuits)

@quantum_bp.route('/quantum/algorithms')
def quantum_algorithms():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('quantum/algorithms.html', user=user)

@quantum_bp.route('/quantum/circuits')
def quantum_circuits():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    circuits = QuantumCircuit.query.filter_by(user_id=user.id).order_by(QuantumCircuit.created_at.desc()).all()
    
    return render_template('quantum/circuits.html', user=user, circuits=circuits)

@quantum_bp.route('/quantum/training')
def quantum_training():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('quantum/training.html', user=user)

@quantum_bp.route('/quantum/analysis')
def quantum_analysis():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('quantum/analysis.html', user=user)

@quantum_bp.route('/api/quantum/circuits', methods=['GET', 'POST'])
def api_circuits():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            circuit_data = data.get('circuit_data', {})
            backend = data.get('backend', 'qiskit')
            
            if not name:
                return jsonify({'error': 'Circuit name is required'}), 400
            
            circuit = QuantumCircuit(
                user_id=user.id,
                name=name,
                description=description,
                circuit_data=circuit_data,
                backend=backend
            )
            
            db.session.add(circuit)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'circuit': circuit.to_dict()
            })
            
        except Exception as e:
            logging.error(f"Error creating quantum circuit: {str(e)}")
            return jsonify({'error': 'Failed to create circuit'}), 500
    
    # GET request
    circuits = QuantumCircuit.query.filter_by(user_id=user.id).order_by(QuantumCircuit.created_at.desc()).all()
    return jsonify({
        'success': True,
        'circuits': [circuit.to_dict() for circuit in circuits]
    })

@quantum_bp.route('/api/quantum/circuits/<circuit_id>/execute', methods=['POST'])
def execute_circuit(circuit_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        circuit = QuantumCircuit.query.filter_by(id=circuit_id, user_id=user.id).first()
        
        if not circuit:
            return jsonify({'error': 'Circuit not found'}), 404
        
        data = request.get_json()
        shots = data.get('shots', 1024)
        backend_name = data.get('backend', 'qasm_simulator')
        
        # Execute quantum circuit
        quantum_service = QuantumService()
        result = quantum_service.execute_circuit(
            circuit.circuit_data,
            backend_name=backend_name,
            shots=shots
        )
        
        # Update execution count
        circuit.execution_count += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'result': result,
            'circuit': circuit.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Error executing quantum circuit: {str(e)}")
        return jsonify({'error': f'Failed to execute circuit: {str(e)}'}), 500

@quantum_bp.route('/api/quantum/backends')
def get_backends():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        quantum_service = QuantumService()
        backends = quantum_service.get_available_backends()
        
        return jsonify({
            'success': True,
            'backends': backends
        })
        
    except Exception as e:
        logging.error(f"Error getting quantum backends: {str(e)}")
        return jsonify({'error': 'Failed to get backends'}), 500

@quantum_bp.route('/api/quantum/algorithms')
def get_algorithms():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Quantum algorithms templates
    algorithms = [
        {
            'name': 'Grover\'s Algorithm',
            'description': 'Quantum search algorithm for unstructured databases',
            'category': 'Search',
            'qubits': 3,
            'complexity': 'O(√N)',
            'template': {
                'gates': ['H', 'Oracle', 'Diffusion'],
                'iterations': 'π/4 * √N'
            }
        },
        {
            'name': 'Shor\'s Algorithm',
            'description': 'Quantum algorithm for integer factorization',
            'category': 'Cryptography',
            'qubits': 'log₂(N)',
            'complexity': 'O((log N)³)',
            'template': {
                'gates': ['QFT', 'Modular Exponentiation', 'Inverse QFT'],
                'steps': ['Period Finding', 'Classical Post-processing']
            }
        },
        {
            'name': 'Quantum Approximate Optimization Algorithm (QAOA)',
            'description': 'Hybrid quantum-classical algorithm for optimization',
            'category': 'Optimization',
            'qubits': 'Problem dependent',
            'complexity': 'Variable',
            'template': {
                'gates': ['RX', 'RZ', 'CNOT'],
                'parameters': ['β', 'γ']
            }
        },
        {
            'name': 'Variational Quantum Eigensolver (VQE)',
            'description': 'Quantum algorithm for finding ground state energies',
            'category': 'Chemistry',
            'qubits': 'System dependent',
            'complexity': 'Variable',
            'template': {
                'gates': ['RY', 'RZ', 'CNOT'],
                'ansatz': 'Hardware-efficient'
            }
        }
    ]
    
    return jsonify({
        'success': True,
        'algorithms': algorithms
    })

@quantum_bp.route('/api/quantum/simulate', methods=['POST'])
def simulate_quantum():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        algorithm_name = data.get('algorithm', '')
        parameters = data.get('parameters', {})
        
        if not algorithm_name:
            return jsonify({'error': 'Algorithm name is required'}), 400
        
        quantum_service = QuantumService()
        result = quantum_service.simulate_algorithm(algorithm_name, parameters)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logging.error(f"Error simulating quantum algorithm: {str(e)}")
        return jsonify({'error': f'Simulation failed: {str(e)}'}), 500

@quantum_bp.route('/api/quantum/optimize', methods=['POST'])
def quantum_optimize():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        problem_type = data.get('problem_type', '')
        problem_data = data.get('problem_data', {})
        
        if not problem_type:
            return jsonify({'error': 'Problem type is required'}), 400
        
        quantum_service = QuantumService()
        result = quantum_service.quantum_optimization(problem_type, problem_data)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logging.error(f"Error in quantum optimization: {str(e)}")
        return jsonify({'error': f'Optimization failed: {str(e)}'}), 500
