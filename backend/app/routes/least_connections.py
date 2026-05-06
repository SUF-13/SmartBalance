class LeastConnectionsBalancer:
    """
    Least Connections Strategy:
    Always routes the next request to the server
    with the fewest active connections at that moment.
    Better than Round Robin under uneven load conditions.
    """
    def get_server(self, servers, **kwargs):
        alive = [s for s in servers if s.is_alive]
        if not alive:
            return None

        return min(alive, key=lambda s: s.active_connections)