from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

def create_app():
    load_dotenv()
    # static_folder='static', template_folder='templates' are relative to this file's location (app/)
    # So if we move them to app/, consistent.
    app = Flask(__name__, static_folder="static", template_folder="templates")
    CORS(app)
    
    # Config
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
    
    # Init Services
    from .services.email_service import init_email_service
    init_email_service(app)
    
    # Blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
