from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..services.auth_service import AuthService
from ..models.student import Student

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new student (no auth).
    ---
    tags:
      - Auth
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [student_id, full_name, email, password]
          properties:
            student_id: { type: string, example: "DEMO-STUDENT" }
            full_name: { type: string, example: "Demo Student" }
            email: { type: string, example: "demo@student.edu" }
            password: { type: string, example: "pass123" }
            department: { type: string, example: "CS" }
            semester: { type: integer, example: 1 }
    responses:
      201:
        description: Created
      400:
        description: Validation error
      409:
        description: Already exists
    """
    data = request.get_json()
    required = ["student_id", "full_name", "email", "password"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    student, err = AuthService.register(data)
    if err:
        return jsonify({"error": err}), 409

    token = create_access_token(identity=student.student_id)
    return jsonify({
        "message": "Registration successful",
        "student": student.to_dict(),
        "token": token,
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login with email/password (no token; returns student profile).
    ---
    tags:
      - Auth
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [email, password]
          properties:
            email: { type: string, example: "demo@student.edu" }
            password: { type: string, example: "pass123" }
    responses:
      200:
        description: OK
      400:
        description: Validation error
      401:
        description: Invalid credentials
    """
    data = request.get_json() or {}
    email = data.get("email") or data.get("student_id")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "student_id/email and password are required"}), 400

    student, _token, err = AuthService.login(email, password)
    if err:
        return jsonify({"error": err}), 401

    token = create_access_token(identity=student.student_id)
    return jsonify({
        "message": "Login successful",
        "student": student.to_dict(),
        "token": token,
    })


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Get a student profile (no auth).
    ---
    tags:
      - Auth
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
      404:
        description: Student not found
    """
    """
    Get current logged-in student profile.
    ---
    tags:
      - Auth
    security:
      - bearerAuth: []
    responses:
      200:
        description: OK
      401:
        description: Missing/invalid token
    """
    student_id = get_jwt_identity()
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student.to_dict())