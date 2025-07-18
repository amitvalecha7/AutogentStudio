import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # File upload configuration
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
    app.config['UPLOAD_FOLDER'] = 'uploads'
    
    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    with app.app_context():
        # Import models to ensure they're registered
        import models
        db.create_all()
        logging.info("Database tables created")
    
    return app

# Create app instance
app = create_app()
