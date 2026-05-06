from ..extensions import db
from datetime import datetime

class TrafficLog(db.Model):
    __tablename__ = "traffic_logs"

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    requests_count = db.Column(db.Integer, nullable=False)
    active_connections  = db.Column(db.Integer, default=0)
    algorithm_used = db.Column(db.String(30))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "requests_count": self.requests_count,
            "active_connections": self.active_connections,
            "algorithm_used": self.algorithm_used,
            "recorded_at": self.recorded_at.isoformat()
        }