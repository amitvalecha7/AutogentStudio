import os

class Config:
    # Basic Flask config
    SECRET_KEY = os.environ.get('SESSION_SECRET') or 'autogent-studio-secret-key'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://localhost/autogent_studio'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AI Provider APIs
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'default_openai_key')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', 'default_anthropic_key')
    COHERE_API_KEY = os.environ.get('COHERE_API_KEY', 'default_cohere_key')
    
    # Quantum Computing APIs
    IBM_QUANTUM_TOKEN = os.environ.get('IBM_QUANTUM_TOKEN', 'default_ibm_token')
    GOOGLE_QUANTUM_KEY = os.environ.get('GOOGLE_QUANTUM_KEY', 'default_google_key')
    AWS_BRAKET_ACCESS_KEY = os.environ.get('AWS_BRAKET_ACCESS_KEY', 'default_braket_key')
    
    # Blockchain
    WEB3_PROVIDER_URL = os.environ.get('WEB3_PROVIDER_URL', 'https://mainnet.infura.io/v3/default')
    IPFS_GATEWAY = os.environ.get('IPFS_GATEWAY', 'https://gateway.pinata.cloud/ipfs/')
    
    # File Storage
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    
    # Security
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'autogent-studio-encryption-key')
    
    # Features
    ENABLE_QUANTUM = os.environ.get('ENABLE_QUANTUM', 'true').lower() == 'true'
    ENABLE_FEDERATED = os.environ.get('ENABLE_FEDERATED', 'true').lower() == 'true'
    ENABLE_NEUROMORPHIC = os.environ.get('ENABLE_NEUROMORPHIC', 'true').lower() == 'true'
    ENABLE_SAFETY = os.environ.get('ENABLE_SAFETY', 'true').lower() == 'true'
    ENABLE_SELF_IMPROVING = os.environ.get('ENABLE_SELF_IMPROVING', 'true').lower() == 'true'
