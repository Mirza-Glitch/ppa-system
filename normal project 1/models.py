from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False) # Admin, Company, Student

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(100))
    status = db.Column(db.String(20), default='Pending') # Pending/Approved [cite: 59]
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    job_title = db.Column(db.String(100), nullable=False) #[cite: 39]
    description = db.Column(db.Text)# [cite: 40]
    criteria = db.Column(db.String(200)) #[cite: 41]
    status = db.Column(db.String(20), default='Pending') # Pending/Approved [cite: 43]

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'))
    status = db.Column(db.String(20), default='Applied') #[cite: 52]


    