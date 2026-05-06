from ..extensions import db
from datetime import datetime

class Registration(db.Model):
    __tablename__ = "registrations"
    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", name="unique_student_course"),
    )

    registration_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), db.ForeignKey("students.student_id"), nullable=False)
    course_id = db.Column(db.String(20), db.ForeignKey("courses.course_id"), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="enrolled")  # enrolled, dropped
    grade = db.Column(db.String(5))

    def to_dict(self):
        return {
            "registration_id": self.registration_id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "course_name": self.course.course_name if self.course else None,
            "credit_hours": self.course.credit_hours if self.course else None,
            "instructor": self.course.instructor if self.course else None,
            "schedule": self.course.schedule if self.course else None,
            "room": self.course.room if self.course else None,
            "registered_at": self.registered_at.isoformat(),
            "status": self.status,
            "grade": self.grade
        }