from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin

db = SQLAlchemy()

roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    active = db.Column(db.Boolean(), default=True)
    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic')
    )

    name = db.Column(db.String(255))
    is_approved = db.Column(db.Boolean(), default=False)
    cgpa = db.Column(db.Float, nullable=True)
    branch = db.Column(db.String(120), nullable=True)
    grad_year = db.Column(db.Integer, nullable=True)
    website = db.Column(db.String(255), nullable=True)
    hr_contact = db.Column(db.String(255), nullable=True)
    resume_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    job_title = db.Column(db.String(255))
    description = db.Column(db.Text)
    criteria_cgpa = db.Column(db.Float)
    criteria_branch = db.Column(db.String(120), nullable=True)
    criteria_year = db.Column(db.Integer, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    package_amount = db.Column(db.String(120), nullable=True)
    deadline = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    company = db.relationship('User', foreign_keys=[company_id])


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'))
    status = db.Column(db.String(50), default='Applied')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    notes = db.Column(db.Text, nullable=True)
    student = db.relationship('User', foreign_keys=[student_id])
    drive = db.relationship('PlacementDrive', foreign_keys=[drive_id])
