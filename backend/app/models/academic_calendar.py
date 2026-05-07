from ..extensions import db


class AcademicCalendar(db.Model):
    __tablename__ = "academic_calendars"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    semester_label = db.Column(db.String(50), nullable=False)
    registration_start = db.Column(db.String(30), nullable=False)
    registration_end = db.Column(db.String(30), nullable=False)
    classes_start = db.Column(db.String(30), nullable=False)
    classes_end = db.Column(db.String(30), nullable=False)
    withdrawal_start = db.Column(db.String(30), nullable=False)
    withdrawal_end = db.Column(db.String(30), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "semester_label": self.semester_label,
            "registration_start": self.registration_start,
            "registration_end": self.registration_end,
            "classes_start": self.classes_start,
            "classes_end": self.classes_end,
            "withdrawal_start": self.withdrawal_start,
            "withdrawal_end": self.withdrawal_end,
        }
