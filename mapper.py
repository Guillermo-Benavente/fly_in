from collections import deque
from hub import Hub, TypeZone, TypeMetadata as TMHub
from connection import TypeMetadata as TMConnection
from network_zone import NetworkZone


class MapNode:
    hub: Hub
    remaining_cost: int
    neighbors: dict[str, 'MapNode']
    max_drones: int
    priority_count: int

    def __init__(self, hub: Hub) -> None:
        self.hub = hub
        self.remaining_cost = -1
        self.neighbors = {}
        self.max_drones = int(hub.metadata.get(TMHub.MAX_DRONES, 1))
        self.priority_count = 0


class Mapper:
    nodes: dict[str, MapNode]
    connection_capacity: dict[str, int]

    def __init__(self, network_zone: NetworkZone) -> None:
        self.nodes = {}
        self.connection_capacity = {}
        all_hubs: list[Hub] = [*network_zone.hubs, network_zone.start, network_zone.end]
        for hub in all_hubs:
            self.nodes[hub.name] = MapNode(hub)
        for connection in network_zone.connections:
            init_hub_name: str
            final_hub_name: str
            init_hub_name, final_hub_name = connection.init_hub.name, connection.final_hub.name
            init_node: MapNode = self.nodes[init_hub_name]
            final_node: MapNode = self.nodes[final_hub_name]
            init_node.neighbors[final_hub_name] = final_node
            final_node.neighbors[init_hub_name] = init_node
            unique_name: str = self.connection_key(init_hub_name, final_hub_name)
            self.connection_capacity[unique_name] = int(connection.metadata.get(TMConnection.MAX_LINK_CAPACITY, 1))
        self._calculate_remaining_costs(network_zone.end.name)
        self._calculate_priority_counts()

    def _calculate_remaining_costs(self, end_hub_name: str) -> None: #TODO
        end_node: MapNode = self.nodes[end_hub_name]
        end_node.remaining_cost = 0
        queue: deque[MapNode] = deque([end_node])
        while queue:
            current: MapNode = queue.popleft()
            for neighbor in current.neighbors.values():
                if neighbor.hub.get_turn_zone() == -1:
                    continue
                new_cost: int = current.remaining_cost + neighbor.hub.get_turn_zone()
                if neighbor.remaining_cost == -1 or new_cost < neighbor.remaining_cost:
                    neighbor.remaining_cost = new_cost
                    queue.append(neighbor)

    def _calculate_priority_counts(self) -> None:
        sorted_nodes: list[MapNode] = sorted(self.nodes.values(), key=lambda n: n.remaining_cost)
        for node in sorted_nodes:
            for neighbor in node.neighbors.values():
                expected_rc: int = node.remaining_cost + neighbor.hub.get_turn_zone()
                if neighbor.remaining_cost == expected_rc:
                    bonus: int = 1 if neighbor.hub.metadata.get(TMHub.ZONE) == TypeZone.PRIORITY else 0
                    new_count: int = node.priority_count + bonus
                    if new_count > neighbor.priority_count:
                        neighbor.priority_count = new_count

    @staticmethod
    def connection_key(current_hub: str, next_hub: str) -> str:
        return f'{min(current_hub, next_hub)}-{max(current_hub, next_hub)}'
