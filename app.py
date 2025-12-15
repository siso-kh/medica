from flask import Flask
from flask_login import LoginManager
from models import db, User, Pharmacy  # Add Pharmacy import
from config import Config
import os  # Import os module


# Initialize extensions
login_manager = LoginManager()
login_manager.login_view = 'routes.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    if os.environ.get('RENDER'):  # Detect Render environment
        app.config.from_object('config.ProductionConfig')
    else:
        app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Add Pharmacy to Jinja globals for template access
    app.jinja_env.globals['Pharmacy'] = Pharmacy
    
    # Register blueprints
    from routes import bp as routes_bp
    app.register_blueprint(routes_bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

