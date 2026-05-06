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
            'cgpa': float(self.cgpa) if self.cgpa is not None else None,
            'credit_hours_completed': self.credit_hours_completed,
            'enrolled_at': self.enrolled_at.isoformat(),
            'is_active': self.is_active
        }


