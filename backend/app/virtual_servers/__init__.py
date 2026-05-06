from .virtual_servers import VirtualServer
from .server_pool import ServerPool

# Singleton server pool used across the app
server_pool = ServerPool()