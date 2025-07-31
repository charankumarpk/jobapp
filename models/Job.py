from utils.db import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import validates
import re
from datetime import datetime

class JobPortal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    company_score = db.Column(db.Integer, nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    salary = db.Column(db.Integer, nullable=False)

    @validates('company_score')
    def validate_company_score(self, key, value):
        if value < 0 or value > 5:
            raise ValueError("Company score must be between 0 and 5.")
        return value
    
    def __init__(self, company, company_score, job_title, location, date, salary):
        self.company = company
        self.company_score = company_score
        self.job_title = job_title
        self.location = location
        self.date = date
        self.salary = salary

    def to_dict(self):
        return {
            'id': self.id,
            'company': self.company,
            'company_score': self.company_score,
            'job_title': self.job_title,
            'location': self.location,
            'date': self.date.strftime('%Y-%m-%d'),
            'salary': self.salary,
        }


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)  # Make sure password field exists
    role = db.Column(db.String(50), nullable=False, default='user')

    def __init__(self, username, email, password, role):
        self.username = username
        self.email = email
        self.password = password
        self.role = role

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @validates('email')
    def validate_email(self, key, email):
        # Basic email validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email address")
        return email

    @validates('username')
    def validate_username(self, key, username):
        # Username validation: 3-20 characters, alphanumeric
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
            raise ValueError("Username must be 3-20 characters long and contain only letters, numbers, and underscores")
        return username
    
# Add this model to your models.py
class FailedLoginAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<FailedLoginAttempt {self.user_id} {self.timestamp}>'