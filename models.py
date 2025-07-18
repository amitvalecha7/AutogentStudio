from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    profile_image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True)
    files = db.relationship('File', backref='user', lazy=True)
    knowledge_bases = db.relationship('KnowledgeBase', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    model_provider = db.Column(db.String(50), default='openai')
    model_name = db.Column(db.String(100), default='gpt-4o')
    system_prompt = db.Column(db.Text)
    temperature = db.Column(db.Float, default=0.7)
    max_tokens = db.Column(db.Integer, default=2000)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade='all, delete-orphan')

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    metadata = db.Column(db.Text)  # JSON string for additional data
    
    def set_metadata(self, data):
        self.metadata = json.dumps(data)
    
    def get_metadata(self):
        return json.loads(self.metadata) if self.metadata else {}

class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(100), nullable=False)
    mime_type = db.Column(db.String(100))
    is_processed = db.Column(db.Boolean, default=False)
    processing_status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    knowledge_base_files = db.relationship('KnowledgeBaseFile', backref='file', lazy=True)
    chunks = db.relationship('FileChunk', backref='file', lazy=True, cascade='all, delete-orphan')

class KnowledgeBase(db.Model):
    __tablename__ = 'knowledge_bases'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    embedding_model = db.Column(db.String(100), default='text-embedding-3-small')
    chunk_size = db.Column(db.Integer, default=1000)
    chunk_overlap = db.Column(db.Integer, default=200)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    files = db.relationship('KnowledgeBaseFile', backref='knowledge_base', lazy=True)

class KnowledgeBaseFile(db.Model):
    __tablename__ = 'knowledge_base_files'
    
    id = db.Column(db.Integer, primary_key=True)
    knowledge_base_id = db.Column(db.Integer, db.ForeignKey('knowledge_bases.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

class FileChunk(db.Model):
    __tablename__ = 'file_chunks'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.LargeBinary)  # Store embedding as binary data
    metadata = db.Column(db.Text)  # JSON string for additional data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_metadata(self, data):
        self.metadata = json.dumps(data)
    
    def get_metadata(self):
        return json.loads(self.metadata) if self.metadata else {}

class Assistant(db.Model):
    __tablename__ = 'assistants'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    avatar_url = db.Column(db.String(500))
    system_prompt = db.Column(db.Text)
    model_provider = db.Column(db.String(50), default='openai')
    model_name = db.Column(db.String(100), default='gpt-4o')
    temperature = db.Column(db.Float, default=0.7)
    max_tokens = db.Column(db.Integer, default=2000)
    category = db.Column(db.String(100))
    tags = db.Column(db.Text)  # JSON array of tags
    downloads = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0.0)
    created_by = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Plugin(db.Model):
    __tablename__ = 'plugins'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    avatar_url = db.Column(db.String(500))
    repository_url = db.Column(db.String(500))
    package_manager = db.Column(db.String(50))  # 'npm', 'python', etc.
    install_command = db.Column(db.String(500))
    category = db.Column(db.String(100))
    service_type = db.Column(db.String(50))  # 'Local Service', 'Hybrid Service', etc.
    tools_count = db.Column(db.Integer, default=0)
    schema_count = db.Column(db.Integer, default=0)
    downloads = db.Column(db.Integer, default=0)
    rating = db.Column(db.String(10), default='A')  # A, B, C rating
    created_by = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ModelProvider(db.Model):
    __tablename__ = 'model_providers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255))
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(500))
    base_url = db.Column(db.String(500))
    api_key_required = db.Column(db.Boolean, default=True)
    supported_models = db.Column(db.Text)  # JSON array of models
    capabilities = db.Column(db.Text)  # JSON array of capabilities
    pricing_info = db.Column(db.Text)  # JSON object with pricing details
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    setting_key = db.Column(db.String(255), nullable=False)
    setting_value = db.Column(db.Text)
    is_encrypted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'setting_key'),)

class WorkflowExecution(db.Model):
    __tablename__ = 'workflow_executions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    workflow_name = db.Column(db.String(255), nullable=False)
    workflow_data = db.Column(db.Text)  # JSON string of workflow configuration
    status = db.Column(db.String(50), default='pending')
    result = db.Column(db.Text)
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def set_workflow_data(self, data):
        self.workflow_data = json.dumps(data)
    
    def get_workflow_data(self):
        return json.loads(self.workflow_data) if self.workflow_data else {}

class QuantumExperiment(db.Model):
    __tablename__ = 'quantum_experiments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    quantum_provider = db.Column(db.String(100))  # 'ibm', 'google', 'aws'
    circuit_data = db.Column(db.Text)  # JSON string of quantum circuit
    execution_results = db.Column(db.Text)  # JSON string of results
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FederatedLearningNode(db.Model):
    __tablename__ = 'federated_learning_nodes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    node_name = db.Column(db.String(255), nullable=False)
    node_type = db.Column(db.String(50))  # 'coordinator', 'participant'
    status = db.Column(db.String(50), default='inactive')
    endpoint_url = db.Column(db.String(500))
    capabilities = db.Column(db.Text)  # JSON string of node capabilities
    last_seen = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NeuromorphicDevice(db.Model):
    __tablename__ = 'neuromorphic_devices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    device_name = db.Column(db.String(255), nullable=False)
    device_type = db.Column(db.String(100))  # 'loihi', 'truenorth', 'spinnaker'
    status = db.Column(db.String(50), default='offline')
    configuration = db.Column(db.Text)  # JSON string of device config
    performance_metrics = db.Column(db.Text)  # JSON string of metrics
    last_active = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SafetyAssessment(db.Model):
    __tablename__ = 'safety_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assessment_type = db.Column(db.String(100), nullable=False)
    model_name = db.Column(db.String(255))
    assessment_data = db.Column(db.Text)  # JSON string of assessment details
    risk_score = db.Column(db.Float)
    recommendations = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ResearchProject(db.Model):
    __tablename__ = 'research_projects'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    research_domain = db.Column(db.String(100))
    hypothesis = db.Column(db.Text)
    methodology = db.Column(db.Text)
    progress_status = db.Column(db.String(50), default='planning')
    findings = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BlockchainTransaction(db.Model):
    __tablename__ = 'blockchain_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_hash = db.Column(db.String(255), unique=True, nullable=False)
    transaction_type = db.Column(db.String(100))  # 'plugin_purchase', 'revenue_share', etc.
    amount = db.Column(db.Numeric(precision=20, scale=8))
    token_symbol = db.Column(db.String(10))
    status = db.Column(db.String(50), default='pending')
    metadata = db.Column(db.Text)  # JSON string for additional data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
