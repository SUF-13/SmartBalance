from ..extensions import db
from datetime import datetime

class Server(db.Model):
    __tablename__ = "servers"

    server_id = db.Column(db.String(20), primary_key=True)
    server_name = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, default=50)
    is_alive = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    request_logs = db.relationship("RequestLog", backref="server", lazy=True)

    def to_dict(self):
        return {
            "server_id": self.server_id,
            "server_name": self.server_name,
            "capacity": self.capacity,
            "is_alive": self.is_alive,
            "created_at": self.created_at.isoformat()
        }