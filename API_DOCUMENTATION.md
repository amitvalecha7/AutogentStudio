# Autogent Studio API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Application Structure](#application-structure)
3. [Database Models](#database-models)
4. [Core Services](#core-services)
5. [API Routes](#api-routes)
6. [Utility Functions](#utility-functions)
7. [Configuration](#configuration)
8. [WebSocket Events](#websocket-events)
9. [Usage Examples](#usage-examples)

## Overview

Autogent Studio is a comprehensive AI development platform that provides chat, file management, knowledge base creation, quantum computing, federated learning, neuromorphic computing, and blockchain integration capabilities.

## Application Structure

### Main Application (`app.py`)

The main Flask application factory that initializes all components:

```python
from app import create_app

app = create_app()
```

**Key Components:**
- Flask application with SQLAlchemy database
- SocketIO for real-time communication
- Redis for session management
- Blueprint registration for modular routing

## Database Models

### User Model

```python
class User(UserMixin, db.Model):
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
```

**Usage:**
```python
# Create a new user
user = User(
    id=str(uuid.uuid4()),
    email="user@example.com",
    username="username",
    first_name="John",
    last_name="Doe"
)

# Query user
user = User.query.filter_by(email="user@example.com").first()
```

### ChatSession Model

```python
class ChatSession(db.Model):
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
```

### ChatMessage Model

```python
class ChatMessage(db.Model):
    id = db.Column(String(255), primary_key=True)
    session_id = db.Column(String(255), ForeignKey('chat_sessions.id'), nullable=False)
    role = db.Column(String(20), nullable=False)  # user, assistant, system
    content = db.Column(Text, nullable=False)
    metadata = db.Column(JSON, default=dict)
    tokens_used = db.Column(Integer, default=0)
    cost = db.Column(Float, default=0.0)
    created_at = db.Column(DateTime, default=datetime.utcnow)
```

### File Model

```python
class File(db.Model):
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
```

### KnowledgeBase Model

```python
class KnowledgeBase(db.Model):
    id = db.Column(String(255), primary_key=True)
    user_id = db.Column(String(255), ForeignKey('users.id'), nullable=False)
    name = db.Column(String(255), nullable=False)
    description = db.Column(Text)
    settings = db.Column(JSON, default=dict)
    file_count = db.Column(Integer, default=0)
    total_chunks = db.Column(Integer, default=0)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Core Services

### AIService

The main AI service that handles interactions with various AI providers.

#### Methods

**chat_completion(messages, provider, model, settings)**
```python
def chat_completion(self, messages: List[Dict], provider: str = 'openai', 
                   model: str = None, settings: Dict = None) -> Dict:
    """
    Generate chat completion using specified AI provider
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        provider: AI provider ('openai', 'anthropic', 'google', 'cohere')
        model: Model name (defaults to latest for each provider)
        settings: Additional settings (temperature, max_tokens, etc.)
    
    Returns:
        Dict with 'content', 'model', 'tokens_used', 'cost'
    
    Example:
        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant'},
            {'role': 'user', 'content': 'Hello, how are you?'}
        ]
        response = ai_service.chat_completion(messages, 'openai', 'gpt-4o')
    """
```

**stream_chat_completion(messages, provider, model, settings)**
```python
def stream_chat_completion(self, messages: List[Dict], provider: str = 'openai', 
                          model: str = None, settings: Dict = None) -> Generator[Dict, None, None]:
    """
    Stream chat completion responses
    
    Args:
        messages: List of message dictionaries
        provider: AI provider
        model: Model name
        settings: Additional settings
    
    Yields:
        Dict with streaming content chunks
    
    Example:
        for chunk in ai_service.stream_chat_completion(messages, 'openai'):
            print(chunk['content'], end='', flush=True)
    """
```

**generate_image_openai(prompt, size, quality, n)**
```python
def generate_image_openai(self, prompt: str, size: str = "1024x1024", 
                         quality: str = "standard", n: int = 1) -> Dict:
    """
    Generate images using OpenAI DALL-E
    
    Args:
        prompt: Text description of the image
        size: Image size ('1024x1024', '1024x1792', '1792x1024')
        quality: Image quality ('standard', 'hd')
        n: Number of images to generate
    
    Returns:
        Dict with image URLs and metadata
    """
```

**get_embedding(text, model)**
```python
def get_embedding(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    Get text embedding using OpenAI's embedding model
    
    Args:
        text: Text to embed
        model: Embedding model name
    
    Returns:
        List of float values representing the embedding
    """
```

### ChatService

Manages chat sessions and message handling.

#### Methods

**create_session(user_id, title, model)**
```python
def create_session(self, user_id: str, title: str = None, model: str = 'gpt-4o') -> str:
    """
    Create a new chat session
    
    Args:
        user_id: User ID
        title: Session title (auto-generated if None)
        model: AI model to use
    
    Returns:
        Session ID
    
    Example:
        session_id = chat_service.create_session(user_id, "My Chat Session")
    """
```

**get_session(session_id, user_id)**
```python
def get_session(self, session_id: str, user_id: str) -> dict:
    """
    Get chat session with all messages
    
    Args:
        session_id: Session ID
        user_id: User ID for authorization
    
    Returns:
        Dict with session info and messages
    
    Example:
        session_data = chat_service.get_session(session_id, user_id)
        for message in session_data['messages']:
            print(f"{message['role']}: {message['content']}")
    """
```

**add_message(session_id, role, content, model_used, tokens_used)**
```python
def add_message(self, session_id: str, role: str, content: str, 
                model_used: str = None, tokens_used: int = None) -> str:
    """
    Add a message to a chat session
    
    Args:
        session_id: Session ID
        role: Message role ('user', 'assistant', 'system')
        content: Message content
        model_used: AI model used for this message
        tokens_used: Number of tokens used
    
    Returns:
        Message ID
    
    Example:
        message_id = chat_service.add_message(session_id, 'user', 'Hello AI!')
    """
```

**chat_completion(session_id, user_message, model, provider)**
```python
def chat_completion(self, session_id: str, user_message: str, 
                   model: str = 'gpt-4o', provider: str = 'openai') -> dict:
    """
    Generate AI response and save to session
    
    Args:
        session_id: Session ID
        user_message: User's message
        model: AI model to use
        provider: AI provider
    
    Returns:
        Dict with AI response and metadata
    
    Example:
        response = chat_service.chat_completion(session_id, "What is AI?", 'gpt-4o')
        print(response['content'])
    """
```

### FileService

Handles file upload, processing, and management.

#### Methods

**upload_file(user_id, file)**
```python
def upload_file(self, user_id: str, file: FileStorage) -> dict:
    """
    Upload and process a file
    
    Args:
        user_id: User ID
        file: FileStorage object from Flask
    
    Returns:
        Dict with file info and status
    
    Example:
        from flask import request
        file = request.files['file']
        result = file_service.upload_file(user_id, file)
        print(f"Uploaded: {result['filename']}")
    """
```

**get_user_files(user_id)**
```python
def get_user_files(self, user_id: str) -> List[Dict]:
    """
    Get all files for a user
    
    Args:
        user_id: User ID
    
    Returns:
        List of file dictionaries
    
    Example:
        files = file_service.get_user_files(user_id)
        for file in files:
            print(f"{file['filename']} - {file['file_size']} bytes")
    """
```

**delete_file(file_id, user_id)**
```python
def delete_file(self, file_id: str, user_id: str) -> bool:
    """
    Delete a file
    
    Args:
        file_id: File ID
        user_id: User ID for authorization
    
    Returns:
        True if successful
    
    Example:
        success = file_service.delete_file(file_id, user_id)
        if success:
            print("File deleted successfully")
    """
```

### VectorService

Manages vector embeddings and knowledge base operations.

#### Methods

**create_embeddings(text_chunks, model)**
```python
def create_embeddings(self, text_chunks: List[str], model: str = None) -> List[List[float]]:
    """
    Create embeddings for text chunks
    
    Args:
        text_chunks: List of text strings
        model: Embedding model name
    
    Returns:
        List of embedding vectors
    
    Example:
        chunks = ["Hello world", "How are you?"]
        embeddings = vector_service.create_embeddings(chunks)
    """
```

**chunk_text(text, chunk_size, overlap)**
```python
def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """
    Split text into chunks with overlap
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk
        overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    
    Example:
        chunks = vector_service.chunk_text(long_text, chunk_size=1000, overlap=200)
    """
```

**search_knowledge_base(knowledge_base, query, limit, similarity_threshold)**
```python
def search_knowledge_base(self, knowledge_base: KnowledgeBase, query: str, 
                         limit: int = 5, similarity_threshold: float = 0.7) -> List[Dict]:
    """
    Search knowledge base for relevant content
    
    Args:
        knowledge_base: KnowledgeBase object
        query: Search query
        limit: Maximum number of results
        similarity_threshold: Minimum similarity score
    
    Returns:
        List of relevant documents with scores
    
    Example:
        results = vector_service.search_knowledge_base(kb, "machine learning", limit=10)
        for result in results:
            print(f"Score: {result['score']}, Content: {result['content']}")
    """
```

## API Routes

### Chat Routes (`/api/chat/`)

**GET /api/chat/conversations**
```python
# Get all conversations for the current user
# Returns: List of conversation objects
```

**POST /api/chat/conversations**
```python
# Create a new conversation
# Body: {
#   "title": "Conversation Title",
#   "system_prompt": "You are a helpful assistant",
#   "model_provider": "openai",
#   "model_name": "gpt-4o"
# }
# Returns: Created conversation object
```

**GET /api/chat/conversations/<conversation_id>/messages**
```python
# Get all messages in a conversation
# Returns: List of message objects
```

**POST /api/chat/conversations/<conversation_id>/messages**
```python
# Send a message in a conversation
# Body: {
#   "content": "User message",
#   "model": "gpt-4o",
#   "provider": "openai"
# }
# Returns: AI response with message details
```

### File Routes (`/api/files/`)

**POST /api/files/upload**
```python
# Upload a file
# Form data: file (multipart/form-data)
# Returns: File upload result
```

**GET /api/files**
```python
# Get all files for the current user
# Returns: List of file objects
```

**DELETE /api/files/<file_id>**
```python
# Delete a file
# Returns: Success status
```

### Knowledge Base Routes (`/api/knowledge/`)

**POST /api/knowledge/bases**
```python
# Create a new knowledge base
# Body: {
#   "name": "Knowledge Base Name",
#   "description": "Description"
# }
# Returns: Created knowledge base object
```

**GET /api/knowledge/bases**
```python
# Get all knowledge bases for the current user
# Returns: List of knowledge base objects
```

**POST /api/knowledge/bases/<kb_id>/search**
```python
# Search knowledge base
# Body: {
#   "query": "Search query",
#   "limit": 5,
#   "similarity_threshold": 0.7
# }
# Returns: Search results
```

## Utility Functions

### Security Functions

**generate_secure_token(length)**
```python
def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token
    
    Args:
        length: Token length
    
    Returns:
        Secure random token
    
    Example:
        token = generate_secure_token(32)
    """
```

**generate_api_key()**
```python
def generate_api_key() -> str:
    """
    Generate a secure API key
    
    Returns:
        API key with 'ask_' prefix
    
    Example:
        api_key = generate_api_key()
        # Returns: "ask_abc123..."
    """
```

**hash_password(password, salt)**
```python
def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
    """
    Hash password with salt using PBKDF2
    
    Args:
        password: Plain text password
        salt: Salt (generated if None)
    
    Returns:
        Dict with 'hash' and 'salt'
    
    Example:
        result = hash_password("mypassword")
        stored_hash = result['hash']
        salt = result['salt']
    """
```

**verify_password(password, stored_hash, salt)**
```python
def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """
    Verify password against stored hash
    
    Args:
        password: Plain text password
        stored_hash: Stored password hash
        salt: Salt used for hashing
    
    Returns:
        True if password matches
    
    Example:
        is_valid = verify_password("mypassword", stored_hash, salt)
    """
```

### File Utility Functions

**format_file_size(size_bytes)**
```python
def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted size string
    
    Example:
        size_str = format_file_size(1024)
        # Returns: "1.0 KB"
    """
```

**get_file_type_icon(filename)**
```python
def get_file_type_icon(filename: str) -> str:
    """
    Get icon class for file type
    
    Args:
        filename: File name
    
    Returns:
        FontAwesome icon class
    
    Example:
        icon = get_file_type_icon("document.pdf")
        # Returns: "fas fa-file-pdf text-danger"
    """
```

**calculate_file_hash(file_path, algorithm)**
```python
def calculate_file_hash(file_path: str, algorithm: str = "md5") -> str:
    """
    Calculate file hash
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
    
    Returns:
        File hash string
    
    Example:
        file_hash = calculate_file_hash("/path/to/file.txt", "sha256")
    """
```

### Text Utility Functions

**truncate_text(text, max_length, suffix)**
```python
def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    
    Example:
        short_text = truncate_text("Very long text here", 10)
        # Returns: "Very long..."
    """
```

**format_datetime(dt, format_str)**
```python
def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object
    
    Args:
        dt: Datetime object
        format_str: Format string
    
    Returns:
        Formatted datetime string
    
    Example:
        formatted = format_datetime(datetime.now(), "%Y-%m-%d")
        # Returns: "2024-01-15"
    """
```

**time_ago(dt)**
```python
def time_ago(dt: datetime) -> str:
    """
    Get human readable time ago string
    
    Args:
        dt: Datetime object
    
    Returns:
        Time ago string
    
    Example:
        ago = time_ago(datetime.now() - timedelta(hours=2))
        # Returns: "2 hours ago"
    """
```

## Configuration

### Environment Variables

The application uses the following environment variables:

```python
# Database
DATABASE_URL = "postgresql://localhost/autogent_studio"

# Session
SESSION_SECRET = "your-secret-key"
REDIS_URL = "redis://localhost:6379"

# AI Providers
OPENAI_API_KEY = "your-openai-key"
ANTHROPIC_API_KEY = "your-anthropic-key"
COHERE_API_KEY = "your-cohere-key"
GOOGLE_API_KEY = "your-google-key"

# Quantum Computing
IBM_QUANTUM_TOKEN = "your-ibm-token"
GOOGLE_QUANTUM_KEY = "your-google-quantum-key"
AWS_BRAKET_ACCESS_KEY = "your-braket-key"

# Blockchain
WEB3_PROVIDER_URL = "https://mainnet.infura.io/v3/your-key"
IPFS_GATEWAY = "https://gateway.pinata.cloud/ipfs/"

# File Storage
UPLOAD_FOLDER = "uploads"
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

# Security
ENCRYPTION_KEY = "your-encryption-key"

# Features
ENABLE_QUANTUM = "true"
ENABLE_FEDERATED = "true"
ENABLE_NEUROMORPHIC = "true"
ENABLE_SAFETY = "true"
ENABLE_SELF_IMPROVING = "true"
```

## WebSocket Events

### Chat Events

**join_conversation**
```javascript
// Join a conversation room
socket.emit('join_conversation', {
    conversation_id: 'conversation-uuid'
});
```

**leave_conversation**
```javascript
// Leave a conversation room
socket.emit('leave_conversation', {
    conversation_id: 'conversation-uuid'
});
```

**send_message**
```javascript
// Send a message
socket.emit('send_message', {
    conversation_id: 'conversation-uuid',
    content: 'Hello AI!',
    model: 'gpt-4o',
    provider: 'openai'
});
```

**message_received**
```javascript
// Listen for incoming messages
socket.on('message_received', function(data) {
    console.log('New message:', data.content);
});
```

**typing_indicator**
```javascript
// Send typing indicator
socket.emit('typing_indicator', {
    conversation_id: 'conversation-uuid',
    is_typing: true
});

// Listen for typing indicators
socket.on('user_typing', function(data) {
    console.log('User is typing:', data.user_id);
});
```

## Usage Examples

### Basic Chat Implementation

```python
from services.chat_service import ChatService
from services.ai_service import AIService

# Initialize services
chat_service = ChatService()
ai_service = AIService()

# Create a new chat session
session_id = chat_service.create_session(user_id, "My AI Chat")

# Send a message and get AI response
response = chat_service.chat_completion(
    session_id=session_id,
    user_message="What is artificial intelligence?",
    model="gpt-4o",
    provider="openai"
)

print(f"AI Response: {response['content']}")
```

### File Upload and Processing

```python
from services.file_service import FileService
from services.vector_service import VectorService

# Initialize services
file_service = FileService()
vector_service = VectorService()

# Upload a file
with open('document.pdf', 'rb') as f:
    file_storage = FileStorage(f)
    result = file_service.upload_file(user_id, file_storage)

# Create knowledge base
kb_id = file_service.create_knowledge_base(user_id, "My Documents")

# Search knowledge base
results = vector_service.search_knowledge_base(
    knowledge_base=kb,
    query="machine learning algorithms",
    limit=5
)

for result in results:
    print(f"Relevance: {result['score']}")
    print(f"Content: {result['content']}")
```

### AI Service Usage

```python
from services.ai_service import AIService

ai_service = AIService()

# Chat completion
messages = [
    {'role': 'system', 'content': 'You are a helpful assistant'},
    {'role': 'user', 'content': 'Explain quantum computing'}
]

response = ai_service.chat_completion(
    messages=messages,
    provider='openai',
    model='gpt-4o',
    settings={'temperature': 0.7, 'max_tokens': 1000}
)

print(f"Response: {response['content']}")
print(f"Tokens used: {response['tokens_used']}")
print(f"Cost: ${response['cost']:.4f}")

# Generate image
image_result = ai_service.generate_image_openai(
    prompt="A futuristic AI robot in a laboratory",
    size="1024x1024",
    quality="hd"
)

print(f"Image URL: {image_result['url']}")

# Get embeddings
text = "This is a sample text for embedding"
embedding = ai_service.get_embedding(text, "text-embedding-3-small")
print(f"Embedding dimension: {len(embedding)}")
```

### WebSocket Chat Implementation

```javascript
// Connect to WebSocket
const socket = io();

// Join a conversation
socket.emit('join_conversation', {
    conversation_id: 'conversation-uuid'
});

// Send a message
function sendMessage(content) {
    socket.emit('send_message', {
        conversation_id: 'conversation-uuid',
        content: content,
        model: 'gpt-4o',
        provider: 'openai'
    });
}

// Listen for AI responses
socket.on('message_received', function(data) {
    if (data.role === 'assistant') {
        displayMessage(data.content);
    }
});

// Listen for typing indicators
socket.on('user_typing', function(data) {
    showTypingIndicator(data.user_id);
});

// Send typing indicator
function sendTypingIndicator(isTyping) {
    socket.emit('typing_indicator', {
        conversation_id: 'conversation-uuid',
        is_typing: isTyping
    });
}
```

### Database Operations

```python
from models import User, ChatSession, ChatMessage
from app import db

# Create a new user
user = User(
    id=str(uuid.uuid4()),
    email="user@example.com",
    username="username",
    first_name="John",
    last_name="Doe"
)
db.session.add(user)
db.session.commit()

# Create a chat session
session = ChatSession(
    id=str(uuid.uuid4()),
    user_id=user.id,
    title="My Chat Session",
    model_name="gpt-4o",
    model_provider="openai"
)
db.session.add(session)
db.session.commit()

# Add messages
message = ChatMessage(
    id=str(uuid.uuid4()),
    session_id=session.id,
    role="user",
    content="Hello AI!",
    tokens_used=5
)
db.session.add(message)
db.session.commit()

# Query messages
messages = ChatMessage.query.filter_by(session_id=session.id).order_by(ChatMessage.created_at).all()
for msg in messages:
    print(f"{msg.role}: {msg.content}")
```

This documentation provides a comprehensive overview of all public APIs, functions, and components in the Autogent Studio application. Each section includes detailed explanations, parameter descriptions, return values, and practical usage examples.