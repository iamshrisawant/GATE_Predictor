from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os
import threading
import time
import requests

def keep_alive(app):
    """
    Background daemon that pings the application periodically
    if SELF_URL is configured in the environment.
    """
    self_url = os.getenv("SELF_URL")
    if not self_url:
        app.logger.info("SELF_URL not set. Internal keep-alive daemon disabled.")
        return

    # Normalize url
    if not self_url.endswith("/api/ping"):
        self_url = self_url.rstrip("/") + "/api/ping"
        
    app.logger.info(f"Keep-alive daemon started. Pinging {self_url} every 10 minutes.")
    
    while True:
        try:
            # 10 minutes wait
            time.sleep(600)
            res = requests.get(self_url, timeout=10)
            if res.status_code == 200:
                app.logger.debug("Keep-alive ping successful")
            else:
                app.logger.warning(f"Keep-alive ping returned status {res.status_code}")
        except Exception as e:
            app.logger.warning(f"Keep-alive ping failed: {e}")

def create_app():
    load_dotenv()
    # static_folder='static', template_folder='templates' are relative to this file's location (app/)
    # So if we move them to app/, consistent.
    app = Flask(__name__, static_folder="static", template_folder="templates")
    CORS(app)
    
    # Config
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
    
    # Init Services
    from .services.storage import StorageService
    app.storage = StorageService(app)

    from .services.email_service import init_email_service
    init_email_service(app)
    
    # Blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    # Start Keep-Alive Daemon
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        # Prevent starting thread twice during development auto-reload
        ping_thread = threading.Thread(target=keep_alive, args=(app,), daemon=True)
        ping_thread.start()
    
    return app
