from __future__ import annotations

import os

from flask import Flask, jsonify
from sqlalchemy import create_engine, text, inspect
from flasgger import Swagger

from .config import config as config_map
from .extensions import cors, db, jwt, limiter, migrate, socketio


def _resolve_database_uri(configured_uri: str | None) -> str:
    """Return a working DB URI, falling back to local SQLite when needed."""
    default_sqlite_uri = "sqlite:///smartbalance.db"
    if not configured_uri:
        return default_sqlite_uri

    try:
        engine = create_engine(configured_uri)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # If the DB is reachable but schema doesn't match our models, prefer SQLite
        # so the project runs without requiring migrations.
        try:
            insp = inspect(engine)
            if "students" in insp.get_table_names():
                cols = {c["name"] for c in insp.get_columns("students")}
                required = {"student_id", "email", "password_hash", "degree"}
                if not required.issubset(cols):
                    engine.dispose()
                    return default_sqlite_uri
        except Exception:
            engine.dispose()
            return default_sqlite_uri

        engine.dispose()
        return configured_uri
    except Exception:
        return default_sqlite_uri


def _ensure_db_ready(app: Flask) -> None:
    """
    Make the project runnable without manual DB setup.
    - Creates tables (SQLite) if they don't exist.
    - If the configured DB is unreachable (e.g. Postgres not running),
      automatically falls back to local SQLite.
    """
    db.create_all()

    # Lightweight "auto-migration" for local SQLite so schema changes
    # (like adding a new column) don't break app startup.
    try:
        engine = db.engine
        if engine.dialect.name == "sqlite":
            insp = inspect(engine)
            if "students" in insp.get_table_names():
                cols = {c["name"] for c in insp.get_columns("students")}
                if "is_admin" not in cols:
                    with engine.begin() as conn:
                        conn.execute(
                            text("ALTER TABLE students ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0")
                        )
    except Exception:
        # If this fails, we'll still surface the underlying error later.
        pass


def _seed_data() -> None:
    # Import inside app context to avoid circular imports.
    from .models.department import Department
    from .models.course import Course
    from .models.student import Student
    from .models.registration import Registration
    from .models.academic_calendar import AcademicCalendar

    if not Department.query.first():
        departments = [
            Department(dept_id="CS", dept_name="Computer Science", faculty_count=25),
            Department(dept_id="SE", dept_name="Software Engineering", faculty_count=18),
            Department(dept_id="EE", dept_name="Electrical Engineering", faculty_count=22),
        ]
        db.session.add_all(departments)

    seed_courses = [
        Course(course_id="CS3012", course_name="Technical and Business Writing", dept_id="CS", credit_hours=3, semester=6,
               seats_total=40, instructor="Dr. A. Khan", schedule="Mon/Wed 10:00-11:30", room="C-101"),
        Course(course_id="CS3044", course_name="Applied Human Computer Interaction", dept_id="CS", credit_hours=3, semester=6,
               seats_total=35, instructor="Dr. S. Ali", schedule="Tue/Thu 09:00-10:30", room="C-202"),
        Course(course_id="AI2002", course_name="Artificial Intelligence", dept_id="CS", credit_hours=3, semester=6,
               seats_total=30, instructor="Dr. M. Noor", schedule="Mon/Wed 12:00-13:30", room="S-110"),
        Course(course_id="CS4045", course_name="Deep Learning for Perception", dept_id="CS", credit_hours=3, semester=6,
               seats_total=45, instructor="Dr. R. Ahmed", schedule="Tue/Thu 11:00-12:30", room="E-105"),
        Course(course_id="CS4051", course_name="Information Retrieval", dept_id="CS", credit_hours=3, semester=6,
               seats_total=40, instructor="Dr. H. Javed", schedule="Mon/Wed 13:00-14:30", room="C-303"),
        Course(course_id="CS4048", course_name="Data Science", dept_id="CS", credit_hours=3, semester=6,
               seats_total=40, instructor="Dr. M. Raza", schedule="Tue/Thu 13:00-14:30", room="C-305"),
        Course(course_id="CS4068", course_name="Network Protocols and Standards", dept_id="CS", credit_hours=3, semester=6,
               seats_total=35, instructor="Dr. F. Waqar", schedule="Fri 11:00-13:00", room="C-210"),
        Course(course_id="CS4032", course_name="Web Programming", dept_id="CS", credit_hours=3, semester=6,
               seats_total=45, instructor="Dr. U. Rehman", schedule="Mon 09:00-12:00", room="C-115"),
        Course(course_id="NS1001", course_name="Applied Physics", dept_id="EE", credit_hours=3, semester=4,
               seats_total=45, instructor="Dr. N. Saeed", schedule="Mon 14:00-16:00", room="E-205"),
        Course(course_id="SS1014", course_name="Expository Writing", dept_id="SE", credit_hours=3, semester=4,
               seats_total=45, instructor="Dr. H. Asif", schedule="Fri 09:00-11:00", room="S-207"),
    ]
    for course in seed_courses:
        if not Course.query.get(course.course_id):
            db.session.add(course)
    db.session.flush()

    if not AcademicCalendar.query.first():
        db.session.add(
            AcademicCalendar(
                semester_label="Spring 2026",
                registration_start="10 Jan 2026",
                registration_end="20 Jan 2026",
                classes_start="02 Feb 2026",
                classes_end="10 Jun 2026",
                withdrawal_start="15 Mar 2026",
                withdrawal_end="25 Mar 2026",
            )
        )

    demo_student = Student.query.get("DEMO-STUDENT")
    if not demo_student:
        demo_student = Student(
            student_id="DEMO-STUDENT",
            full_name="Muhammad Sufyan Ali",
            email="demo@student.edu",
            department="CS",
            semester=6,
            degree="BS(CS)",
            batch="Fall 2025",
            section="BCS-2A",
            campus="Main Campus",
            gender="Male",
            dob="08/25/2004",
            cnic="42201-5049666-3",
            mobile_no="0334-2228071",
            blood_group="O",
            nationality="Pakistani",
            address="H No S-7, Tariq Street 6, DHA, Karachi",
            home_phone="021-111222333",
            postal_code="75500",
            city="Karachi",
            country="Pakistan",
            warning_count=0,
            credits_earned=83,
            credits_attempted=102,
            cgpa=3.17,
            credit_hours_completed=83,
            is_admin=True,
        )
        demo_student.set_password("pass123")
        db.session.add(demo_student)
        db.session.flush()

    if not Registration.query.filter_by(student_id="DEMO-STUDENT", status="enrolled").first():
        enrolled_course_ids = ["CS3012", "CS3044", "AI2002", "CS4045"]
        for course_id in enrolled_course_ids:
            course = Course.query.get(course_id)
            if not course:
                continue
            db.session.add(
                Registration(
                    student_id="DEMO-STUDENT",
                    course_id=course_id,
                    status="enrolled",
                )
            )
            if course.seats_filled < course.seats_total:
                course.seats_filled += 1

    db.session.commit()


def create_app(env: str | None = None) -> Flask:
    env = env or os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_map.get(env, config_map["default"]))
    app.config["SQLALCHEMY_DATABASE_URI"] = _resolve_database_uri(
        app.config.get("SQLALCHEMY_DATABASE_URI")
    )

    Swagger(
        app,
        template={
            "swagger": "2.0",
            "info": {
                "title": "SmartBalance API",
                "description": "Student portal + load balancing simulation APIs.",
                "version": "1.0.0",
            },
            "securityDefinitions": {
                "bearerAuth": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                    "description": "JWT Bearer token. Example: 'Bearer <token>'",
                }
            },
            "basePath": "/",
            "schemes": ["http", "https"],
        },
        config={
            "headers": [],
            "specs": [
                {
                    "endpoint": "apispec_1",
                    "route": "/openapi.json",
                    "rule_filter": lambda rule: True,
                    "model_filter": lambda tag: True,
                }
            ],
            "static_url_path": "/flasgger_static",
            "swagger_ui": True,
            "specs_route": "/apidocs/",
        },
    )

    # Extensions
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": "*"}},
        allow_headers=["Content-Type", "Authorization"],
    )
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Global singletons used by routes
    from .virtual_servers import server_pool  # noqa: F401
    from .ai import predictor  # noqa: F401
    from .routes import balancer_manager  # noqa: F401

    # Blueprints
    from .middleware import admin_bp, auth_bp
    from .load_balancer import lb_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(lb_bp)

    # Health
    @app.get("/api/health")
    def health():
        return jsonify({"ok": True, "env": env})

    @app.errorhandler(429)
    def ratelimited(_e):
        return jsonify({"error": "Rate limit exceeded"}), 429

    with app.app_context():
        _ensure_db_ready(app)
        _seed_data()

    return app

