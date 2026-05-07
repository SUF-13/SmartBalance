from flask import Blueprint, request, jsonify, current_app
import time, random, threading

from ..extensions import db, socketio
from ..models.request_log import RequestLog
from ..models.registration import Registration
from ..models.course import Course
from ..models.student import Student
from ..models.academic_calendar import AcademicCalendar
from ..services.course_service import CourseService
from ..services.registration_service import RegistrationService
from ..services.analytics_service import AnalyticsService

lb_bp = Blueprint("lb", __name__, url_prefix="/api")


# ─── Courses ──────────────────────────────────────────────────────────────────

@lb_bp.route("/courses", methods=["GET"])
def get_courses():
    """
    List courses (filterable).
    ---
    tags:
      - Courses
    parameters:
      - in: query
        name: dept_id
        required: false
        type: string
        example: "CS"
      - in: query
        name: semester
        required: false
        type: integer
        example: 3
    responses:
      200:
        description: OK
    """
    dept_id = request.args.get("dept_id")
    semester = request.args.get("semester", type=int)
    courses = CourseService.get_all_courses(dept_id=dept_id, semester=semester)
    return jsonify({"courses": courses})


@lb_bp.route("/courses/<course_id>", methods=["GET"])
def get_course(course_id):
    """
    Get course by id.
    ---
    tags:
      - Courses
    parameters:
      - in: path
        name: course_id
        required: true
        type: string
        example: "CS101"
    responses:
      200:
        description: OK
      404:
        description: Not found
    """
    course = CourseService.get_course(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    return jsonify(course)


@lb_bp.route("/departments", methods=["GET"])
def get_departments():
    """
    List departments.
    ---
    tags:
      - Courses
    responses:
      200:
        description: OK
    """
    return jsonify({"departments": CourseService.get_departments()})


# ─── My Courses (registered by this student) ──────────────────────────────────

@lb_bp.route("/my-courses", methods=["GET"])
def my_courses():
    """
    List courses registered by a student.
    ---
    tags:
      - Registration
    parameters:
      - in: query
        name: student_id
        required: false
        type: string
        example: "DEMO-STUDENT"
        description: Defaults to DEMO-STUDENT
    responses:
      200:
        description: OK
    """
    # No auth: allow passing student_id, otherwise use demo account
    student_id = request.args.get("student_id") or "DEMO-STUDENT"
    return jsonify({"courses": CourseService.get_student_courses(student_id)})


@lb_bp.route("/student/home", methods=["GET"])
def student_home():
    """
    Get home page dataset for a student.
    """
    student_id = request.args.get("student_id") or "DEMO-STUDENT"
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    calendar = AcademicCalendar.query.order_by(AcademicCalendar.id.desc()).first()
    calendar_data = calendar.to_dict() if calendar else None

    return jsonify(
        {
            "student_id": student.student_id,
            "university_information": {
                "roll_number": student.student_id,
                "degree": student.degree,
                "batch": student.batch,
                "section": student.section,
                "campus": student.campus,
            },
            "academic_calendar": {
                "registration": (
                    f"{calendar_data['registration_start']} - {calendar_data['registration_end']}"
                    if calendar_data
                    else None
                ),
                "classes": (
                    f"{calendar_data['classes_start']} - {calendar_data['classes_end']}"
                    if calendar_data
                    else None
                ),
                "online_withdrawal_request": (
                    f"{calendar_data['withdrawal_start']} - {calendar_data['withdrawal_end']}"
                    if calendar_data
                    else None
                ),
            },
            "personal_information": {
                "name": student.full_name,
                "gender": student.gender,
                "email": student.email,
                "dob": student.dob,
                "cnic": student.cnic,
                "mobile_no": student.mobile_no,
                "blood_group": student.blood_group,
                "nationality": student.nationality,
            },
            "contact_information": {
                "address": student.address,
                "home_phone": student.home_phone,
                "postal_code": student.postal_code,
                "city": student.city,
                "country": student.country,
            },
        }
    )


@lb_bp.route("/student/registration-data", methods=["GET"])
def student_registration_data():
    """
    Get all data needed by course registration page.
    """
    student_id = request.args.get("student_id") or "DEMO-STUDENT"
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    registered = (
        Registration.query.filter_by(student_id=student_id, status="enrolled")
        .order_by(Registration.registration_id.asc())
        .all()
    )
    registered_course_ids = {r.course_id for r in registered}
    registered_credits = sum((r.course.credit_hours or 0) for r in registered if r.course)

    all_courses = (
        Course.query.filter_by(is_active=True)
        .order_by(Course.semester.asc(), Course.course_id.asc())
        .all()
    )
    available_courses = [c for c in all_courses if c.course_id not in registered_course_ids]
    improvement_courses = [c for c in available_courses if (c.semester or 0) < (student.semester or 0)]
    offered_courses = [c for c in available_courses if c not in improvement_courses]

    return jsonify(
        {
            "student_info": {
                "name": student.full_name,
                "roll_number": student.student_id,
                "program": student.degree or student.department,
                "batch": student.batch,
                "section": student.section,
                "course_limit_for_semester": 6,
                "registered_courses": len(registered),
                "registered_credits": registered_credits,
                "semester": f"Semester {student.semester}" if student.semester is not None else None,
                "warning_count": student.warning_count,
                "credits_earned": student.credits_earned,
                "credits_attempted": student.credits_attempted,
                "cgpa": float(student.cgpa) if student.cgpa is not None else None,
            },
            "courses_available": [
                {
                    "sr": idx + 1,
                    "course_id": c.course_id,
                    "course_name": c.course_name,
                    "cr_hrs": c.credit_hours,
                    "relation": "Core",
                    "status": "Not Registered",
                    "sections": ["RCS-6A", "RCS-6B", "RCS-6C"],
                }
                for idx, c in enumerate(offered_courses)
            ],
            "improvement_courses": [
                {
                    "sr": idx + 1,
                    "course_id": c.course_id,
                    "course_name": c.course_name,
                    "cr_hrs": c.credit_hours,
                    "relation": "Improvement",
                    "status": "Not Registered",
                    "sections": ["RCS-4A", "RCS-4B"],
                }
                for idx, c in enumerate(improvement_courses)
            ],
            "courses_registered": [
                {
                    "sr": idx + 1,
                    "course_code": r.course_id,
                    "course_name": r.course.course_name if r.course else None,
                    "cr_hrs": r.course.credit_hours if r.course else None,
                    "relation": "Core",
                    "status": "Registered",
                    "section": "RCS-6A",
                }
                for idx, r in enumerate(registered)
            ],
        }
    )


# ─── Registration ─────────────────────────────────────────────────────────────

@lb_bp.route("/register", methods=["POST"])
def register_course():
    """
    Register a student to a course (routed through load balancer).
    ---
    tags:
      - Registration
      - Load Balancer
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [course_id]
          properties:
            student_id: { type: string, example: "DEMO-STUDENT" }
            course_id: { type: string, example: "CS101" }
    responses:
      202:
        description: Accepted (processed async)
      400:
        description: Validation or business rule error
    """
    from ..virtual_servers import server_pool
    from ..routes import balancer_manager
    from ..ai import predictor

    data = request.get_json()
    student_id = data.get("student_id") or "DEMO-STUDENT"
    course_id = data.get("course_id")

    if not course_id:
        return jsonify({"error": "course_id required"}), 400

    servers = server_pool.all_alive()
    predicted_load = predictor.predict()
    server = balancer_manager.get_server(servers, predicted_load=predicted_load)
    algorithm = balancer_manager.get_current()

    result = RegistrationService.register_course(
        student_id=student_id,
        course_id=course_id,
        server=server,
        algorithm=algorithm,
        predictor=predictor,
        socketio=socketio,
    )

    if result.get("success"):
        return jsonify(result), 202
    return jsonify(result), 400


@lb_bp.route("/drop", methods=["POST"])
def drop_course():
    """
    Drop a registered course.
    ---
    tags:
      - Registration
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [course_id]
          properties:
            student_id: { type: string, example: "DEMO-STUDENT" }
            course_id: { type: string, example: "CS101" }
    responses:
      200:
        description: OK
      400:
        description: Not found / invalid
    """
    data = request.get_json()
    student_id = data.get("student_id") or "DEMO-STUDENT"
    course_id = data.get("course_id")
    if not course_id:
        return jsonify({"error": "course_id required"}), 400
    result = RegistrationService.drop_course(student_id, course_id)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


# ─── Load Balancer Control ─────────────────────────────────────────────────────

@lb_bp.route("/balancer/algorithm", methods=["GET"])
def get_algorithm():
    """
    Get current load balancing algorithm.
    ---
    tags:
      - Load Balancer
    responses:
      200:
        description: OK
    """
    from ..routes import balancer_manager
    return jsonify({
        "current": balancer_manager.get_current(),
        "available": balancer_manager.get_all(),
    })


@lb_bp.route("/balancer/algorithm", methods=["POST"])
def set_algorithm():
    """
    Set load balancing algorithm.
    ---
    tags:
      - Load Balancer
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [algorithm]
          properties:
            algorithm:
              type: string
              example: "least_connections"
              enum: ["round_robin", "least_connections", "ai_based"]
    responses:
      200:
        description: OK
      400:
        description: Unknown algorithm
    """
    from ..routes import balancer_manager
    data = request.get_json()
    name = data.get("algorithm")
    if not balancer_manager.set_algorithm(name):
        return jsonify({"error": f"Unknown algorithm: {name}"}), 400
    return jsonify({"message": f"Algorithm set to {name}", "current": name})


@lb_bp.route("/balancer/servers", methods=["GET"])
def get_servers():
    """
    List virtual server statuses (simulated).
    ---
    tags:
      - Load Balancer
      - Servers
    responses:
      200:
        description: OK
    """
    from ..virtual_servers import server_pool
    return jsonify({"servers": server_pool.all_status()})


@lb_bp.route("/balancer/servers/<server_id>/toggle", methods=["POST"])
def toggle_server(server_id):
    """
    Toggle a virtual server alive/dead.
    ---
    tags:
      - Servers
    parameters:
      - in: path
        name: server_id
        required: true
        type: string
        example: "SRV-01"
    responses:
      200:
        description: OK
      404:
        description: Not found
    """
    from ..virtual_servers import server_pool
    new_state = server_pool.toggle_server(server_id)
    if new_state is None:
        return jsonify({"error": "Server not found"}), 404
    return jsonify({"server_id": server_id, "is_alive": new_state})


@lb_bp.route("/balancer/servers", methods=["POST"])
def add_server():
    """
    Add a new virtual server to the pool.
    ---
    tags:
      - Servers
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [server_id, name]
          properties:
            server_id: { type: string, example: "SRV-04" }
            name: { type: string, example: "Delta Server" }
            capacity: { type: integer, example: 50 }
    responses:
      201:
        description: Created
      400:
        description: Validation error
    """
    from ..virtual_servers import server_pool
    data = request.get_json()
    sid = data.get("server_id")
    name = data.get("name")
    capacity = data.get("capacity", 50)
    if not sid or not name:
        return jsonify({"error": "server_id and name required"}), 400
    s = server_pool.add_server(sid, name, capacity)
    return jsonify(s.to_dict()), 201


# ─── Analytics & AI ────────────────────────────────────────────────────────────

@lb_bp.route("/analytics/summary", methods=["GET"])
def analytics_summary():
    """
    Basic system summary.
    ---
    tags:
      - Analytics
    responses:
      200:
        description: OK
    """
    return jsonify(AnalyticsService.get_summary())


@lb_bp.route("/analytics/comparison", methods=["GET"])
def analytics_comparison():
    """
    Compare algorithms (avg response time, totals).
    ---
    tags:
      - Analytics
    responses:
      200:
        description: OK
    """
    return jsonify({"comparison": AnalyticsService.get_algorithm_comparison()})


@lb_bp.route("/analytics/logs", methods=["GET"])
def analytics_logs():
    """
    Get recent request logs.
    ---
    tags:
      - Analytics
    parameters:
      - in: query
        name: limit
        required: false
        type: integer
        example: 50
    responses:
      200:
        description: OK
    """
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"logs": AnalyticsService.get_recent_logs(limit)})


@lb_bp.route("/analytics/prediction", methods=["GET"])
def prediction():
    """
    Get current AI traffic prediction snapshot.
    ---
    tags:
      - AI
    responses:
      200:
        description: OK
    """
    from ..ai import predictor
    return jsonify(predictor.to_dict())


# ─── Simulate Load (for demo/testing) ─────────────────────────────────────────

@lb_bp.route("/simulate", methods=["POST"])
def simulate_load():
    """
    Sends N fake requests through the load balancer for demonstration purposes.
    Does NOT create real registrations; only logs request_log entries.
    ---
    tags:
      - Load Balancer
      - Simulation
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            count: { type: integer, example: 25, description: "Max 100" }
            algorithm:
              type: string
              example: "round_robin"
              enum: ["round_robin", "least_connections", "ai_based"]
    responses:
      200:
        description: OK
    """
    from ..ai import predictor
    from ..virtual_servers import server_pool
    from ..routes import balancer_manager

    data = request.get_json()
    n = min(data.get("count", 10), 100)
    algorithm = data.get("algorithm", balancer_manager.get_current())

    balancer_manager.set_algorithm(algorithm)

    # Dereference Flask's proxy object before starting a background thread.
    app = current_app._get_current_object()

    def _simulate():
        for _ in range(n):
            servers = server_pool.all_alive()
            predicted_load = predictor.predict()
            server = balancer_manager.get_server(servers, predicted_load=predicted_load)
            if not server:
                continue

            result = server.handle_request({"simulated": True})
            predictor.record(server.active_connections)

            with app.app_context():
                with db.engine.connect() as conn:
                    from sqlalchemy.orm import Session
                    with Session(db.engine) as session:
                        log = RequestLog(
                            student_id=None,
                            course_id=None,
                            server_id=server.server_id,
                            algorithm_used=algorithm,
                            response_time=result.get("response_time", 0),
                            status="success" if result["success"] else "failed",
                        )
                        session.add(log)
                        session.commit()

            socketio.emit("request_processed", {
                "result": result,
                "servers": server_pool.all_status(),
            })
            time.sleep(random.uniform(0.01, 0.05))

    t = threading.Thread(target=_simulate, daemon=True)
    t.start()
    

    return jsonify({"message": f"Simulating {n} requests with {algorithm}"})