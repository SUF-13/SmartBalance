from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models.student import Student
from ..models.course import Course
from ..models.department import Department


admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _require_admin() -> Student:
    sid = get_jwt_identity()
    student = Student.query.get(sid)
    if not student or not student.is_admin:
        return None
    return student


@admin_bp.route("/courses", methods=["POST"])
@jwt_required()
def create_course():
    """
    Create a course (admin only).
    ---
    tags: [Admin, Courses]
    security:
      - bearerAuth: []
    consumes: [application/json]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [course_id, course_name, dept_id, credit_hours, seats_total]
          properties:
            course_id: { type: string, example: "CS9999" }
            course_name: { type: string, example: "New Course" }
            dept_id: { type: string, example: "CS" }
            credit_hours: { type: integer, example: 3 }
            semester: { type: integer, example: 6 }
            seats_total: { type: integer, example: 40 }
            instructor: { type: string, example: "Dr. X" }
            schedule: { type: string, example: "Mon 10-12" }
            room: { type: string, example: "C-100" }
    responses:
      201: { description: Created }
      400: { description: Validation error }
      403: { description: Admin required }
    """
    if not _require_admin():
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json() or {}
    required = ["course_id", "course_name", "dept_id", "credit_hours", "seats_total"]
    for f in required:
        if data.get(f) in (None, ""):
            return jsonify({"error": f"{f} is required"}), 400

    if Course.query.get(data["course_id"]):
        return jsonify({"error": "Course already exists"}), 409

    if not Department.query.get(data["dept_id"]):
        return jsonify({"error": "Invalid dept_id"}), 400

    course = Course(
        course_id=data["course_id"],
        course_name=data["course_name"],
        dept_id=data["dept_id"],
        credit_hours=int(data["credit_hours"]),
        semester=data.get("semester"),
        seats_total=int(data["seats_total"]),
        seats_filled=int(data.get("seats_filled", 0) or 0),
        instructor=data.get("instructor"),
        schedule=data.get("schedule"),
        room=data.get("room"),
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(course)
    db.session.commit()
    return jsonify(course.to_dict()), 201


@admin_bp.route("/courses/<course_id>", methods=["PATCH"])
@jwt_required()
def update_course(course_id: str):
    """
    Update a course (admin only).
    ---
    tags: [Admin, Courses]
    security:
      - bearerAuth: []
    consumes: [application/json]
    parameters:
      - in: path
        name: course_id
        required: true
        type: string
      - in: body
        name: body
        required: true
        schema:
          type: object
    responses:
      200: { description: OK }
      403: { description: Admin required }
      404: { description: Not found }
    """
    if not _require_admin():
        return jsonify({"error": "Admin access required"}), 403

    course = Course.query.get(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    data = request.get_json() or {}
    for field in ["course_name", "dept_id", "credit_hours", "semester", "seats_total", "seats_filled", "instructor", "schedule", "room", "is_active"]:
        if field in data:
            setattr(course, field, data[field])
    db.session.commit()
    return jsonify(course.to_dict())


@admin_bp.route("/departments", methods=["POST"])
@jwt_required()
def create_department():
    """
    Create a department (admin only).
    ---
    tags: [Admin, Courses]
    security:
      - bearerAuth: []
    consumes: [application/json]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [dept_id, dept_name]
          properties:
            dept_id: { type: string, example: "DS" }
            dept_name: { type: string, example: "Data Science" }
            faculty_count: { type: integer, example: 12 }
    responses:
      201: { description: Created }
      403: { description: Admin required }
      409: { description: Already exists }
    """
    if not _require_admin():
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json() or {}
    dept_id = data.get("dept_id")
    dept_name = data.get("dept_name")
    if not dept_id or not dept_name:
        return jsonify({"error": "dept_id and dept_name are required"}), 400
    if Department.query.get(dept_id):
        return jsonify({"error": "Department already exists"}), 409

    d = Department(dept_id=dept_id, dept_name=dept_name, faculty_count=int(data.get("faculty_count", 0) or 0))
    db.session.add(d)
    db.session.commit()
    return jsonify(d.to_dict()), 201


@admin_bp.route("/courses/<course_id>", methods=["DELETE"])
@jwt_required()
def delete_course(course_id: str):
    """
    Delete (deactivate) a course (admin only).
    ---
    tags: [Admin, Courses]
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: course_id
        required: true
        type: string
    responses:
      200: { description: OK }
      403: { description: Admin required }
      404: { description: Not found }
    """
    if not _require_admin():
        return jsonify({"error": "Admin access required"}), 403

    course = Course.query.get(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    course.is_active = False
    db.session.commit()
    return jsonify({"success": True, "message": "Course deactivated"})

