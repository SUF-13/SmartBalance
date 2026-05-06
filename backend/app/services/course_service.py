from ..models.course import Course
from ..models.department import Department
from ..models.registration import Registration

class CourseService:

    @staticmethod
    def get_all_courses(dept_id=None, semester=None):
        query = Course.query.filter_by(is_active=True)
        if dept_id:
            query = query.filter_by(dept_id=dept_id)
        if semester:
            query = query.filter_by(semester=semester)
        return [c.to_dict() for c in query.all()]

    @staticmethod
    def get_course(course_id):
        course = Course.query.get(course_id)
        return course.to_dict() if course else None

    @staticmethod
    def get_departments():
        return [d.to_dict() for d in Department.query.all()]

    @staticmethod
    def is_student_registered(student_id, course_id):
        return Registration.query.filter_by(
            student_id=student_id,
            course_id=course_id,
            status="enrolled"
        ).first() is not None

    @staticmethod
    def get_student_courses(student_id):
        regs = Registration.query.filter_by(
            student_id=student_id,
            status="enrolled"
        ).all()
        return [r.to_dict() for r in regs]