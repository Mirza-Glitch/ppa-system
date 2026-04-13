import os
import uuid
from datetime import datetime, timedelta

from flask import Flask, jsonify
from flask_cors import CORS
from flask_mail import Mail
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.utils import hash_password
from dotenv import load_dotenv
from sqlalchemy import inspect, text

from models.models import db, User, Role, PlacementDrive
from routes.api import api

load_dotenv()

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, 'instance', 'database.db')


def env_bool(key, default=False):
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'SQLALCHEMY_DATABASE_URI',
    f"sqlite:///{DEFAULT_DB_PATH.replace(os.sep, '/')}"
)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123')
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT', 'ppa-salt')
app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = os.getenv(
    'SECURITY_TOKEN_AUTHENTICATION_HEADER',
    'Authorization'
)
app.config['SECURITY_PASSWORD_HASH'] = os.getenv('SECURITY_PASSWORD_HASH', 'bcrypt')

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.mailtrap.io')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '2525'))
app.config['MAIL_USE_TLS'] = env_bool('MAIL_USE_TLS', True)
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'your-username')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'your-password')

cors_origins = [
    o.strip() for o in os.getenv(
        'CORS_ORIGINS',
        'http://localhost:5173,http://localhost:8080'
    ).split(',') if o.strip()
]

CORS(
    app,
    resources={r"/*": {"origins": cors_origins}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "X-XSRF-TOKEN"],
    methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"]
)

db.init_app(app)
mail = Mail(app)
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

app.register_blueprint(api, url_prefix='/api')


@app.get('/health')
def health_check():
    return jsonify({"status": "ok"}), 200


@app.route('/')
def index():
    return "hello"


def ensure_sqlite_columns():
    if not app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
        return

    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())
    alterations = {
        'user': {
            'branch': 'ALTER TABLE user ADD COLUMN branch VARCHAR(120)',
            'grad_year': 'ALTER TABLE user ADD COLUMN grad_year INTEGER',
            'website': 'ALTER TABLE user ADD COLUMN website VARCHAR(255)',
            'hr_contact': 'ALTER TABLE user ADD COLUMN hr_contact VARCHAR(255)',
            'resume_url': 'ALTER TABLE user ADD COLUMN resume_url VARCHAR(255)',
            'created_at': 'ALTER TABLE user ADD COLUMN created_at DATETIME'
        },
        'placement_drive': {
            'criteria_branch': 'ALTER TABLE placement_drive ADD COLUMN criteria_branch VARCHAR(120)',
            'criteria_year': 'ALTER TABLE placement_drive ADD COLUMN criteria_year INTEGER',
            'location': 'ALTER TABLE placement_drive ADD COLUMN location VARCHAR(255)',
            'package_amount': 'ALTER TABLE placement_drive ADD COLUMN package_amount VARCHAR(120)',
            'created_at': 'ALTER TABLE placement_drive ADD COLUMN created_at DATETIME'
        },
        'application': {
            'applied_at': 'ALTER TABLE application ADD COLUMN applied_at DATETIME',
            'updated_at': 'ALTER TABLE application ADD COLUMN updated_at DATETIME',
            'notes': 'ALTER TABLE application ADD COLUMN notes TEXT'
        }
    }

    for table_name, columns in alterations.items():
        if table_name not in existing_tables:
            continue
        existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
        for column_name, ddl in columns.items():
            if column_name not in existing_columns:
                db.session.execute(text(ddl))
        db.session.commit()


def seed_admin():
    admin_role = user_datastore.find_or_create_role(name='admin')
    user_datastore.find_or_create_role(name='company')
    user_datastore.find_or_create_role(name='student')

    admin_user = user_datastore.find_user(email='admin@ppa.com')
    if not admin_user:
        user_datastore.create_user(
            email='admin@ppa.com',
            password=hash_password('password123'),
            roles=[admin_role],
            fs_uniquifier=uuid.uuid4().hex,
            active=True,
            name='Placement Admin',
            is_approved=True
        )
        db.session.commit()
        print("Admin created: admin@ppa.com / password123")
        return

    admin_user.password = hash_password('password123')
    admin_user.active = True
    admin_user.name = admin_user.name or 'Placement Admin'
    admin_user.is_approved = True
    if admin_role not in admin_user.roles:
        admin_user.roles.append(admin_role)
    db.session.commit()
    print("Admin password reset: admin@ppa.com / password123")


def seed_demo_data():
    company_role = Role.query.filter_by(name='company').first()
    student_role = Role.query.filter_by(name='student').first()

    if company_role and not User.query.filter_by(email='hr@demo-company.com').first():
        company = User(
            email='hr@demo-company.com',
            password=hash_password('password123'),
            fs_uniquifier=uuid.uuid4().hex,
            active=True,
            name='Demo Company',
            website='https://demo-company.example.com',
            hr_contact='hr@demo-company.com',
            is_approved=True
        )
        company.roles.append(company_role)
        db.session.add(company)
        db.session.commit()

    if student_role and not User.query.filter_by(email='student@demo.com').first():
        student = User(
            email='student@demo.com',
            password=hash_password('password123'),
            fs_uniquifier=uuid.uuid4().hex,
            active=True,
            name='Demo Student',
            cgpa=8.5,
            branch='CSE',
            grad_year=2026,
            is_approved=True
        )
        student.roles.append(student_role)
        db.session.add(student)
        db.session.commit()

    company = User.query.filter_by(email='hr@demo-company.com').first()
    if company and not PlacementDrive.query.filter_by(job_title='Software Engineer Intern').first():
        drive = PlacementDrive(
            company_id=company.id,
            job_title='Software Engineer Intern',
            description='Work on product engineering and internal tools.',
            criteria_cgpa=7.0,
            criteria_branch='CSE',
            criteria_year=2026,
            location='Remote',
            package_amount='8 LPA',
            deadline=datetime.utcnow() + timedelta(days=15),
            status='Approved'
        )
        db.session.add(drive)
        db.session.commit()


def setup_database():
    with app.app_context():
        db.create_all()
        ensure_sqlite_columns()
        seed_admin()
        seed_demo_data()


if __name__ == '__main__':
    setup_database()
    print("Backend running at http://127.0.0.1:5000")
    app.run(port=int(os.getenv('PORT', '5000')), debug=True)
