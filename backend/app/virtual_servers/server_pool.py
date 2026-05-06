import threading
from .virtual_servers import VirtualServer


class ServerPool:
    """
    Singleton that manages all virtual servers.
    Provides health-check, dynamic add/remove, and status reporting.
    Implements the Singleton design pattern.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._servers: list[VirtualServer] = []
        self._pool_lock = threading.Lock()
        self._init_defaults()

    def _init_defaults(self):
        defaults = [
            ("SRV-01", "Alpha Server", 50),
            ("SRV-02", "Beta Server", 50),
            ("SRV-03", "Gamma Server", 50),
        ]
        for sid, name, cap in defaults:
            self._servers.append(VirtualServer(sid, name, cap))

    def all_alive(self) -> list[VirtualServer]:
        with self._pool_lock:
            return [s for s in self._servers if s.is_alive]

    def all_servers(self) -> list[VirtualServer]:
        with self._pool_lock:
            return list(self._servers)

    def all_status(self) -> list[dict]:
        with self._pool_lock:
            return [s.to_dict() for s in self._servers]

    def get_by_id(self, server_id: str) -> VirtualServer | None:
        with self._pool_lock:
            for s in self._servers:
                if s.server_id == server_id:
                    return s
        return None

    def add_server(self, server_id: str, name: str, capacity: int = 50) -> VirtualServer:
        s = VirtualServer(server_id, name, capacity)
        with self._pool_lock:
            self._servers.append(s)
        return s

    def remove_server(self, server_id: str) -> bool:
        with self._pool_lock:
            before = len(self._servers)
            self._servers = [s for s in self._servers if s.server_id != server_id]
            return len(self._servers) < before

    def toggle_server(self, server_id: str) -> bool | None:
        """Toggle alive state; returns new state or None if not found."""
        with self._pool_lock:
            for s in self._servers:
                if s.server_id == server_id:
                    s.is_alive = not s.is_alive
                    return s.is_alive
        return None

    def reset(self):
        """Reset pool to defaults (for testing)."""
        with self._pool_lock:
            self._servers.clear()
        self._init_defaults()