from .round_robin import RoundRobinBalancer
from .least_connections import LeastConnectionsBalancer
from .ai_router import AIRouter

class BalancerManager:
    """
    Manages which load balancing algorithm is currently active.
    Implements the Strategy Pattern — algorithms are swappable at runtime.
    """
    ALGORITHMS = ["round_robin", "least_connections", "ai_based"]

    def __init__(self):
        self._strategies = {
            "round_robin": RoundRobinBalancer(),
            "least_connections": LeastConnectionsBalancer(),
            "ai_based": AIRouter()
        }
        self.current_algorithm = "round_robin"

    def set_algorithm(self, name):
        if name in self._strategies:
            self.current_algorithm = name
            return True
        return False

    def get_server(self, servers, predicted_load=0.5):
        strategy = self._strategies[self.current_algorithm]
        return strategy.get_server(servers, predicted_load=predicted_load)

    def get_current(self):
        return self.current_algorithm

    def get_all(self):
        return self.ALGORITHMS