from ..extensions import db
from datetime import datetime

class RequestLog(db.Model):
    __tablename__ = "request_logs"

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), db.ForeignKey("students.student_id"))
    course_id = db.Column(db.String(20), db.ForeignKey("courses.course_id"))
    server_id = db.Column(db.String(20), db.ForeignKey("servers.server_id"))
    algorithm_used = db.Column(db.String(30))
    response_time = db.Column(db.Numeric(6, 3))
    status = db.Column(db.String(20))   # success / failed / queued
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "server_id": self.server_id,
            "algorithm_used": self.algorithm_used,
            "response_time": float(self.response_time) if self.response_time else None,
            "status": self.status,
            "requested_at": self.requested_at.isoformat()
        }