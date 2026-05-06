from ..extensions import db
from datetime import datetime

class Course(db.Model):
    __tablename__ = "courses"
 
    course_id = db.Column(db.String(20), primary_key=True)
    course_name = db.Column(db.String(100), nullable=False)
    dept_id = db.Column(db.String(10), db.ForeignKey("departments.dept_id"))
    credit_hours = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Integer)
    seats_total = db.Column(db.Integer, nullable=False)
    seats_filled = db.Column(db.Integer, default=0)
    instructor = db.Column(db.String(100))
    schedule = db.Column(db.String(100))
    room = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
 

    registrations = db.relationship("Registration", backref="course", lazy=True)
    request_logs = db.relationship("RequestLog", backref="course", lazy=True)
 
    @property
    def seats_available(self):
        return self.seats_total - self.seats_filled
 
    @property
    def is_full(self):
        return self.seats_filled >= self.seats_total
 
    def to_dict(self):
        return {
            "course_id": self.course_id,
            "course_name": self.course_name,
            "dept_id": self.dept_id,
            "credit_hours": self.credit_hours,
            "semester": self.semester,
            "seats_total": self.seats_total,
            "seats_filled": self.seats_filled,
            "seats_available": self.seats_available,
            "is_full": self.is_full,
            "instructor": self.instructor,
            "schedule": self.schedule,
            "room": self.room,
            "is_active": self.is_active
        }