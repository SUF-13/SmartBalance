import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import socketio

env = os.getenv("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    print(f"SmartBalance backend starting on port {port}...")
    socketio.run(app, host="0.0.0.0", port=port, debug=(env == "development"))