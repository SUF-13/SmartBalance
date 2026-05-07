from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
socketio = SocketIO()
jwt = JWTManager()

# Basic rate limiting for security/reliability
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])