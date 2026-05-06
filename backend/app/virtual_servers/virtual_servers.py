import time
import random
import threading


class VirtualServer:
    """
    Simulates a real application server.
    Tracks active connections, CPU usage, and processes requests
    with realistic response-time simulation.
    Implements thread-safe connection tracking.
    """

    def __init__(self, server_id: str, name: str, capacity: int = 50):
        self.server_id = server_id
        self.name = name
        self.capacity = capacity
        self.is_alive = True
        self._active_connections = 0
        self._cpu_usage = 0.0
        self._lock = threading.Lock()
        self._total_requests = 0
        self._failed_requests = 0

    @property
    def active_connections(self) -> int:
        return self._active_connections

    @property
    def cpu_usage(self) -> float:
        return self._cpu_usage

    def _update_cpu(self):
        """Simulate CPU load based on connection ratio."""
        ratio = self._active_connections / max(self.capacity, 1)
        # Add some noise
        noise = random.uniform(-5, 5)
        self._cpu_usage = min(100.0, max(0.0, ratio * 90 + noise))

    def handle_request(self, data: dict) -> dict:
        """
        Simulate processing a registration request.
        Returns result with timing info.
        """
        with self._lock:
            self._active_connections += 1
            self._total_requests += 1
            self._update_cpu()

        try:
            # Simulate processing time proportional to load
            load_ratio = self._active_connections / max(self.capacity, 1)
            base_time = random.uniform(0.05, 0.15)
            # Under high load, response time increases
            processing_time = base_time + (load_ratio * 0.3)

            time.sleep(processing_time)

            # Simulate occasional failures under heavy load (>90% capacity)
            if load_ratio > 0.9 and random.random() < 0.1:
                raise RuntimeError("Server overloaded")

            return {
                "success": True,
                "server_id": self.server_id,
                "server_name": self.name,
                "response_time": round(processing_time, 3),
                "active_connections": self._active_connections,
            }

        except Exception as e:
            with self._lock:
                self._failed_requests += 1
            return {
                "success": False,
                "server_id": self.server_id,
                "server_name": self.name,
                "error": str(e),
                "response_time": 0,
            }

        finally:
            with self._lock:
                self._active_connections = max(0, self._active_connections - 1)
                self._update_cpu()

    def to_dict(self) -> dict:
        return {
            "server_id": self.server_id,
            "name": self.name,
            "capacity": self.capacity,
            "is_alive": self.is_alive,
            "active_connections": self._active_connections,
            "cpu_usage": round(self._cpu_usage, 1),
            "load_percent": round(
                (self._active_connections / max(self.capacity, 1)) * 100, 1
            ),
            "total_requests": self._total_requests,
            "failed_requests": self._failed_requests,
        }

    def __repr__(self):
        return f"<VirtualServer {self.server_id} conn={self._active_connections}>"