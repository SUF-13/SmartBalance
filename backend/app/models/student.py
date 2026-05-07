from ..extensions import db
from datetime import datetime
import bcrypt

class Student(db.Model):
    __tablename__ = 'students'

    student_id = db.Column(db.String(20), primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(50))
    semester = db.Column(db.Integer)
    degree = db.Column(db.String(100))
    batch = db.Column(db.String(50))
    section = db.Column(db.String(20))
    campus = db.Column(db.String(100))

    gender = db.Column(db.String(20))
    dob = db.Column(db.String(20))
    cnic = db.Column(db.String(25))
    mobile_no = db.Column(db.String(25))
    blood_group = db.Column(db.String(10))
    nationality = db.Column(db.String(50))

    address = db.Column(db.String(255))
    home_phone = db.Column(db.String(30))
    postal_code = db.Column(db.String(20))
    city = db.Column(db.String(50))
    country = db.Column(db.String(50))

    warning_count = db.Column(db.Integer, default=0)
    credits_earned = db.Column(db.Integer, default=0)
    credits_attempted = db.Column(db.Integer, default=0)
    cgpa = db.Column(db.Numeric(3, 2))
    credit_hours_completed = db.Column(db.Integer, default=0)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    registrations = db.relationship('Registration', backref='student', lazy=True)
    request_logs = db.relationship('RequestLog', backref='student', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self):
        return {
            'student_id': self.student_id,
            'full_name': self.full_name,
            'email': self.email,
            'department': self.department,
            'semester': self.semester,
            'degree': self.degree,
            'batch': self.batch,
            'section': self.section,
            'campus': self.campus,
            'gender': self.gender,
            'dob': self.dob,
            'cnic': self.cnic,
            'mobile_no': self.mobile_no,
            'blood_group': self.blood_group,
            'nationality': self.nationality,
            'address': self.address,
            'home_phone': self.home_phone,
            'postal_code': self.postal_code,
            'city': self.city,
            'country': self.country,
            'warning_count': self.warning_count,
            'credits_earned': self.credits_earned,
            'credits_attempted': self.credits_attempted,
            'cgpa': float(self.cgpa) if self.cgpa is not None else None,
            'credit_hours_completed': self.credit_hours_completed,
            'enrolled_at': self.enrolled_at.isoformat(),
            'is_active': self.is_active
        }


