from collections import deque
from hub import Hub, TypeMetadata as TMHub
from connection import TypeMetadata as TMConnection
from network_zone import NetworkZone


class MapNode:
    hub: Hub
    remaining_cost: int
    neighbors: dict[str, 'MapNode']
    max_drones: int

    def __init__(self, hub: Hub) -> None:
        self.hub = hub
        self.remaining_cost = -1
        self.neighbors = {}
        self.max_drones = int(hub.metadata.get(TMHub.MAX_DRONES, 1))


class Mapper:
    nodes: dict[str, MapNode]
    link_capacity: dict[str, int]

    def __init__(self, network_zone: NetworkZone) -> None:
        self.nodes = {}
        self.link_capacity = {}
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
            unique_name: str = f'{min(init_hub_name, final_hub_name)}-{max(init_hub_name, final_hub_name)}'
            self.link_capacity[unique_name] = int(connection.metadata.get(TMConnection.MAX_LINK_CAPACITY, 1))
        self._calculate_remaining_costs(network_zone.end.name)

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
