import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_session import Session
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import redis

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    
    # App configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "autogent-studio-secret-key")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "postgresql://localhost/autogent_studio")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Session configuration
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_REDIS'] = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'autogent:'
    
    # File upload configuration
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
    
    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
    Session(app)
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.chat import chat_bp
    from blueprints.files import files_bp
    from blueprints.image import image_bp
    from blueprints.discover import discover_bp
    from blueprints.settings import settings_bp
    from blueprints.api import api_bp
    from blueprints.quantum import quantum_bp
    from blueprints.federated import federated_bp
    from blueprints.neuromorphic import neuromorphic_bp
    from blueprints.safety import safety_bp
    from blueprints.self_improving import self_improving_bp
    from blueprints.orchestration import orchestration_bp
    from blueprints.blockchain import blockchain_bp
    from blueprints.analytics import analytics_bp
    from blueprints.marketplace import marketplace_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(discover_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(quantum_bp)
    app.register_blueprint(federated_bp)
    app.register_blueprint(neuromorphic_bp)
    app.register_blueprint(safety_bp)
    app.register_blueprint(self_improving_bp)
    app.register_blueprint(orchestration_bp)
    app.register_blueprint(blockchain_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(marketplace_bp)
    
    # Main route
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')
    
    # Create database tables
    with app.app_context():
        import models  # noqa: F401
        db.create_all()
        logging.info("Autogent Studio database tables created")
    
    return app

# Create the app instance
app = create_app()
