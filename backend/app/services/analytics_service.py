from ..models.request_log import RequestLog
from ..models.registration import Registration
from sqlalchemy import func

class AnalyticsService:

    @staticmethod
    def get_summary():
        total_requests = RequestLog.query.count()
        successful = RequestLog.query.filter_by(status="success").count()
        failed = RequestLog.query.filter_by(status="failed").count()
        total_enrollments = Registration.query.filter_by(status="enrolled").count()

        return {
            "total_requests": total_requests,
            "successful": successful,
            "failed": failed,
            "total_enrollments": total_enrollments,
            "success_rate": round((successful / total_requests * 100) if total_requests else 0, 2)
        }

    @staticmethod
    def get_algorithm_comparison():
        """Compare average response time per algorithm"""
        results = (
            RequestLog.query
            .with_entities(
                RequestLog.algorithm_used,
                func.avg(RequestLog.response_time).label("avg_response"),
                func.count(RequestLog.log_id).label("total"),
                func.sum(
                    (RequestLog.status == "failed").cast(db_int())
                ).label("failed")
            )
            .group_by(RequestLog.algorithm_used)
            .all()
        )
        return [
            {
                "algorithm": r.algorithm_used,
                "avg_response": round(float(r.avg_response or 0), 3),
                "total": r.total,
                "failed": r.failed or 0
            }
            for r in results
        ]

    @staticmethod
    def get_recent_logs(limit=50):
        logs = RequestLog.query.order_by(
            RequestLog.requested_at.desc()
        ).limit(limit).all()
        return [l.to_dict() for l in logs]

    @staticmethod
    def get_server_stats(server_pool):
        return server_pool.all_status()


def db_int():
    from sqlalchemy import Integer
    return Integer