from flask import Blueprint, request, jsonify
import time, random, threading

from ..extensions import db, socketio
from ..models.request_log import RequestLog
from ..models.registration import Registration
from ..models.course import Course
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

    def _simulate():
        for _ in range(n):
            servers = server_pool.all_alive()
            predicted_load = predictor.predict()
            server = balancer_manager.get_server(servers, predicted_load=predicted_load)
            if not server:
                continue

            result = server.handle_request({"simulated": True})
            predictor.record(server.active_connections)

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