"""Module for managing network topologies and connectivity.

Defines the NetworkZone container class, which aggregates start/end nodes,
intermediate hubs, and connections, providing methods to query connected routes.
"""
from connection import Connection
from hub import Hub


class NetworkZone():
    """Represents a full network graph consisting of hubs, connections, and drones.

    Attributes:
        drones (int): Total count of drones assigned to the network.
        start (Hub): Starting origin hub for drone navigation.
        end (Hub): Destination hub for drone arrivals.
        hubs (list[Hub]): Collection of intermediate network hubs.
        connections (list[Connection]): List of connections linking hubs together.
    """
    drones: int
    start: Hub
    end: Hub
    hubs: list[Hub]
    connections: list[Connection]

    def __init__(
        self, 
        drones: int, 
        start: Hub, 
        end: Hub, 
        hubs: list[Hub], 
        connections: list[Connection]
    ) -> None:
        """Initializes a NetworkZone instance with all required attributes.

        Args:
            drones (int): Total count of drones assigned to the network.
            start (Hub): Starting origin hub for drone navigation.
            end (Hub): Destination hub for drone arrivals.
            hubs (list[Hub]): Collection of intermediate network hubs.
            connections (list[Connection]): List of connections linking hubs together.
        """
        self.drones = drones
        self.start = start
        self.end = end
        self.hubs = hubs
        self.connections = connections

    def all_hubs(self) -> list[Hub]:
        """Retrieves a consolidated list containing all network hubs.

        Includes intermediate hubs as well as the start and end hubs.

        Returns:
            list[Hub]: Combined list of all hubs present in the network zone.
        """
        return [*self.hubs, self.start, self.end]
    
    def find_connection(self, hub: Hub) -> list[Connection]:
        """Finds all connections linked directly to a specified hub.

        Args:
            hub (Hub): The target hub to query for adjacent connections.

        Returns:
            list[Connection]: A list of connections where the target hub is either
                the initial or final endpoint.
        """
        connection_filter: list[Connection] = []
        for connection in self.connections:
            if connection.init_hub == hub or connection.final_hub == hub:
                connection_filter.append(connection)
        return connection_filter
