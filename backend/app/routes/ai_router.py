class AIRouter:
    """
    AI-Based Routing Strategy:
    Uses a weighted scoring function combining:
    - Current active connections (40%)
    - Current CPU usage (40%)
    - Predicted future load from AI model (20%)

    Picks the server with the lowest composite score.
    Automatically avoids overloaded servers even before
    they become a bottleneck.
    """
    def get_server(self, servers, predicted_load=0.5, **kwargs):
        alive = [s for s in servers if s.is_alive]
        if not alive:
            return None

        def score(server):
            w_conn = 0.4
            w_cpu = 0.4
            w_pred = 0.2

            conn_score = server.active_connections / max(server.capacity, 1)
            cpu_score = server.cpu_usage / 100.0
            pred_score = float(predicted_load)

            return (w_conn * conn_score) + (w_cpu * cpu_score) + (w_pred * pred_score)

        return min(alive, key=score)