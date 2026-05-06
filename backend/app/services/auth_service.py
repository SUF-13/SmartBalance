from flask_jwt_extended import create_access_token
from ..models.student import Student
from ..extensions import db

class AuthService:

    @staticmethod
    def register(data):
        """Register a new student"""
        if Student.query.filter_by(email=data["email"]).first():
            return None, "Email already registered"

        if Student.query.filter_by(student_id=data["student_id"]).first():
            return None, "Student ID already exists"

        student = Student(
            student_id=data["student_id"],
            full_name=data["full_name"],
            email=data["email"],
            department=data.get("department"),
            semester=data.get("semester", 1),
            cgpa=data.get("cgpa", 0.0),
            credit_hours_completed=data.get("credit_hours_completed", 0)
        )
        student.set_password(data["password"])

        db.session.add(student)
        db.session.commit()
        return student, None

    @staticmethod
    def login(email, password):
        """Verify credentials and return JWT token"""
        student = Student.query.filter_by(email=email).first()

        if not student or not student.check_password(password):
            return None, None, "Invalid email or password"

        if not student.is_active:
            return None, None, "Account is deactivated"

        token = create_access_token(identity=student.student_id)
        return student, token, None