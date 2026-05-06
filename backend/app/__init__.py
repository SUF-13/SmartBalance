from __future__ import annotations

import os

from flask import Flask, jsonify
from sqlalchemy import text

from .config import config as config_map
from .extensions import cors, db, migrate, socketio


def _ensure_db_ready(app: Flask) -> None:
    """
    Make the project runnable without manual DB setup.
    - Creates tables (SQLite) if they don't exist.
    - If the configured DB is unreachable (e.g. Postgres not running),
      automatically falls back to local SQLite.
    """
    uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    if not uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///smartbalance.db"
        uri = app.config["SQLALCHEMY_DATABASE_URI"]

    try:
        # Smoke-check connectivity before touching models.
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        # Fallback to SQLite so the app still runs.
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///smartbalance.db"
        db.engine.dispose()

    with app.app_context():
        db.create_all()


def _seed_data() -> None:
    # Import inside app context to avoid circular imports.
    from .models.department import Department
    from .models.course import Course

    if Department.query.first():
        return

    departments = [
        Department(dept_id="CS", dept_name="Computer Science", faculty_count=25),
        Department(dept_id="SE", dept_name="Software Engineering", faculty_count=18),
        Department(dept_id="EE", dept_name="Electrical Engineering", faculty_count=22),
    ]
    db.session.add_all(departments)

    courses = [
        Course(course_id="CS101", course_name="Programming Fundamentals", dept_id="CS", credit_hours=3, semester=1,
               seats_total=40, instructor="Dr. A. Khan", schedule="Mon/Wed 10:00-11:30", room="C-101"),
        Course(course_id="CS201", course_name="Data Structures", dept_id="CS", credit_hours=3, semester=3,
               seats_total=35, instructor="Dr. S. Ali", schedule="Tue/Thu 09:00-10:30", room="C-202"),
        Course(course_id="SE210", course_name="Software Design", dept_id="SE", credit_hours=3, semester=3,
               seats_total=30, instructor="Dr. M. Noor", schedule="Mon/Wed 12:00-13:30", room="S-110"),
        Course(course_id="EE102", course_name="Circuit Analysis", dept_id="EE", credit_hours=3, semester=2,
               seats_total=45, instructor="Dr. R. Ahmed", schedule="Tue/Thu 11:00-12:30", room="E-105"),
    ]
    db.session.add_all(courses)
    db.session.commit()


def create_app(env: str | None = None) -> Flask:
    env = env or os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_map.get(env, config_map["default"]))

    # Extensions
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    # Global singletons used by routes
    from .virtual_servers import server_pool  # noqa: F401
    from .ai import predictor  # noqa: F401
    from .routes import balancer_manager  # noqa: F401

    # Blueprints
    from .middleware import auth_bp
    from .load_balancer import lb_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(lb_bp)

    # Health
    @app.get("/api/health")
    def health():
        return jsonify({"ok": True, "env": env})

    with app.app_context():
        _ensure_db_ready(app)
        _seed_data()

    return app

