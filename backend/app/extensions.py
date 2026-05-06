from flask_cors import CORS
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from flask_alchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
socketio = SocketIO()
jwt = JWTManager()

