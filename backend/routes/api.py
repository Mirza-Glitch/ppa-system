from flask import Blueprint, jsonify, request
from models.models import db, User, PlacementDrive, Application
from flask_security import auth_required, roles_accepted, current_user
from flask_security.utils import verify_password

api = Blueprint('api', __name__)

@api.route('/login', methods=['POST', 'OPTIONS'])
def login():
    # Handle CORS Pre-flight
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
        
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    # Verify using Bcrypt as per app.py config
    if user and verify_password(password, user.password):
        token = user.get_auth_token()
        role = user.roles[0].name if user.roles else 'student'
        return jsonify({
            "token": token,
            "role": role,
            "message": "Login Successful"
        }), 200
    
    return jsonify({"message": "Invalid email or password"}), 401

@api.route('/drives', methods=['GET'])
@auth_required('token')
def get_drives():
    # Requirement: Show approved drives
    drives = PlacementDrive.query.filter_by(status='Approved').all()
    return jsonify([
        {
            "id": d.id, 
            "title": d.job_title, 
            "min_cgpa": d.min_cgpa,
            "company": d.company.name if d.company else "Direct"
        } for d in drives
    ])

@api.route('/apply/<int:drive_id>', methods=['POST'])
@auth_required('token')
@roles_accepted('student')
def apply_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    # Logic: Student must meet CGPA criteria
    if current_user.cgpa < drive.min_cgpa:
        return jsonify({"message": "Ineligible: Low CGPA"}), 400
        
    # Prevent duplicate apps
    exists = Application.query.filter_by(student_id=current_user.id, drive_id=drive_id).first()
    if exists:
        return jsonify({"message": "Already Applied"}), 400
        
    new_app = Application(student_id=current_user.id, drive_id=drive_id, status='Applied')
    db.session.add(new_app)
    db.session.commit()
    return jsonify({"message": "Applied successfully!"})