# Autogent Studio Specialized Services Documentation

## Table of Contents

1. [Quantum Computing Service](#quantum-computing-service)
2. [Blockchain Service](#blockchain-service)
3. [Safety Service](#safety-service)
4. [Federated Learning Service](#federated-learning-service)
5. [Neuromorphic Computing Service](#neuromorphic-computing-service)
6. [Self-Improving AI Service](#self-improving-ai-service)
7. [Orchestration Service](#orchestration-service)
8. [RAG Service](#rag-service)
9. [Usage Examples](#usage-examples)

## Quantum Computing Service

The QuantumService provides access to quantum computing capabilities through multiple providers.

### Methods

**create_circuit(user_id, name, provider, circuit_data)**
```python
def create_circuit(self, user_id: str, name: str, provider: str = 'qiskit', circuit_data: dict = None) -> str:
    """
    Create a new quantum circuit
    
    Args:
        user_id: User ID
        name: Circuit name
        provider: Quantum provider ('qiskit', 'cirq', 'braket')
        circuit_data: Circuit definition data
    
    Returns:
        Circuit ID
    
    Example:
        circuit_id = quantum_service.create_circuit(user_id, "My Quantum Circuit", "qiskit")
    """
```

**get_user_circuits(user_id)**
```python
def get_user_circuits(self, user_id: str) -> List[Dict]:
    """
    Get all quantum circuits for a user
    
    Args:
        user_id: User ID
    
    Returns:
        List of circuit dictionaries
    
    Example:
        circuits = quantum_service.get_user_circuits(user_id)
        for circuit in circuits:
            print(f"Circuit: {circuit['name']} - Provider: {circuit['provider']}")
    """
```

**simulate_circuit(circuit_id, shots)**
```python
def simulate_circuit(self, circuit_id: str, shots: int = 1024) -> Dict:
    """
    Simulate a quantum circuit
    
    Args:
        circuit_id: Circuit ID
        shots: Number of simulation shots
    
    Returns:
        Simulation results with counts and statistics
    
    Example:
        results = quantum_service.simulate_circuit(circuit_id, shots=1000)
        print(f"Results: {results['counts']}")
    """
```

**get_quantum_algorithms()**
```python
def get_quantum_algorithms(self) -> List[Dict]:
    """
    Get available quantum algorithms
    
    Returns:
        List of quantum algorithms with descriptions
    
    Example:
        algorithms = quantum_service.get_quantum_algorithms()
        for algo in algorithms:
            print(f"Algorithm: {algo['name']} - {algo['description']}")
    """
```

### Quantum Circuit Examples

**Qiskit Circuit Creation:**
```python
from services.quantum_service import QuantumService

quantum_service = QuantumService()

# Create a simple Bell state circuit
circuit_data = {
    'provider': 'qiskit',
    'circuit': {
        'qubits': 2,
        'gates': [
            {'type': 'h', 'target': 0},
            {'type': 'cx', 'control': 0, 'target': 1}
        ]
    }
}

circuit_id = quantum_service.create_circuit(user_id, "Bell State", "qiskit", circuit_data)
results = quantum_service.simulate_circuit(circuit_id, shots=1000)
```

## Blockchain Service

The BlockchainService provides blockchain integration for NFTs, smart contracts, and decentralized applications.

### Methods

**get_wallet_balance(wallet_address)**
```python
def get_wallet_balance(self, wallet_address: str) -> Dict[str, Any]:
    """
    Get wallet balance for ETH and tokens
    
    Args:
        wallet_address: Ethereum wallet address
    
    Returns:
        Dict with ETH and token balances
    
    Example:
        balance = blockchain_service.get_wallet_balance("0x1234...")
        print(f"ETH: {balance['eth_balance']}")
        print(f"Tokens: {balance['token_balances']}")
    """
```

**purchase_plugin(buyer_address, plugin_id, price)**
```python
def purchase_plugin(self, buyer_address: str, plugin_id: str, price: float) -> Dict[str, Any]:
    """
    Purchase plugin using smart contract
    
    Args:
        buyer_address: Buyer's wallet address
        plugin_id: Plugin ID to purchase
        price: Price in ETH
    
    Returns:
        Transaction details
    
    Example:
        transaction = blockchain_service.purchase_plugin(
            "0x1234...", 
            "plugin-uuid", 
            0.1
        )
        print(f"Transaction: {transaction['transaction_hash']}")
    """
```

**mint_ai_agent_nft(owner_address, agent_config, metadata)**
```python
def mint_ai_agent_nft(self, owner_address: str, agent_config: Dict[str, Any], 
                      metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mint NFT for AI agent
    
    Args:
        owner_address: NFT owner's wallet address
        agent_config: AI agent configuration
        metadata: NFT metadata
    
    Returns:
        NFT minting details
    
    Example:
        nft_result = blockchain_service.mint_ai_agent_nft(
            "0x1234...",
            {"name": "My AI Agent", "description": "Custom AI agent"},
            {"image_url": "https://example.com/image.png"}
        )
    """
```

**claim_revenue_share(creator_address)**
```python
def claim_revenue_share(self, creator_address: str) -> Dict[str, Any]:
    """
    Claim revenue share for plugin creator
    
    Args:
        creator_address: Creator's wallet address
    
    Returns:
        Revenue claim details
    
    Example:
        claim = blockchain_service.claim_revenue_share("0x1234...")
        print(f"Claimed: {claim['amount']} ETH")
    """
```

**create_smart_contract(contract_type, parameters)**
```python
def create_smart_contract(self, contract_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new smart contract
    
    Args:
        contract_type: Type of contract ('plugin_marketplace', 'revenue_sharing', etc.)
        parameters: Contract parameters
    
    Returns:
        Contract deployment details
    
    Example:
        contract = blockchain_service.create_smart_contract(
            "plugin_marketplace",
            {"owner": "0x1234...", "fee_percentage": 5}
        )
    """
```

## Safety Service

The SafetyService provides AI safety protocols and monitoring capabilities.

### Methods

**create_safety_protocol(user_id, protocol_name, protocol_type, configuration)**
```python
def create_safety_protocol(self, user_id: str, protocol_name: str, protocol_type: str, 
                          configuration: Dict = None) -> str:
    """
    Create a new AI safety protocol
    
    Args:
        user_id: User ID
        protocol_name: Name of the protocol
        protocol_type: Type of safety protocol
        configuration: Protocol configuration
    
    Returns:
        Protocol ID
    
    Example:
        protocol_id = safety_service.create_safety_protocol(
            user_id, 
            "My Safety Protocol", 
            "alignment"
        )
    """
```

**get_user_protocols(user_id)**
```python
def get_user_protocols(self, user_id: str) -> List[Dict]:
    """
    Get all safety protocols for a user
    
    Args:
        user_id: User ID
    
    Returns:
        List of protocol dictionaries
    
    Example:
        protocols = safety_service.get_user_protocols(user_id)
        for protocol in protocols:
            print(f"Protocol: {protocol['protocol_name']} - Type: {protocol['protocol_type']}")
    """
```

**monitor_ai_system(system_id, monitoring_config)**
```python
def monitor_ai_system(self, system_id: str, monitoring_config: Dict) -> Dict:
    """
    Monitor AI system for safety violations
    
    Args:
        system_id: AI system ID
        monitoring_config: Monitoring configuration
    
    Returns:
        Monitoring results
    
    Example:
        monitoring_config = {
            'alignment_checks': True,
            'bias_detection': True,
            'robustness_testing': True
        }
        results = safety_service.monitor_ai_system(system_id, monitoring_config)
    """
```

**get_safety_analytics(user_id)**
```python
def get_safety_analytics(self, user_id: str) -> Dict:
    """
    Get safety analytics for a user
    
    Args:
        user_id: User ID
    
    Returns:
        Safety analytics data
    
    Example:
        analytics = safety_service.get_safety_analytics(user_id)
        print(f"Violations: {analytics['total_violations']}")
        print(f"Risk Score: {analytics['risk_score']}")
    """
```

### Safety Protocol Types

**Alignment Protocol:**
```python
alignment_config = {
    'value_learning_enabled': True,
    'human_feedback_integration': True,
    'constitutional_ai_rules': [
        "Be helpful, harmless, and honest",
        "Respect human autonomy and dignity",
        "Avoid deception and manipulation",
        "Promote human wellbeing"
    ],
    'alignment_checks': ['intent_verification', 'value_consistency', 'outcome_evaluation'],
    'monitoring_frequency': 'real_time'
}
```

**Robustness Protocol:**
```python
robustness_config = {
    'adversarial_testing': True,
    'distribution_shift_detection': True,
    'confidence_calibration': True,
    'uncertainty_quantification': True,
    'stress_testing_enabled': True,
    'fallback_mechanisms': ['graceful_degradation', 'human_oversight', 'system_shutdown']
}
```

**Bias Detection Protocol:**
```python
bias_config = {
    'fairness_metrics': ['demographic_parity', 'equalized_odds', 'calibration'],
    'bias_monitoring': True,
    'debiasing_techniques': ['resampling', 'reweighting', 'adversarial_debiasing'],
    'protected_attributes': ['race', 'gender', 'age', 'religion'],
    'mitigation_strategies': ['preprocessing', 'inprocessing', 'postprocessing']
}
```

## Federated Learning Service

The FederatedService enables distributed machine learning across multiple nodes.

### Methods

**create_federated_node(user_id, name, node_type, endpoint_url)**
```python
def create_federated_node(self, user_id: str, name: str, node_type: str, 
                         endpoint_url: str = None) -> str:
    """
    Create a new federated learning node
    
    Args:
        user_id: User ID
        name: Node name
        node_type: Node type ('coordinator', 'participant')
        endpoint_url: Node endpoint URL
    
    Returns:
        Node ID
    
    Example:
        node_id = federated_service.create_federated_node(
            user_id, 
            "My Node", 
            "participant"
        )
    """
```

**start_federated_training(training_config)**
```python
def start_federated_training(self, training_config: Dict) -> str:
    """
    Start federated learning training
    
    Args:
        training_config: Training configuration
    
    Returns:
        Training job ID
    
    Example:
        config = {
            'model_architecture': 'resnet18',
            'participating_nodes': ['node1', 'node2'],
            'total_rounds': 10,
            'local_epochs': 5
        }
        job_id = federated_service.start_federated_training(config)
    """
```

**get_training_status(job_id)**
```python
def get_training_status(self, job_id: str) -> Dict:
    """
    Get federated training status
    
    Args:
        job_id: Training job ID
    
    Returns:
        Training status and metrics
    
    Example:
        status = federated_service.get_training_status(job_id)
        print(f"Current round: {status['current_round']}")
        print(f"Accuracy: {status['accuracy']}")
    """
```

## Neuromorphic Computing Service

The NeuromorphicService provides access to neuromorphic computing devices and spiking neural networks.

### Methods

**create_neuromorphic_device(user_id, name, device_type, location)**
```python
def create_neuromorphic_device(self, user_id: str, name: str, device_type: str, 
                              location: str = None) -> str:
    """
    Create a new neuromorphic device
    
    Args:
        user_id: User ID
        name: Device name
        device_type: Device type ('loihi', 'truenorth', 'spinnaker')
        location: Device location
    
    Returns:
        Device ID
    
    Example:
        device_id = neuromorphic_service.create_neuromorphic_device(
            user_id, 
            "My Loihi Device", 
            "loihi"
        )
    """
```

**create_spiking_neural_network(user_id, name, architecture, neuron_model)**
```python
def create_spiking_neural_network(self, user_id: str, name: str, architecture: Dict, 
                                 neuron_model: str) -> str:
    """
    Create a spiking neural network
    
    Args:
        user_id: User ID
        name: Network name
        architecture: Network architecture
        neuron_model: Neuron model ('lif', 'izhikevich', 'hodgkin_huxley')
    
    Returns:
        Network ID
    
    Example:
        architecture = {
            'layers': [784, 100, 10],
            'connectivity': 'sparse',
            'plasticity': 'stdp'
        }
        network_id = neuromorphic_service.create_spiking_neural_network(
            user_id, 
            "My SNN", 
            architecture, 
            "lif"
        )
    """
```

**deploy_network_to_device(network_id, device_id)**
```python
def deploy_network_to_device(self, network_id: str, device_id: str) -> Dict:
    """
    Deploy spiking neural network to neuromorphic device
    
    Args:
        network_id: Network ID
        device_id: Device ID
    
    Returns:
        Deployment status
    
    Example:
        deployment = neuromorphic_service.deploy_network_to_device(network_id, device_id)
        print(f"Deployment status: {deployment['status']}")
    """
```

## Self-Improving AI Service

The SelfImprovingService enables AI systems to improve themselves through various mechanisms.

### Methods

**create_self_improving_agent(user_id, name, agent_config)**
```python
def create_self_improving_agent(self, user_id: str, name: str, agent_config: Dict) -> str:
    """
    Create a self-improving AI agent
    
    Args:
        user_id: User ID
        name: Agent name
        agent_config: Agent configuration
    
    Returns:
        Agent ID
    
    Example:
        config = {
            'improvement_strategies': ['meta_learning', 'curriculum_learning', 'self_play'],
            'evaluation_metrics': ['accuracy', 'efficiency', 'robustness'],
            'improvement_threshold': 0.05
        }
        agent_id = self_improving_service.create_self_improving_agent(
            user_id, 
            "My Self-Improving Agent", 
            config
        )
    """
```

**start_improvement_cycle(agent_id)**
```python
def start_improvement_cycle(self, agent_id: str) -> str:
    """
    Start a self-improvement cycle
    
    Args:
        agent_id: Agent ID
    
    Returns:
        Cycle ID
    
    Example:
        cycle_id = self_improving_service.start_improvement_cycle(agent_id)
    """
```

**get_improvement_metrics(agent_id)**
```python
def get_improvement_metrics(self, agent_id: str) -> Dict:
    """
    Get improvement metrics for an agent
    
    Args:
        agent_id: Agent ID
    
    Returns:
        Improvement metrics
    
    Example:
        metrics = self_improving_service.get_improvement_metrics(agent_id)
        print(f"Performance improvement: {metrics['performance_improvement']}")
        print(f"Efficiency gain: {metrics['efficiency_gain']}")
    """
```

## Orchestration Service

The OrchestrationService manages complex AI workflows and multi-agent systems.

### Methods

**create_workflow(user_id, name, workflow_definition)**
```python
def create_workflow(self, user_id: str, name: str, workflow_definition: Dict) -> str:
    """
    Create a new AI workflow
    
    Args:
        user_id: User ID
        name: Workflow name
        workflow_definition: Workflow definition
    
    Returns:
        Workflow ID
    
    Example:
        workflow_def = {
            'nodes': [
                {'id': 'data_loader', 'type': 'data_input'},
                {'id': 'preprocessor', 'type': 'data_processing'},
                {'id': 'model', 'type': 'ai_model'},
                {'id': 'evaluator', 'type': 'evaluation'}
            ],
            'edges': [
                {'from': 'data_loader', 'to': 'preprocessor'},
                {'from': 'preprocessor', 'to': 'model'},
                {'from': 'model', 'to': 'evaluator'}
            ]
        }
        workflow_id = orchestration_service.create_workflow(
            user_id, 
            "My AI Pipeline", 
            workflow_def
        )
    """
```

**execute_workflow(workflow_id, input_data)**
```python
def execute_workflow(self, workflow_id: str, input_data: Dict) -> Dict:
    """
    Execute a workflow with input data
    
    Args:
        workflow_id: Workflow ID
        input_data: Input data for the workflow
    
    Returns:
        Execution results
    
    Example:
        input_data = {'dataset_path': '/path/to/data.csv'}
        results = orchestration_service.execute_workflow(workflow_id, input_data)
        print(f"Execution status: {results['status']}")
    """
```

**get_workflow_status(workflow_id)**
```python
def get_workflow_status(self, workflow_id: str) -> Dict:
    """
    Get workflow execution status
    
    Args:
        workflow_id: Workflow ID
    
    Returns:
        Workflow status and metrics
    
    Example:
        status = orchestration_service.get_workflow_status(workflow_id)
        print(f"Progress: {status['progress']}%")
        print(f"Current node: {status['current_node']}")
    """
```

## RAG Service

The RAGService provides Retrieval-Augmented Generation capabilities for enhanced AI responses.

### Methods

**create_rag_system(user_id, name, configuration)**
```python
def create_rag_system(self, user_id: str, name: str, configuration: Dict) -> str:
    """
    Create a RAG system
    
    Args:
        user_id: User ID
        name: System name
        configuration: RAG configuration
    
    Returns:
        RAG system ID
    
    Example:
        config = {
            'retriever_type': 'vector_search',
            'generator_model': 'gpt-4o',
            'embedding_model': 'text-embedding-3-small',
            'chunk_size': 1000,
            'similarity_threshold': 0.7
        }
        rag_id = rag_service.create_rag_system(user_id, "My RAG System", config)
    """
```

**add_documents_to_rag(rag_id, documents)**
```python
def add_documents_to_rag(self, rag_id: str, documents: List[Dict]) -> Dict:
    """
    Add documents to RAG system
    
    Args:
        rag_id: RAG system ID
        documents: List of documents
    
    Returns:
        Processing results
    
    Example:
        documents = [
            {'content': 'Document 1 content', 'metadata': {'source': 'file1.pdf'}},
            {'content': 'Document 2 content', 'metadata': {'source': 'file2.pdf'}}
        ]
        results = rag_service.add_documents_to_rag(rag_id, documents)
    """
```

**query_rag_system(rag_id, query, max_results)**
```python
def query_rag_system(self, rag_id: str, query: str, max_results: int = 5) -> Dict:
    """
    Query RAG system
    
    Args:
        rag_id: RAG system ID
        query: Query string
        max_results: Maximum number of results
    
    Returns:
        Query results with retrieved context and generated response
    
    Example:
        results = rag_service.query_rag_system(rag_id, "What is machine learning?", 5)
        print(f"Generated response: {results['response']}")
        print(f"Retrieved context: {results['context']}")
    """
```

## Usage Examples

### Quantum Computing Example

```python
from services.quantum_service import QuantumService

quantum_service = QuantumService()

# Create a quantum circuit
circuit_data = {
    'provider': 'qiskit',
    'circuit': {
        'qubits': 3,
        'gates': [
            {'type': 'h', 'target': 0},
            {'type': 'cx', 'control': 0, 'target': 1},
            {'type': 'cx', 'control': 1, 'target': 2},
            {'type': 'measure', 'target': [0, 1, 2]}
        ]
    }
}

circuit_id = quantum_service.create_circuit(user_id, "GHZ State", "qiskit", circuit_data)

# Simulate the circuit
results = quantum_service.simulate_circuit(circuit_id, shots=1000)
print(f"Measurement results: {results['counts']}")
```

### Blockchain Integration Example

```python
from services.blockchain_service import BlockchainService

blockchain_service = BlockchainService()

# Check wallet balance
balance = blockchain_service.get_wallet_balance("0x1234567890123456789012345678901234567890")
print(f"ETH Balance: {balance['eth_balance']}")

# Purchase a plugin
transaction = blockchain_service.purchase_plugin(
    "0x1234567890123456789012345678901234567890",
    "plugin-uuid-123",
    0.05  # 0.05 ETH
)
print(f"Transaction hash: {transaction['transaction_hash']}")

# Mint AI agent NFT
nft_result = blockchain_service.mint_ai_agent_nft(
    "0x1234567890123456789012345678901234567890",
    {
        "name": "My Custom AI Agent",
        "description": "A specialized AI agent for data analysis",
        "capabilities": ["data_processing", "visualization", "prediction"]
    },
    {
        "image_url": "https://example.com/agent-image.png",
        "attributes": {"intelligence": 85, "specialization": "data_science"}
    }
)
print(f"NFT Token ID: {nft_result['token_id']}")
```

### AI Safety Example

```python
from services.safety_service import SafetyService

safety_service = SafetyService()

# Create alignment protocol
protocol_id = safety_service.create_safety_protocol(
    user_id,
    "My Alignment Protocol",
    "alignment",
    {
        'constitutional_ai_rules': [
            "Be helpful, harmless, and honest",
            "Respect human autonomy and dignity",
            "Avoid deception and manipulation"
        ],
        'alignment_checks': ['intent_verification', 'value_consistency'],
        'monitoring_frequency': 'real_time'
    }
)

# Monitor AI system
monitoring_config = {
    'alignment_checks': True,
    'bias_detection': True,
    'robustness_testing': True,
    'confidence_threshold': 0.8
}

monitoring_results = safety_service.monitor_ai_system("system-123", monitoring_config)
print(f"Safety violations: {monitoring_results['violations']}")
print(f"Risk score: {monitoring_results['risk_score']}")
```

### Federated Learning Example

```python
from services.federated_service import FederatedService

federated_service = FederatedService()

# Create federated nodes
node1_id = federated_service.create_federated_node(user_id, "Node 1", "participant")
node2_id = federated_service.create_federated_node(user_id, "Node 2", "participant")

# Start federated training
training_config = {
    'model_architecture': 'resnet18',
    'participating_nodes': [node1_id, node2_id],
    'total_rounds': 10,
    'local_epochs': 5,
    'learning_rate': 0.001,
    'batch_size': 32
}

job_id = federated_service.start_federated_training(training_config)

# Monitor training progress
status = federated_service.get_training_status(job_id)
print(f"Current round: {status['current_round']}/{status['total_rounds']}")
print(f"Accuracy: {status['accuracy']:.4f}")
```

### Neuromorphic Computing Example

```python
from services.neuromorphic_service import NeuromorphicService

neuromorphic_service = NeuromorphicService()

# Create neuromorphic device
device_id = neuromorphic_service.create_neuromorphic_device(
    user_id,
    "My Loihi Device",
    "loihi",
    "Intel Loihi 2"
)

# Create spiking neural network
architecture = {
    'layers': [784, 256, 128, 10],  # MNIST classification
    'connectivity': 'sparse',
    'plasticity': 'stdp',
    'learning_rate': 0.01
}

network_id = neuromorphic_service.create_spiking_neural_network(
    user_id,
    "MNIST SNN",
    architecture,
    "lif"
)

# Deploy network to device
deployment = neuromorphic_service.deploy_network_to_device(network_id, device_id)
print(f"Deployment status: {deployment['status']}")
```

### Self-Improving AI Example

```python
from services.self_improving_service import SelfImprovingService

self_improving_service = SelfImprovingService()

# Create self-improving agent
agent_config = {
    'improvement_strategies': ['meta_learning', 'curriculum_learning', 'self_play'],
    'evaluation_metrics': ['accuracy', 'efficiency', 'robustness'],
    'improvement_threshold': 0.05,
    'max_improvement_cycles': 100,
    'learning_rate_adaptation': True
}

agent_id = self_improving_service.create_self_improving_agent(
    user_id,
    "My Self-Improving Agent",
    agent_config
)

# Start improvement cycle
cycle_id = self_improving_service.start_improvement_cycle(agent_id)

# Get improvement metrics
metrics = self_improving_service.get_improvement_metrics(agent_id)
print(f"Performance improvement: {metrics['performance_improvement']:.4f}")
print(f"Efficiency gain: {metrics['efficiency_gain']:.4f}")
print(f"Robustness improvement: {metrics['robustness_improvement']:.4f}")
```

### Orchestration Example

```python
from services.orchestration_service import OrchestrationService

orchestration_service = OrchestrationService()

# Create AI workflow
workflow_definition = {
    'nodes': [
        {'id': 'data_loader', 'type': 'data_input', 'config': {'source': 'csv'}},
        {'id': 'preprocessor', 'type': 'data_processing', 'config': {'normalize': True}},
        {'id': 'model', 'type': 'ai_model', 'config': {'model_type': 'transformer'}},
        {'id': 'evaluator', 'type': 'evaluation', 'config': {'metrics': ['accuracy', 'f1']}}
    ],
    'edges': [
        {'from': 'data_loader', 'to': 'preprocessor'},
        {'from': 'preprocessor', 'to': 'model'},
        {'from': 'model', 'to': 'evaluator'}
    ]
}

workflow_id = orchestration_service.create_workflow(
    user_id,
    "My AI Pipeline",
    workflow_definition
)

# Execute workflow
input_data = {
    'dataset_path': '/path/to/dataset.csv',
    'model_config': {'epochs': 10, 'batch_size': 32}
}

results = orchestration_service.execute_workflow(workflow_id, input_data)
print(f"Execution status: {results['status']}")
print(f"Final accuracy: {results['metrics']['accuracy']}")
```

### RAG System Example

```python
from services.rag_service import RAGService

rag_service = RAGService()

# Create RAG system
rag_config = {
    'retriever_type': 'vector_search',
    'generator_model': 'gpt-4o',
    'embedding_model': 'text-embedding-3-small',
    'chunk_size': 1000,
    'similarity_threshold': 0.7,
    'max_context_length': 4000
}

rag_id = rag_service.create_rag_system(user_id, "My Knowledge Base", rag_config)

# Add documents
documents = [
    {
        'content': 'Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.',
        'metadata': {'source': 'ml_intro.pdf', 'topic': 'machine_learning'}
    },
    {
        'content': 'Deep learning uses neural networks with multiple layers to model complex patterns in data.',
        'metadata': {'source': 'deep_learning.pdf', 'topic': 'deep_learning'}
    }
]

rag_service.add_documents_to_rag(rag_id, documents)

# Query the RAG system
results = rag_service.query_rag_system(
    rag_id,
    "What is the difference between machine learning and deep learning?",
    max_results=3
)

print(f"Generated response: {results['response']}")
print(f"Retrieved context: {results['context']}")
```

This documentation provides comprehensive coverage of all specialized services in the Autogent Studio platform, including detailed method descriptions, parameter explanations, return values, and practical usage examples for each service.