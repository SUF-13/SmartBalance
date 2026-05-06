from ..extensions import db

class Department(db.Model):
    __tablename__ = "departments"

    dept_id = db.Column(db.String(10), primary_key=True)
    dept_name = db.Column(db.String(100), nullable=False)
    faculty_count = db.Column(db.Integer, default=0)

   
    courses = db.relationship("Course", backref="department_obj", lazy=True)

    def to_dict(self):
        return {
            "dept_id": self.dept_id,
            "dept_name": self.dept_name,
            "faculty_count": self.faculty_count
        }