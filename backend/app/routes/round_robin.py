class RoundRobinBalancer:
    """
    Round Robin Strategy:
    Distributes requests evenly across all alive servers
    in a circular sequence regardless of their current load.
    """
    def __init__(self):
        self.current_index = 0

    def get_server(self, servers, **kwargs):
        alive = [s for s in servers if s.is_alive]
        if not alive:
            return None

        self.current_index = self.current_index % len(alive)
        server = alive[self.current_index]
        self.current_index += 1
        return server

    def reset(self):
        self.current_index = 0