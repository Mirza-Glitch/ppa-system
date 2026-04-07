import uuid
import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.utils import hash_password
from flask_cors import CORS
from flask_mail import Mail
from dotenv import load_dotenv
from models.models import db, User, Role
from routes.api import api

load_dotenv()

app = Flask(__name__)


def env_bool(key, default=False):
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///database.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123')
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT', 'ppa-salt')
app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = os.getenv('SECURITY_TOKEN_AUTHENTICATION_HEADER', 'Authorization')
app.config['SECURITY_PASSWORD_HASH'] = os.getenv('SECURITY_PASSWORD_HASH', 'bcrypt')



# Flask-Mail (Required for Celery)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.mailtrap.io')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '2525'))
app.config['MAIL_USE_TLS'] = env_bool('MAIL_USE_TLS', True)
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'your-username')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'your-password')

cors_origins = [origin.strip() for origin in os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:8080').split(',') if origin.strip()]

# --- EXTENSIONS ---
# Strictly allowing the Frontend Origin
CORS(app, resources={r"/api/*": {"origins": cors_origins}}, 
     supports_credentials=True, 
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"])

db.init_app(app)
mail = Mail(app)

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Register Blueprint
app.register_blueprint(api, url_prefix='/api')


@app.get('/health')
def health_check():
    return jsonify({"status": "ok"}), 200

def setup_database():
    with app.app_context():
        db.create_all()
        
        # Create Roles
        admin_role = user_datastore.find_or_create_role(name='admin')
        user_datastore.find_or_create_role(name='company')
        user_datastore.find_or_create_role(name='student')
        
        # Create Admin with HASHED password
        if not user_datastore.find_user(email='admin@ppa.com'):
            user_datastore.create_user(
                email='admin@ppa.com', 
                password=hash_password('password123'), 
                roles=[admin_role],
                fs_uniquifier=uuid.uuid4().hex,
                active=True
            )
            db.session.commit()
            print("Admin created: admin@ppa.com / password123")

if __name__ == '__main__':
    setup_database()
    print("Backend running at http://127.0.0.1:5000")
    app.run(port=int(os.getenv('PORT', '5000')), debug=os.getenv('FLASK_ENV', 'development') == 'development')
    