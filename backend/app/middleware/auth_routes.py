from flask import Blueprint, request, jsonify
from ..services.auth_service import AuthService
from ..models.student import Student

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    required = ["student_id", "full_name", "email", "password"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    student, err = AuthService.register(data)
    if err:
        return jsonify({"error": err}), 409

    return jsonify({
        "message": "Registration successful",
        "student": student.to_dict(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    student, _token, err = AuthService.login(email, password)
    if err:
        return jsonify({"error": err}), 401

    return jsonify({
        "message": "Login successful",
        "student": student.to_dict(),
    })


@auth_bp.route("/me", methods=["GET"])
def me():
    # No auth: allow explicit student_id, otherwise return a demo user if present.
    student_id = request.args.get("student_id") or "DEMO-STUDENT"
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student.to_dict())