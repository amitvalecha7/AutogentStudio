from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Text, JSON, Boolean, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(String(255), primary_key=True)
    email = db.Column(String(255), unique=True, nullable=False)
    username = db.Column(String(100), unique=True, nullable=False)
    password_hash = db.Column(String(256))
    first_name = db.Column(String(100))
    last_name = db.Column(String(100))
    profile_image_url = db.Column(Text)
    is_active = db.Column(Boolean, default=True)
    role = db.Column(String(50), default='user')
    preferences = db.Column(JSON, default=dict)
    api_keys = db.Column(Text)  # Encrypted JSON
    subscription_tier = db.Column(String(50), default='free')
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    files = relationship("File", back_populates="user", cascade="all, delete-orphan")
    knowledge_bases = relationship("KnowledgeBase", back_populates="user", cascade="all, delete-orphan")
    research_projects = relationship("ResearchProject", back_populates="user", cascade="all, delete-orphan")

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    
    id = db.Column(String(255), primary_key=True)
    user_id = db.Column(String(255), ForeignKey('users.id'), nullable=False)
    title = db.Column(String(255), nullable=False)
    model_provider = db.Column(String(100))
    model_name = db.Column(String(100))
    system_prompt = db.Column(Text)
    settings = db.Column(JSON, default=dict)
    is_active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(String(255), primary_key=True)
    session_id = db.Column(String(255), ForeignKey('chat_sessions.id'), nullable=False)
    role = db.Column(String(20), nullable=False)  # user, assistant, system
    content = db.Column(Text, nullable=False)
    metadata = db.Column(JSON, default=dict)
    tokens_used = db.Column(Integer, default=0)
    cost = db.Column(Float, default=0.0)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(String(255), primary_key=True)
    user_id = db.Column(String(255), ForeignKey('users.id'), nullable=False)
    filename = db.Column(String(255), nullable=False)
    original_filename = db.Column(String(255), nullable=False)
    file_type = db.Column(String(100), nullable=False)
    file_size = db.Column(Integer, nullable=False)
    mime_type = db.Column(String(100))
    storage_path = db.Column(Text, nullable=False)
    is_processed = db.Column(Boolean, default=False)
    processing_status = db.Column(String(50), default='pending')
    metadata = db.Column(JSON, default=dict)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="files")
    embeddings = relationship("FileEmbedding", back_populates="file", cascade="all, delete-orphan")

class KnowledgeBase(db.Model):
    __tablename__ = 'knowledge_bases'
    
    id = db.Column(String(255), primary_key=True)
    user_id = db.Column(String(255), ForeignKey('users.id'), nullable=False)
    name = db.Column(String(255), nullable=False)
    description = db.Column(Text)
    settings = db.Column(JSON, default=dict)
    file_count = db.Column(Integer, default=0)
    total_chunks = db.Column(Integer, default=0)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="knowledge_bases")
    embeddings = relationship("FileEmbedding", back_populates="knowledge_base", cascade="all, delete-orphan")

class FileEmbedding(db.Model):
    __tablename__ = 'file_embeddings'
    
    id = db.Column(String(255), primary_key=True)
    file_id = db.Column(String(255), ForeignKey('files.id'), nullable=False)
    knowledge_base_id = db.Column(String(255), ForeignKey('knowledge_bases.id'))
    chunk_text = db.Column(Text, nullable=False)
    chunk_index = db.Column(Integer, nullable=False)
    embedding_model = db.Column(String(100), nullable=False)
    embedding_vector = db.Column(db.ARRAY(Float))  # pgvector
    metadata = db.Column(JSON, default=dict)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    file = relationship("File", back_populates="embeddings")
    knowledge_base = relationship("KnowledgeBase", back_populates="embeddings")

class AIModel(db.Model):
    __tablename__ = 'ai_models'
    
    id = db.Column(String(255), primary_key=True)
    name = db.Column(String(255), nullable=False)
    provider = db.Column(String(100), nullable=False)
    model_type = db.Column(String(100), nullable=False)  # chat, image, embedding
    capabilities = db.Column(JSON, default=list)  # vision, function_calling, etc.
    max_tokens = db.Column(Integer)
    cost_per_token_input = db.Column(Float)
    cost_per_token_output = db.Column(Float)
    is_active = db.Column(Boolean, default=True)
    settings = db.Column(JSON, default=dict)
    created_at = db.Column(DateTime, default=datetime.utcnow)

class Plugin(db.Model):
    __tablename__ = 'plugins'
    
    id = db.Column(String(255), primary_key=True)
    name = db.Column(String(255), nullable=False)
    description = db.Column(Text)
    category = db.Column(String(100))
    version = db.Column(String(50))
    author = db.Column(String(255))
    github_url = db.Column(Text)
    npm_package = db.Column(String(255))
    installation_type = db.Column(String(50))  # npm, python, local
    is_featured = db.Column(Boolean, default=False)
    download_count = db.Column(Integer, default=0)
    rating = db.Column(Float, default=0.0)
    settings_schema = db.Column(JSON, default=dict)
    created_at = db.Column(DateTime, default=datetime.utcnow)

class Assistant(db.Model):
    __tablename__ = 'assistants'
    
    id = db.Column(String(255), primary_key=True)
    name = db.Column(String(255), nullable=False)
    description = db.Column(Text)
    category = db.Column(String(100))
    author = db.Column(String(255))
    github_url = db.Column(Text)
    system_prompt = db.Column(Text)
    model_config = db.Column(JSON, default=dict)
    capabilities = db.Column(JSON, default=list)
    is_featured = db.Column(Boolean, default=False)
    usage_count = db.Column(Integer, default=0)
    rating = db.Column(Float, default=0.0)
    created_at = db.Column(DateTime, default=datetime.utcnow)

# Quantum Computing Models
class QuantumCircuit(db.Model):
    __tablename__ = 'quantum_circuits'
    
    id = db.Column(String(255), primary_key=True)
    user_id = db.Column(String(255), ForeignKey('users.id'), nullable=False)
    name = db.Column(String(255), nullable=False)
    description = db.Column(Text)
    circuit_data = db.Column(JSON, nullable=False)  # Qiskit/Cirq circuit definition
    provider = db.Column(String(100))  # ibm, google, amazon
    num_qubits = db.Column(Integer, nullable=False)
    depth = db.Column(Integer)
    gates_count = db.Column(Integer)
    execution_results = db.Column(JSON, default=dict)
    created_at = db.Column(DateTime, default=datetime.utcnow)

# Federated Learning Models
class FederatedNode(db.Model):
    __tablename__ = 'federated_nodes'
    
    id = db.Column(String(255), primary_key=True)
    user_id = db.Column(String(255), ForeignKey('users.id'), nullable=False)
    name = db.Column(String(255), nullable=False)
    node_type = db.Column(String(100))  # coordinator, participant
    status = db.Column(String(50), default='inactive')
    endpoint_url = db.Column(Text)
    capabilities = db.Column(JSON, default=dict)
    last_seen = db.Column(DateTime)
    created_at = db.Column(DateTime, default=datetime.utcnow)

class FederatedTrainingJob(db.Model):
    __tablename__ = 'federated_training_jobs'
    
    id = db.Column(String(255), primary_key=True)
    user_id = db.Column(String(255), ForeignKey('users.id'), nullable=False)
    name = db.Column(String(255), nullable=False)
    model_architecture = db.Column(JSON, nullable=False)
    training_config = db.Column(JSON, nullable=False)
    participating_nodes = db.Column(JSON, default=list)
    status = db.Column(String(50), default='pending')
    current_round = db.Column(Integer, default=0)
    total_rounds = db.Column(Integer, nullable=False)
    aggregation_results = db.Column(JSON, default=dict)
    created_at = db.Column(DateTime, default=datetime.utcnow)

# Neuromorphic Computing Models
class NeuromorphicDevice(db.Model):
    __tablename__ = 'neuromorphic_devices'
    
    id = db.Column(String(255), primary_key=True)
    user_id = db.Column(String(255), ForeignKey('users.id'), nullable=False)
    name = db.Column(String(255), nullable=False)
    device_type = db.Column(String(100))  # loihi, truenorth, spinnaker
    location = db.Column(String(255))
    capabilities = db.Column(JSON, default=dict)
    status = db.Column(String(50), default='offline')
    last_heartbeat = db.Column(DateTime)
    created_at = db.Column(DateTime, default=datetime.utcnow)

class SpikingNeuralNetwork(db.Model):
    __tablename__ = 'spiking_neural_networks'
    
    id = db.Column(String(255), primary_key=True)
    user_id = db.Column(String(255), ForeignKey('users.id'), nullable=False)
    name = db.Column(String(255), nullable=False)
    architecture = db.Column(JSON, nullable=False)
    neuron_model = db.Column(String(100))  # lif, izhikevich, hodgkin_huxley
    network_size = db.Column(Integer)
    deployment_target = db.Column(String(255))
    performance_metrics = db.Column(JSON, default=dict)
    created_at = db.Column(DateTime, default=datetime.utcnow)

# AI Safety Models
class SafetyProtocol(db.Model):
    __tablename__ = 'safety_protocols'
    
    id = db.Column(String(255), primary_key=True)
    name = db.Column(String(255), nullable=False)
    description = db.Column(Text)
    protocol_type = db.Column(String(100))  # alignment, robustness, interpretability
    implementation = db.Column(JSON, nullable=False)
    severity_level = db.Column(String(50))  # low, medium, high, critical
    is_active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)

class SafetyViolation(db.Model):
    __tablename__ = 'safety_violations'
    
    id = db.Column(String(255), primary_key=True)
    protocol_id = db.Column(String(255), ForeignKey('safety_protocols.id'), nullable=False)
    user_id = db.Column(String(255), ForeignKey('users.id'))
    session_id = db.Column(String(255), ForeignKey('chat_sessions.id'))
    violation_type = db.Column(String(100), nullable=False)
    severity = db.Column(String(50))
    details = db.Column(JSON, nullable=False)
    resolved = db.Column(Boolean, default=False)
    created_at = db.Column(DateTime, default=datetime.utcnow)

# Self-Improving AI Models
class ResearchProject(db.Model):
    __tablename__ = 'research_projects'
    
    id = db.Column(String(255), primary_key=True)
    user_id = db.Column(String(255), ForeignKey('users.id'), nullable=False)
    name = db.Column(String(255), nullable=False)
    description = db.Column(Text)
    research_area = db.Column(String(100))
    hypothesis = db.Column(Text)
    methodology = db.Column(JSON, default=dict)
    status = db.Column(String(50), default='active')
    progress_percentage = db.Column(Float, default=0.0)
    findings = db.Column(JSON, default=list)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="research_projects")
    experiments = relationship("Experiment", back_populates="project", cascade="all, delete-orphan")

class Experiment(db.Model):
    __tablename__ = 'experiments'
    
    id = db.Column(String(255), primary_key=True)
    project_id = db.Column(String(255), ForeignKey('research_projects.id'), nullable=False)
    name = db.Column(String(255), nullable=False)
    hypothesis = db.Column(Text)
    experimental_design = db.Column(JSON, nullable=False)
    parameters = db.Column(JSON, default=dict)
    results = db.Column(JSON, default=dict)
    status = db.Column(String(50), default='planned')
    start_time = db.Column(DateTime)
    end_time = db.Column(DateTime)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("ResearchProject", back_populates="experiments")

# Blockchain Models
class BlockchainWallet(db.Model):
    __tablename__ = 'blockchain_wallets'
    
    id = db.Column(String(255), primary_key=True)
    user_id = db.Column(String(255), ForeignKey('users.id'), nullable=False)
    wallet_address = db.Column(String(255), nullable=False)
    wallet_type = db.Column(String(100))  # metamask, walletconnect
    network = db.Column(String(100))  # ethereum, polygon, bsc
    is_active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)

class SmartContract(db.Model):
    __tablename__ = 'smart_contracts'
    
    id = db.Column(String(255), primary_key=True)
    name = db.Column(String(255), nullable=False)
    contract_address = db.Column(String(255), nullable=False)
    network = db.Column(String(100), nullable=False)
    abi = db.Column(JSON, nullable=False)
    purpose = db.Column(String(255))
    is_verified = db.Column(Boolean, default=False)
    created_at = db.Column(DateTime, default=datetime.utcnow)

# Analytics Models
class UsageMetrics(db.Model):
    __tablename__ = 'usage_metrics'
    
    id = db.Column(String(255), primary_key=True)
    user_id = db.Column(String(255), ForeignKey('users.id'))
    metric_type = db.Column(String(100), nullable=False)
    metric_name = db.Column(String(255), nullable=False)
    value = db.Column(Float, nullable=False)
    metadata = db.Column(JSON, default=dict)
    timestamp = db.Column(DateTime, default=datetime.utcnow)

# Workflow Orchestration Models
class Workflow(db.Model):
    __tablename__ = 'workflows'
    
    id = db.Column(String(255), primary_key=True)
    user_id = db.Column(String(255), ForeignKey('users.id'), nullable=False)
    name = db.Column(String(255), nullable=False)
    description = db.Column(Text)
    flow_definition = db.Column(JSON, nullable=False)  # Drawflow format
    is_active = db.Column(Boolean, default=True)
    execution_count = db.Column(Integer, default=0)
    last_execution = db.Column(DateTime)
    created_at = db.Column(DateTime, default=datetime.utcnow)

class WorkflowExecution(db.Model):
    __tablename__ = 'workflow_executions'
    
    id = db.Column(String(255), primary_key=True)
    workflow_id = db.Column(String(255), ForeignKey('workflows.id'), nullable=False)
    status = db.Column(String(50), default='running')
    input_data = db.Column(JSON, default=dict)
    output_data = db.Column(JSON, default=dict)
    execution_log = db.Column(JSON, default=list)
    start_time = db.Column(DateTime, default=datetime.utcnow)
    end_time = db.Column(DateTime)
