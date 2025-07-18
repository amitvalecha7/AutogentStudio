from flask import Blueprint, render_template, request, jsonify, session
from app import db
from models import User, QuantumCircuit, QuantumJob
from blueprints.auth import login_required, get_current_user
from services.quantum_service import QuantumService
import logging
import json

quantum_bp = Blueprint('quantum', __name__)

@quantum_bp.route('/')
@login_required
def quantum_index():
    user = get_current_user()
    circuits = QuantumCircuit.query.filter_by(user_id=user.id).order_by(QuantumCircuit.created_at.desc()).limit(10).all()
    jobs = QuantumJob.query.filter_by(user_id=user.id).order_by(QuantumJob.created_at.desc()).limit(10).all()
    
    return render_template('quantum/dashboard.html', 
                         user=user, 
                         circuits=circuits, 
                         jobs=jobs)

@quantum_bp.route('/algorithms')
@login_required
def quantum_algorithms():
    user = get_current_user()
    
    # Predefined quantum algorithms
    algorithms = [
        {
            'name': 'Grover\'s Algorithm',
            'description': 'Quantum search algorithm for unsorted databases',
            'complexity': 'O(√N)',
            'qubits_required': '4-20',
            'category': 'Search'
        },
        {
            'name': 'Shor\'s Algorithm',
            'description': 'Quantum algorithm for integer factorization',
            'complexity': 'O(log³N)',
            'qubits_required': '100+',
            'category': 'Cryptography'
        },
        {
            'name': 'Quantum Fourier Transform',
            'description': 'Quantum version of discrete Fourier transform',
            'complexity': 'O(n²)',
            'qubits_required': '4-16',
            'category': 'Mathematical'
        },
        {
            'name': 'Variational Quantum Eigensolver',
            'description': 'Hybrid algorithm for finding ground states',
            'complexity': 'Variable',
            'qubits_required': '4-50',
            'category': 'Optimization'
        },
        {
            'name': 'Quantum Approximate Optimization',
            'description': 'Algorithm for combinatorial optimization problems',
            'complexity': 'O(p·m)',
            'qubits_required': '4-100',
            'category': 'Optimization'
        }
    ]
    
    return render_template('quantum/algorithms.html', 
                         user=user, 
                         algorithms=algorithms)

@quantum_bp.route('/circuits')
@login_required
def quantum_circuits():
    user = get_current_user()
    circuits = QuantumCircuit.query.filter_by(user_id=user.id).order_by(QuantumCircuit.created_at.desc()).all()
    
    return render_template('quantum/circuits.html', 
                         user=user, 
                         circuits=circuits)

@quantum_bp.route('/circuits/create', methods=['POST'])
@login_required
def create_circuit():
    user = get_current_user()
    data = request.get_json()
    
    name = data.get('name')
    circuit_data = data.get('circuit_data')
    provider = data.get('provider', 'qiskit')
    
    if not name or not circuit_data:
        return jsonify({'error': 'Circuit name and data are required'}), 400
    
    try:
        circuit = QuantumCircuit(
            user_id=user.id,
            name=name,
            circuit_data=json.dumps(circuit_data),
            provider=provider
        )
        
        db.session.add(circuit)
        db.session.commit()
        
        logging.info(f"Quantum circuit created: {circuit.id}")
        return jsonify({
            'success': True,
            'circuit_id': circuit.id,
            'message': 'Quantum circuit created successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating quantum circuit: {str(e)}")
        return jsonify({'error': 'Failed to create quantum circuit'}), 500

@quantum_bp.route('/circuits/<int:circuit_id>/execute', methods=['POST'])
@login_required
def execute_circuit(circuit_id):
    user = get_current_user()
    circuit = QuantumCircuit.query.filter_by(id=circuit_id, user_id=user.id).first_or_404()
    
    data = request.get_json()
    shots = data.get('shots', 1024)
    backend = data.get('backend', 'simulator')
    
    try:
        quantum_service = QuantumService()
        job_result = quantum_service.execute_circuit(
            circuit_data=json.loads(circuit.circuit_data),
            provider=circuit.provider,
            shots=shots,
            backend=backend
        )
        
        # Save job record
        job = QuantumJob(
            user_id=user.id,
            circuit_id=circuit_id,
            job_id=job_result.get('job_id', ''),
            status='running',
            result_data=json.dumps(job_result)
        )
        
        db.session.add(job)
        db.session.commit()
        
        logging.info(f"Quantum circuit executed: {circuit_id}")
        return jsonify({
            'success': True,
            'job_id': job.id,
            'quantum_job_id': job_result.get('job_id', ''),
            'status': 'running'
        })
    
    except Exception as e:
        logging.error(f"Error executing quantum circuit: {str(e)}")
        return jsonify({'error': 'Failed to execute quantum circuit'}), 500

@quantum_bp.route('/training')
@login_required
def quantum_training():
    user = get_current_user()
    return render_template('quantum/training.html', user=user)

@quantum_bp.route('/analysis')
@login_required
def quantum_analysis():
    user = get_current_user()
    return render_template('quantum/analysis.html', user=user)

@quantum_bp.route('/jobs/<int:job_id>/status')
@login_required
def get_job_status(job_id):
    user = get_current_user()
    job = QuantumJob.query.filter_by(id=job_id, user_id=user.id).first_or_404()
    
    try:
        quantum_service = QuantumService()
        status = quantum_service.get_job_status(job.job_id)
        
        # Update job status if changed
        if status != job.status:
            job.status = status
            db.session.commit()
        
        return jsonify({
            'job_id': job.id,
            'quantum_job_id': job.job_id,
            'status': status,
            'created_at': job.created_at.isoformat()
        })
    
    except Exception as e:
        logging.error(f"Error getting job status: {str(e)}")
        return jsonify({'error': 'Failed to get job status'}), 500

@quantum_bp.route('/jobs/<int:job_id>/results')
@login_required
def get_job_results(job_id):
    user = get_current_user()
    job = QuantumJob.query.filter_by(id=job_id, user_id=user.id).first_or_404()
    
    if job.status != 'completed':
        return jsonify({'error': 'Job not completed yet'}), 400
    
    try:
        if job.result_data:
            results = json.loads(job.result_data)
            return jsonify({
                'job_id': job.id,
                'results': results,
                'status': job.status
            })
        else:
            return jsonify({'error': 'No results available'}), 404
    
    except Exception as e:
        logging.error(f"Error getting job results: {str(e)}")
        return jsonify({'error': 'Failed to get job results'}), 500

@quantum_bp.route('/providers')
@login_required
def get_quantum_providers():
    """Get available quantum computing providers"""
    providers = [
        {
            'id': 'qiskit',
            'name': 'IBM Qiskit',
            'description': 'IBM Quantum Experience and Qiskit',
            'simulators': ['aer_simulator', 'statevector_simulator'],
            'hardware': ['ibmq_lima', 'ibmq_belem', 'ibmq_quito'],
            'max_qubits': 127
        },
        {
            'id': 'cirq',
            'name': 'Google Cirq',
            'description': 'Google Quantum AI and Cirq',
            'simulators': ['cirq_simulator'],
            'hardware': ['sycamore'],
            'max_qubits': 70
        },
        {
            'id': 'braket',
            'name': 'Amazon Braket',
            'description': 'Amazon Braket Quantum Computing',
            'simulators': ['local_simulator'],
            'hardware': ['rigetti', 'ionq', 'oxford'],
            'max_qubits': 32
        }
    ]
    
    return jsonify({'providers': providers})
