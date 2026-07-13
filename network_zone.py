from connection import Connection
from hub import Hub


class NetworkZone():
    drones: int | None
    start: Hub | None
    end: Hub | None
    hubs: list[Hub]
    connections: list[Connection]

    def __init__(self) -> None:
        self.drones = None
        self.start = None
        self.end = None
        self.hubs = []
        self.connections = []
    
    def find_connection(self, hub: Hub) -> list[Connection]:
        connection_filter: list[Connection] = []
        for connection in self.connections:
            if connection.init_hub == hub or connection.final_hub == hub:
                connection_filter.append(connection)
        return connection_filter
