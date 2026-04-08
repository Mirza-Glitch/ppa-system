from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, Company, PlacementDrive, Application

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'gate_project_secret_key'
db.init_app(app)

# 1. Programmatic Database & Admin Creation
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', password='adminpassword', role='admin')
        db.session.add(admin_user)
        db.session.commit()
        print("Admin created: User=admin, Pass=adminpassword")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        display_name = request.form.get('display_name')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        if role == 'company':
            new_company = Company(name=display_name, user_id=new_user.id, status='Pending')
            db.session.add(new_company)
            db.session.commit()
            flash('Company registered! Awaiting Admin approval.', 'info')
        else:
            flash('Student registered successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username, password=password).first()
    
    if user:
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        if user.role == 'admin':
            return redirect(url_for('admin_dash'))
        elif user.role == 'company':
            comp = Company.query.filter_by(user_id=user.id).first()
            if comp and comp.status == 'Approved':
                return redirect(url_for('comp_dash'))
            flash('Company account pending approval.', 'warning')
        elif user.role == 'student':
            return redirect(url_for('stud_dash'))
            
    flash('Invalid credentials', 'danger')
    return redirect(url_for('index'))

# --- ADMIN ROUTES ---
@app.route('/admin/dashboard')
def admin_dash():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    stats = {'students': User.query.filter_by(role='student').count(),
             'companies': Company.query.count(),
             'drives': PlacementDrive.query.count(),
             'apps': Application.query.count()}
    pending_comps = Company.query.filter_by(status='Pending').all()
    pending_drives = PlacementDrive.query.filter_by(status='Pending').all()
    return render_template('admin_dash.html', stats=stats, pending_companies=pending_comps, pending_drives=pending_drives)

@app.route('/admin/approve/company/<int:id>')
def approve_company(id):
    comp = Company.query.get(id)
    if comp: comp.status = 'Approved'
    db.session.commit()
    return redirect(url_for('admin_dash'))

@app.route('/admin/reject/company/<int:id>')
def reject_company(id):
    comp = Company.query.get(id)
    if comp: comp.status = 'Rejected'
    db.session.commit()
    return redirect(url_for('admin_dash'))

@app.route('/admin/approve/drive/<int:id>')
def approve_drive(id):
    drive = PlacementDrive.query.get(id)
    if drive: drive.status = 'Approved'
    db.session.commit()
    return redirect(url_for('admin_dash'))

# --- COMPANY ROUTES ---
@app.route('/company/dashboard')
def comp_dash():
    comp = Company.query.filter_by(user_id=session.get('user_id')).first()
    drives = PlacementDrive.query.filter_by(company_id=comp.id).all()
    return render_template('comp_dash.html', my_drives=drives)

@app.route('/create-drive', methods=['GET', 'POST'])
def create_drive():
    if request.method == 'POST':
        comp = Company.query.filter_by(user_id=session['user_id']).first()
        drive = PlacementDrive(company_id=comp.id, job_title=request.form.get('job_title'), 
                               description=request.form.get('description'), criteria=request.form.get('criteria'))
        db.session.add(drive)
        db.session.commit()
        return redirect(url_for('comp_dash'))
    return render_template('create_drive.html')

# --- STUDENT ROUTES ---
@app.route('/student/dashboard')
def stud_dash():
    drives = PlacementDrive.query.filter_by(status='Approved').all()
    apps = Application.query.filter_by(student_id=session.get('user_id')).all()
    return render_template('stud_dash.html', approved_drives=drives, my_apps=apps)

@app.route('/apply/<int:drive_id>', methods=['POST'])
def apply(drive_id):
    new_app = Application(student_id=session['user_id'], drive_id=drive_id)
    db.session.add(new_app)
    db.session.commit()
    flash('Applied successfully!', 'success')
    return redirect(url_for('stud_dash'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)