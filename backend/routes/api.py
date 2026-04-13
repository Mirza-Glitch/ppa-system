import csv
import io
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request, Response
from flask_security import auth_required, roles_accepted, current_user
from flask_security.utils import hash_password
from sqlalchemy import or_, func

from models.models import db, User, Role, PlacementDrive, Application

api = Blueprint('api', __name__)


def current_role(user):
    return user.roles[0].name if user.roles else None


def parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def serialize_drive(drive):
    return {
        "id": drive.id,
        "title": drive.job_title,
        "description": drive.description,
        "company": drive.company.name if drive.company else "Unknown",
        "min_cgpa": drive.criteria_cgpa,
        "branch": drive.criteria_branch,
        "year": drive.criteria_year,
        "location": drive.location,
        "package_amount": drive.package_amount,
        "deadline": drive.deadline.isoformat() if drive.deadline else None,
        "status": drive.status
    }


def serialize_application(application):
    return {
        "id": application.id,
        "status": application.status,
        "applied_at": application.applied_at.isoformat() if application.applied_at else None,
        "updated_at": application.updated_at.isoformat() if application.updated_at else None,
        "student_name": application.student.name if application.student else "Unknown",
        "student_email": application.student.email if application.student else "",
        "drive_id": application.drive.id if application.drive else None,
        "drive_title": application.drive.job_title if application.drive else "",
        "company_name": application.drive.company.name if application.drive and application.drive.company else "",
        "notes": application.notes or ""
    }


def serialize_admin_user(user):
    role = current_role(user)
    return {
        "id": user.id,
        "name": user.name or user.email,
        "email": user.email,
        "role": role,
        "active": bool(user.active),
        "is_blacklisted": not bool(user.active),
        "is_approved": bool(user.is_approved)
    }


@api.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')

    if not email or not isinstance(password, str):
        return jsonify({"message": "Email and password are required"}), 400

    if len(password.encode('utf-8')) > 72:
        return jsonify({"message": "Invalid email or password"}), 401

    user = User.query.filter_by(email=email).first()
    if not user or not user.active:
        return jsonify({"message": "Invalid email or password"}), 401

    if user.verify_and_update_password(password):
        db.session.commit()
        return jsonify({
            "token": user.get_auth_token(),
            "role": current_role(user) or 'student',
            "message": "Login successful"
        }), 200

    return jsonify({"message": "Invalid email or password"}), 401


@api.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json() or {}
    role_name = (data.get('role') or '').strip().lower()
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')

    if role_name not in {'student', 'company'}:
        return jsonify({"message": "Role must be student or company"}), 400
    if not name or not email or not isinstance(password, str):
        return jsonify({"message": "Name, email, password and role are required"}), 400
    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters"}), 400
    if len(password.encode('utf-8')) > 72:
        return jsonify({"message": "Password cannot be longer than 72 bytes"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 409

    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return jsonify({"message": "Role is not configured"}), 500

    cgpa = None
    grad_year = None
    if role_name == 'student':
        if data.get('cgpa') not in (None, ''):
            try:
                cgpa = float(data.get('cgpa'))
            except (TypeError, ValueError):
                return jsonify({"message": "CGPA must be a valid number"}), 400
        if data.get('grad_year') not in (None, ''):
            try:
                grad_year = int(data.get('grad_year'))
            except (TypeError, ValueError):
                return jsonify({"message": "Graduation year must be a valid number"}), 400

    user = User(
        email=email,
        password=hash_password(password),
        fs_uniquifier=uuid.uuid4().hex,
        active=True,
        name=name,
        is_approved=False if role_name == 'company' else True,
        cgpa=cgpa,
        branch=(data.get('branch') or '').strip() or None,
        grad_year=grad_year,
        website=(data.get('website') or '').strip() or None,
        hr_contact=(data.get('hr_contact') or '').strip() or None,
        resume_url=(data.get('resume_url') or '').strip() or None
    )
    user.roles.append(role)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": f"{role_name.title()} registered successfully",
        "is_approved": user.is_approved
    }), 201


@api.route('/admin/summary', methods=['GET'])
@auth_required('token')
@roles_accepted('admin')
def admin_summary():
    return jsonify({
        "students": User.query.join(User.roles).filter(Role.name == 'student').count(),
        "companies": User.query.join(User.roles).filter(Role.name == 'company').count(),
        "drives": PlacementDrive.query.count(),
        "applications": Application.query.count()
    })


@api.route('/admin/pending', methods=['GET'])
@auth_required('token')
@roles_accepted('admin')
def admin_pending():
    pending_companies = (
        User.query.join(User.roles)
        .filter(Role.name == 'company', User.is_approved.is_(False))
        .all()
    )
    pending_drives = PlacementDrive.query.filter_by(status='Pending').all()

    items = [
        {
            "id": company.id,
            "name": company.name or company.email,
            "subtitle": company.email,
            "type": "company"
        } for company in pending_companies
    ]
    items.extend([
        {
            "id": drive.id,
            "name": drive.job_title,
            "subtitle": drive.company.name if drive.company else "",
            "type": "drive"
        } for drive in pending_drives
    ])
    return jsonify(items)


@api.route('/admin/approve/<string:item_type>/<int:item_id>', methods=['POST'])
@auth_required('token')
@roles_accepted('admin')
def admin_approve(item_type, item_id):
    if item_type == 'company':
        company = User.query.get_or_404(item_id)
        company.is_approved = True
        company.active = True
    elif item_type == 'drive':
        drive = PlacementDrive.query.get_or_404(item_id)
        drive.status = 'Approved'
    else:
        return jsonify({"message": "Unsupported approval type"}), 400

    db.session.commit()
    return jsonify({"message": f"{item_type.title()} approved successfully"})


@api.route('/admin/reject/<string:item_type>/<int:item_id>', methods=['POST'])
@auth_required('token')
@roles_accepted('admin')
def admin_reject(item_type, item_id):
    if item_type == 'company':
        company = User.query.get_or_404(item_id)
        company.active = False
        company.is_approved = False
    elif item_type == 'drive':
        drive = PlacementDrive.query.get_or_404(item_id)
        drive.status = 'Rejected'
    else:
        return jsonify({"message": "Unsupported rejection type"}), 400

    db.session.commit()
    return jsonify({"message": f"{item_type.title()} rejected successfully"})


@api.route('/admin/users', methods=['GET'])
@auth_required('token')
@roles_accepted('admin')
def admin_users_search():
    user_type = (request.args.get('type') or '').strip().lower()
    query = (request.args.get('q') or '').strip().lower()

    if user_type not in {'student', 'company'}:
        return jsonify({"message": "type must be student or company"}), 400

    users_query = User.query.join(User.roles).filter(Role.name == user_type)

    if query:
        users_query = users_query.filter(
            or_(
                func.lower(User.name).contains(query),
                func.lower(User.email).contains(query)
            )
        )

    users = users_query.order_by(User.id.desc()).all()
    return jsonify([serialize_admin_user(user) for user in users])


@api.route('/admin/blacklist/<string:user_type>/<int:user_id>', methods=['POST'])
@auth_required('token')
@roles_accepted('admin')
def admin_blacklist_toggle(user_type, user_id):
    user_type = (user_type or '').strip().lower()
    if user_type not in {'student', 'company'}:
        return jsonify({"message": "Unsupported user type"}), 400

    target_user = User.query.get_or_404(user_id)
    target_role = current_role(target_user)
    if target_role != user_type:
        return jsonify({"message": "User type mismatch"}), 400

    data = request.get_json(silent=True) or {}
    blacklisted = data.get('blacklisted')
    if not isinstance(blacklisted, bool):
        return jsonify({"message": "blacklisted must be true or false"}), 400

    target_user.active = not blacklisted
    if user_type == 'company' and target_user.active:
        target_user.is_approved = True

    db.session.commit()

    action = 'blacklisted' if blacklisted else 'removed from blacklist'
    return jsonify({
        "message": f"{user_type.title()} {action} successfully",
        "user": serialize_admin_user(target_user)
    })


@api.route('/company/drives', methods=['GET'])
@auth_required('token')
@roles_accepted('company')
def company_drives():
    drives = PlacementDrive.query.filter_by(company_id=current_user.id).order_by(PlacementDrive.id.desc()).all()
    payload = []
    for drive in drives:
        applications = Application.query.filter_by(drive_id=drive.id).order_by(Application.id.desc()).all()
        payload.append({
            **serialize_drive(drive),
            "applicants": [serialize_application(app) for app in applications]
        })
    return jsonify({
        "company": {
            "name": current_user.name,
            "email": current_user.email,
            "website": current_user.website,
            "approved": current_user.is_approved
        },
        "drives": payload
    })


@api.route('/company/create-drive', methods=['POST'])
@auth_required('token')
@roles_accepted('company')
def create_drive():
    if not current_user.is_approved:
        return jsonify({"message": "Company is pending admin approval"}), 403

    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    description = (data.get('desc') or data.get('description') or '').strip()

    if not title or not description:
        return jsonify({"message": "Job title and description are required"}), 400

    try:
        min_cgpa = float(data.get('cgpa') or 0)
    except (TypeError, ValueError):
        return jsonify({"message": "Minimum CGPA must be a valid number"}), 400

    criteria_year = None
    if data.get('year') not in (None, ''):
        try:
            criteria_year = int(data.get('year'))
        except (TypeError, ValueError):
            return jsonify({"message": "Eligibility year must be a valid number"}), 400

    deadline = parse_datetime(data.get('deadline'))
    if deadline is None:
        deadline = datetime.utcnow()

    drive = PlacementDrive(
        company_id=current_user.id,
        job_title=title,
        description=description,
        criteria_cgpa=min_cgpa,
        criteria_branch=(data.get('branch') or '').strip() or None,
        criteria_year=criteria_year,
        location=(data.get('location') or '').strip() or None,
        package_amount=(data.get('package_amount') or '').strip() or None,
        deadline=deadline,
        status='Pending'
    )
    db.session.add(drive)
    db.session.commit()
    return jsonify({"message": "Drive created and sent for admin approval"}), 201


@api.route('/company/application/<int:application_id>/status', methods=['POST'])
@auth_required('token')
@roles_accepted('company')
def update_application_status(application_id):
    data = request.get_json() or {}
    new_status = (data.get('status') or '').strip()
    allowed = {'Applied', 'Shortlisted', 'Selected', 'Rejected'}
    if new_status not in allowed:
        return jsonify({"message": "Invalid application status"}), 400

    application = Application.query.get_or_404(application_id)
    if not application.drive or application.drive.company_id != current_user.id:
        return jsonify({"message": "You can only manage your own drive applications"}), 403

    application.status = new_status
    application.notes = (data.get('notes') or '').strip() or application.notes
    db.session.commit()
    return jsonify({"message": "Application status updated"})


@api.route('/student/profile', methods=['GET'])
@auth_required('token')
@roles_accepted('student')
def student_profile():
    return jsonify({
        "name": current_user.name,
        "email": current_user.email,
        "cgpa": current_user.cgpa,
        "branch": current_user.branch,
        "grad_year": current_user.grad_year,
        "resume_url": current_user.resume_url
    })


@api.route('/drives', methods=['GET'])
@auth_required('token')
@roles_accepted('student')
def get_drives():
    search = (request.args.get('search') or '').strip().lower()
    drives = PlacementDrive.query.filter_by(status='Approved').order_by(PlacementDrive.id.desc()).all()

    results = []
    for drive in drives:
        if search and search not in drive.job_title.lower() and search not in (drive.company.name.lower() if drive.company and drive.company.name else ''):
            continue
        results.append(serialize_drive(drive))
    return jsonify(results)


@api.route('/student/applications', methods=['GET'])
@auth_required('token')
@roles_accepted('student')
def student_applications():
    applications = Application.query.filter_by(student_id=current_user.id).order_by(Application.id.desc()).all()
    return jsonify([serialize_application(app) for app in applications])


@api.route('/student/export', methods=['GET'])
@auth_required('token')
@roles_accepted('student')
def export_student_history():
    applications = Application.query.filter_by(student_id=current_user.id).order_by(Application.id.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student Name', 'Company Name', 'Drive Title', 'Status', 'Applied At'])
    for app in applications:
        writer.writerow([
            current_user.name,
            app.drive.company.name if app.drive and app.drive.company else '',
            app.drive.job_title if app.drive else '',
            app.status,
            app.applied_at.isoformat() if app.applied_at else ''
        ])

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=placement-history.csv'
        }
    )


@api.route('/apply/<int:drive_id>', methods=['POST'])
@auth_required('token')
@roles_accepted('student')
def apply_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)

    if drive.status != 'Approved':
        return jsonify({"message": "This drive is not open for applications"}), 400

    if current_user.cgpa is not None and drive.criteria_cgpa is not None and current_user.cgpa < drive.criteria_cgpa:
        return jsonify({"message": "Ineligible: CGPA below required criteria"}), 400
    if drive.criteria_branch and current_user.branch and current_user.branch.lower() != drive.criteria_branch.lower():
        return jsonify({"message": "Ineligible: Branch does not match"}), 400
    if drive.criteria_year and current_user.grad_year and current_user.grad_year != drive.criteria_year:
        return jsonify({"message": "Ineligible: Graduation year does not match"}), 400

    existing = Application.query.filter_by(student_id=current_user.id, drive_id=drive_id).first()
    if existing:
        return jsonify({"message": "Already applied to this drive"}), 400

    application = Application(
        student_id=current_user.id,
        drive_id=drive_id,
        status='Applied'
    )
    db.session.add(application)
    db.session.commit()
    return jsonify({"message": "Applied successfully"}), 201
