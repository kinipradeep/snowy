import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def create_app():
    # Create the app
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Configure the database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize the app with the extension
    db.init_app(app)
    
    # Register blueprints
    from auth import auth_bp
    from contacts import contacts_bp
    from groups import groups_bp
    from templates_mgmt import templates_bp
    from users import users_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(contacts_bp, url_prefix='/contacts')
    app.register_blueprint(groups_bp, url_prefix='/groups')
    app.register_blueprint(templates_bp, url_prefix='/templates')
    app.register_blueprint(users_bp, url_prefix='/users')
    
    # Import main routes to register them with the app
    import main
    
    with app.app_context():
        # Import models to ensure tables are created
        import models
        db.create_all()
        logging.info("Database tables created")
    
    return app

# Create app instance
app = create_app()
