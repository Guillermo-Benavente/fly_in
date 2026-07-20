# mapper.py
from hub import Hub
from connection import Connection
from network_zone import NetworkZone


class MapNode:
    hub: Hub
    remaining_cost: int
    neighbors: dict[str, 'MapNode']

    def __init__(self, hub: Hub) -> None:
        self.hub = hub
        self.remaining_cost = -1
        self.neighbors = {}


class Mapper:
    nodes: dict[str, MapNode]
    start_node: MapNode
    end_node: MapNode

    def __init__(self, network_zone: NetworkZone) -> None:
        self.nodes = {}
        all_hubs:list[Hub] = [*network_zone.hubs, network_zone.start, network_zone.end]
        for hub in all_hubs:
            self.nodes[hub.name] = MapNode(hub)
        self.start_node = self.nodes[network_zone.start.name]
        self.end_node = self.nodes[network_zone.end.name]
        for connection in network_zone.connections:
            init_node = self.nodes[connection.init_hub.name]
            final_node = self.nodes[connection.final_hub.name]
            init_node.neighbors[final_node.hub.name] = final_node
            final_node.neighbors[init_node.hub.name] = init_node
        self._calculate_remaining_costs()

    def _calculate_remaining_costs(self) -> None:
        self.end_node.remaining_cost = 0
        queue: list[MapNode] = [self.end_node]
        while queue:
            current = queue.pop(0)
            for neighbor in current.neighbors.values():
                if neighbor.hub.get_turn_zone() == -1:
                    continue
                new_cost = current.remaining_cost + current.hub.get_turn_zone()
                if neighbor.remaining_cost == -1 or new_cost < neighbor.remaining_cost:
                    neighbor.remaining_cost = new_cost
                    queue.append(neighbor)