"""Module for mapping network topology and calculating route traversal metrics.

Provides graph node representations and distance/priority metrics used by the
route planning system to determine optimal drone pathways.
"""
from collections import deque
from hub import Hub, TypeZone, TypeMetadata as TMHub
from connection import TypeMetadata as TMConnection
from network_zone import NetworkZone


class MapNode:
    """Represents a node within the navigation graph wrapping a Hub instance.

    Attributes:
        hub (Hub): The underlying Hub object associated with this node.
        remaining_cost (int):
            Estimated turns/cost required to reach the destination node.
        neighbors (dict[str, MapNode]): Adjacent nodes mapped by hub name.
        max_drones (int):
            Maximum drone capacity allowed simultaneously at this hub.
        priority_count (int): Cumulative count of priority zones
            along the path to destination.
    """
    hub: Hub
    remaining_cost: int
    neighbors: dict[str, 'MapNode']
    max_drones: int
    priority_count: int

    def __init__(self, hub: Hub) -> None:
        """Initializes a MapNode wrapping the target Hub.

        Args:
            hub (Hub): The Hub instance represented by this node.
        """
        self.hub = hub
        self.remaining_cost = -1
        self.neighbors = {}
        self.max_drones = int(hub.metadata.get(TMHub.MAX_DRONES, 1))
        self.priority_count = 0


class Mapper:
    """Constructs and manages the graph structure for the entire network zone.

    Calculates path costs, connection capacities, and priority node frequencies
    relative to the target destination.

    Attributes:
        nodes (dict[str, MapNode]): Map of hub names to MapNode instances.
        connection_capacity (dict[str, int]):
            Map of formatted edge keys to max capacity limits.
    """
    nodes: dict[str, MapNode]
    connection_capacity: dict[str, int]

    def __init__(self, network_zone: NetworkZone) -> None:
        """Builds graph nodes and connections from a given
        NetworkZone topology.

        Args:
            network_zone (NetworkZone):
                Network topology containing hubs and connections.
        """
        self.nodes = {}
        self.connection_capacity = {}
        all_hubs: list[Hub] = network_zone.all_hubs()
        for hub in all_hubs:
            self.nodes[hub.name] = MapNode(hub)
        for connection in network_zone.connections:
            init_hub_name: str = connection.init_hub.name
            final_hub_name: str = connection.final_hub.name
            init_node: MapNode = self.nodes[init_hub_name]
            final_node: MapNode = self.nodes[final_hub_name]
            init_node.neighbors[final_hub_name] = final_node
            final_node.neighbors[init_hub_name] = init_node
            unique_name: str = self.connection_key(
                init_hub_name, final_hub_name
            )
            self.connection_capacity[unique_name] = int(
                connection.metadata.get(TMConnection.MAX_LINK_CAPACITY, 1)
            )
        self._calculate_remaining_costs(network_zone.end.name)
        self._calculate_priority_counts()

    def _calculate_remaining_costs(self, end_hub_name: str) -> None:
        """Computes shortest turn costs from all accessible nodes
        to the destination.

        Uses Breadth-First Search (BFS) starting from the destination
        hub backwards, skipping restricted hubs with a turn cost of -1.

        Args:
            end_hub_name (str): Identifier of the destination hub.
        """
        end_node: MapNode = self.nodes[end_hub_name]
        end_node.remaining_cost = 0
        neighbor_queue: deque[MapNode] = deque([end_node])
        while neighbor_queue:
            current_hub: MapNode = neighbor_queue.popleft()
            for neighbor_hub in current_hub.neighbors.values():
                if neighbor_hub.hub.get_turn_zone() == -1:
                    continue
                new_cost: int = (
                    current_hub.remaining_cost +
                    neighbor_hub.hub.get_turn_zone()
                )
                if (
                    neighbor_hub.remaining_cost == -1 or
                    new_cost < neighbor_hub.remaining_cost
                ):
                    neighbor_hub.remaining_cost = new_cost
                    neighbor_queue.append(neighbor_hub)

    def _calculate_priority_counts(self) -> None:
        """Calculates cumulative priority hub bonuses along optimal paths.

        Traverses nodes sorted by remaining cost to maximize priority
        hub counts for drones choosing between equal-cost paths.
        """
        sorted_nodes: list[MapNode] = sorted(
            self.nodes.values(),
            key=lambda node: node.remaining_cost
        )
        for node in sorted_nodes:
            for neighbor in node.neighbors.values():
                expected_remaining_cost: int = (
                    node.remaining_cost + neighbor.hub.get_turn_zone()
                )
                if neighbor.remaining_cost == expected_remaining_cost:
                    if (
                        neighbor.hub.metadata.get(TMHub.ZONE) ==
                        TypeZone.PRIORITY
                    ):
                        bonus: int = 1
                    else:
                        bonus = 0
                    new_count: int = node.priority_count + bonus
                    if new_count > neighbor.priority_count:
                        neighbor.priority_count = new_count

    @staticmethod
    def connection_key(current_hub: str, next_hub: str) -> str:
        """Generates a canonical, order-independent lookup key for
        an edge between two hubs.

        Args:
            current_hub (str): Name of the first hub.
            next_hub (str): Name of the second hub.

        Returns:
            str: Alphabetically ordered edge identifier (e.g., 'hubA-hubB').
        """
        return f'{min(current_hub, next_hub)}-{max(current_hub, next_hub)}'
