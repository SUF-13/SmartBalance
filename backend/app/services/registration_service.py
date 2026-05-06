import threading
from ..extensions import db
from ..models.registration import Registration
from ..models.course import Course
from ..models.request_log import RequestLog

class RegistrationService:

    @staticmethod
    def register_course(student_id, course_id, server, algorithm, predictor, socketio):
        """
        Full registration flow:
        1. Validate course & check seats
        2. Check duplicate registration
        3. Route to server via load balancer
        4. Save registration + log
        5. Emit real-time update
        """
        course = Course.query.get(course_id)
        if not course:
            return {"success": False, "error": "Course not found"}

        if course.is_full:
            return {"success": False, "error": "Course is full"}

        if Registration.query.filter_by(
            student_id=student_id,
            course_id=course_id,
            status="enrolled"
        ).first():
            return {"success": False, "error": "Already registered for this course"}

        if not server:
            return {"success": False, "error": "No servers available"}

        # Process in background thread to not block the response
        def process():
            result = server.handle_request({
                "student_id": student_id,
                "course_id":  course_id
            })

            predictor.record(server.active_connections)

            with db.engine.connect() as conn:
                from sqlalchemy.orm import Session
                with Session(db.engine) as session:
                    log = RequestLog(
                        student_id=student_id,
                        course_id=course_id,
                        server_id=server.server_id,
                        algorithm_used=algorithm,
                        response_time=result.get("response_time", 0),
                        status="success" if result["success"] else "failed"
                    )
                    session.add(log)

                    if result["success"]:
                        reg = Registration(
                            student_id=student_id,
                            course_id=course_id,
                            status="enrolled"
                        )
                        session.add(reg)
                        # Update seat count
                        c = session.get(Course, course_id)
                        if c:
                            c.seats_filled += 1
                    session.commit()

            # Broadcast real-time update to dashboard
            from .. import server_pool
            socketio.emit("request_processed", {
                "result":  result,
                "servers": server_pool.all_status()
            })

        t = threading.Thread(target=process)
        t.daemon = True
        t.start()

        return {
            "success": True,
            "message": "Registration request sent",
            "assigned_server": server.name,
            "algorithm": algorithm
        }

    @staticmethod
    def drop_course(student_id, course_id):
        reg = Registration.query.filter_by(
            student_id=student_id,
            course_id=course_id,
            status="enrolled"
        ).first()

        if not reg:
            return {"success": False, "error": "Registration not found"}

        reg.status = "dropped"
        course = Course.query.get(course_id)
        if course and course.seats_filled > 0:
            course.seats_filled -= 1

        db.session.commit()
        return {"success": True, "message": "Course dropped successfully"}