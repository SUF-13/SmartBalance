from .balancer_manager import BalancerManager
from .round_robin import RoundRobinBalancer
from .least_connections import LeastConnectionsBalancer
from .ai_router import AIRouter

# Singleton manager instance used by API routes
balancer_manager = BalancerManager()