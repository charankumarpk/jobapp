import os
from flask import Flask, flash, jsonify, render_template, request, redirect, session, url_for
from datetime import datetime
from flask_migrate import Migrate
from flask_session import Session
from models.Job import User, JobPortal
from utils.db import db
from sqlalchemy import or_
from werkzeug.exceptions import NotFound
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash
from flask_wtf import CSRFProtect
import scan

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///job.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'yas@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'gast ozbh ilzx mpqx'     # Replace with your app password
app.config['MAIL_DEFAULT_SENDER'] = 'yas@gmail.com'

app.secret_key = 'your_secret_key'
csrf = CSRFProtect(app)

db.init_app(app)

Session(app)

mail = Mail(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Initialize database
with app.app_context():
    db.create_all()

# Home Page
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/infoviz')
def Infoviz():
    # Your logic for the Infoviz route
    return render_template('infoviz.html')  # Or whatever page you want to display


# Home Page
@app.route('/index')
def index():
    return render_template('index.html')

# About Page
@app.route('/about')
def about():
    return render_template('about.html')

# Contact Page
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Create email content
        email_body = f"""
        New contact form submission:
        
        Name: {name}
        Email: {email}
        Subject: {subject}
        Message:
        {message}
        """
        
        try:
            # Create and send email
            msg = Message(
                subject=f"Job Portal Contact: {subject}",
                recipients=['yas@example.com'],  # Replace with your personal email
                body=email_body
            )
            mail.send(msg)
            
            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('contact'))
            
        except Exception as e:
            flash('An error occurred while sending your message. Please try again.', 'error')
            print(f"Error sending email: {str(e)}")
            
    return render_template('contact.html')

@app.route('/single-blog')
def single_blog():
    return render_template('single-blog.html')


@app.route('/scan', methods=['GET', 'POST'])
def scan_resume():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file uploaded", 400

        file = request.files['file']
        if file.filename == '':
            return "No selected file", 400

        text = scan.extract_text_from_pdf(file)  # Extract text from the uploaded PDF
        skills_set = scan.load_skills_database()  # Load pre-defined skills database
        skills = scan.extract_skills(text, skills_set)  # Extract skills from text

        return render_template('scan.html', skills=skills)  # Pass skills to template

    return render_template('scan.html')  # Show upload form



@app.route('/Job_L', methods=['GET', 'POST'])
def Job_L():
    try:
        role = session.get('role', 'user')  # Default to 'user' if no role is set
        print(f"Current role: {role}")  # Debugging output
        jobs = JobPortal.query.order_by(JobPortal.date.desc()).all()
        return render_template('Job_L.html', jobs=jobs, role=role)
    except Exception:
        flash("An error occurred while loading jobs.", "error")
        return render_template('Job_L.html', jobs=[], role='user')

@app.route('/job_details')
def job_details():
    job_id = request.args.get('id', type=int)
    job = JobPortal.query.get_or_404(job_id)
    return render_template('job_details.html', job=job)

# Upload CV Page
@app.route('/upload_cv', methods=['GET', 'POST'])
def upload_cv():
    return render_template('upload_cv.html')

# Manipulate Jobs (View All for Admin)
@app.route('/manipulate')
def manipulate():
    job = JobPortal.query.all()
    return render_template('manipulate.html', job=job)

# Submit New Job
@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Input validation
        required_fields = ['company', 'job_title', 'location', 'date']
        form_data = request.form.to_dict()
        
        for field in required_fields:
            if not form_data.get(field):
                raise ValueError(f"{field} is required")
        
        # Type conversion and validation
        company_score = float(form_data.get('company_score', 0))  # Default to 0 if missing
        salary = int(form_data.get('salary', 0))  # Default to 0 if missing
        date_obj = datetime.strptime(form_data['date'], '%Y-%m-%d').date()

        job = JobPortal(
            company=form_data['company'],
            company_score=company_score,
            job_title=form_data['job_title'],
            location=form_data['location'],
            date=date_obj,
            salary=salary
        )

        db.session.add(job)
        db.session.commit()
        flash("Job submitted successfully!", "success")
        
    except ValueError as e:
        flash(f"Invalid input: {str(e)}", "error")
        db.session.rollback()
    except Exception as e:
        flash(f"Error submitting job: {str(e)}", "error")
        db.session.rollback()
    
    return redirect('/Job_L')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def edit_job(id):
    try:
        job = JobPortal.query.get_or_404(id)
        
        if request.method == 'POST':
            try:
                # Validate required fields
                required_fields = ['company', 'job_title', 'location', 'date', 'salary', 'company_score']
                for field in required_fields:
                    if not request.form.get(field):
                        raise ValueError(f"{field} is required")
                
                # Validate and convert company score
                company_score = float(request.form['company_score'])
                if not 0 <= company_score <= 5:
                    raise ValueError("Company score must be between 0 and 5")
                
                # Validate and convert salary
                salary = int(request.form['salary'])
                if salary <= 0:
                    raise ValueError("Salary must be a positive number")
                
                # Validate and convert date
                try:
                    date_obj = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError("Invalid date format")
                
                # Update job fields
                job.company = request.form['company'].strip()
                job.company_score = company_score
                job.job_title = request.form['job_title'].strip()
                job.location = request.form['location'].strip()
                job.date = date_obj
                job.salary = salary
                
                # Commit changes
                db.session.commit()
                flash('Job updated successfully!', 'success')
                return redirect(url_for('Job_L'))
                
            except ValueError as e:
                flash(f'Validation error: {str(e)}', 'error')
                db.session.rollback()
            except Exception as e:
                flash(f'Error updating job: {str(e)}', 'error')
                db.session.rollback()
            
            return render_template('update.html', job=job)
        
        # GET request - show the form
        return render_template('update.html', job=job)
        
    except NotFound:
        flash('Job not found!', 'error')
        return redirect(url_for('Job_L'))
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('Job_L'))

# About Page
@app.route('/update')
def update():
    return render_template('update.html')

# Delete Job
@app.route('/delete/<int:id>', methods=['POST', 'DELETE'])
def delete(id):
    try:
        job = JobPortal.query.get_or_404(id)
        db.session.delete(job)
        db.session.commit()
        flash("Job deleted successfully!", "success")
        return jsonify({'message': 'Job deleted successfully'}), 200
    except Exception as e:
        flash(f"Error deleting job: {str(e)}", "error")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/apply_job/<int:id>', methods=['POST'])
def apply_job(id):
    job = JobPortal.query.get_or_404(id)
    role = session.get('role')
    if role != 'user':
        flash("Only users can apply for jobs.", "danger")
        return redirect(url_for('Job_L'))

    flash(f"Application submitted for the job: {job.job_title}", "success")
    return redirect(url_for('job_details', id=id))

@app.route('/jobs', methods=['GET'])
def get_jobs():
    try:
        sort_by = request.args.get('sort_by')
        order = request.args.get('order', 'desc')
        job_title = request.args.get('job_title', '')

        query = JobPortal.query

        if job_title:
            query = query.filter(JobPortal.job_title.ilike(f'%{job_title}%'))

        if sort_by:
            sort_column = getattr(JobPortal, sort_by)
            if order == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(JobPortal.date.desc())

        jobs = query.all()
        return jsonify([{
            'id': job.id,
            'job_title': job.job_title,
            'company': job.company,
            'location': job.location,
            'salary': job.salary,
            'date': job.date.strftime('%Y-%m-%d'),
            'company_score': job.company_score
        } for job in jobs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/set_role/<role>')
def set_role(role):
    if role in ['user', 'admin']:
        session['role'] = role
        session.modified = True  # Ensure session updates are saved
        return redirect(url_for('Job_L'))
    return redirect(url_for('home'))


# Assuming you have a `User` model and `db` for database handling
# and `User` has fields like username, email, password, role.

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print(request.method)
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            role = request.form.get('role', 'user')  # Default to 'user' if not specified

            # Debug print statements
            print(f"Received signup data - Username: {username}, Email: {email}, Role: {role}")

            # Validation checks
            if not all([username, email, password, confirm_password]):
                flash('All fields are required!', 'error')
                return render_template('signup.html')

            if password != confirm_password:
                flash('Passwords do not match!', 'error')
                return render_template('signup.html')

            # Check if user already exists
            existing_user = User.query.filter(
                or_(User.username == username, User.email == email)
            ).first()

            if existing_user:
                if existing_user.username == username:
                    flash('Username already exists!', 'error')
                else:
                    flash('Email already registered!', 'error')
                return redirect(url_for('signup'))

            # Create new user with hashed password
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')  # Corrected hashing method
            new_user = User(
                username=username.strip(),
                email=email.strip(),
                password=hashed_password,  # Pass hashed password to the model
                role=role  # Use the role passed from the form
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            print(f"Error during signup: {str(e)}")
            flash(f'An error occurred during signup: {str(e)}', 'error')
            return render_template('signup.html')

    return render_template('signup.html')


@app.route('/login', methods=['POST'])
def login():
    if request.content_type != 'application/json':
        return jsonify({"message": "Content-type must be application/json", "success": False}), 400

    data = request.get_json()
    username_or_email = data.get('username_or_email')
    password = data.get('password')

    # Dummy authentication check
    if username_or_email == "test" and password == "password":
        return jsonify({"success": True, "redirect": "/dashboard"})

    return jsonify({"message": "Invalid credentials", "success": False}), 401


@app.route('/user_index')
def user_index():
    if 'role' not in session or session['role'] != 'user':
        return redirect(url_for('login'))
    return render_template('index.html')  # User dashboard page

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('index.html')  # Admin dashboard page

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=5001,
        debug=True
    )
