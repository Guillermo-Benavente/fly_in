from network_zone import NetworkZone
from hub import TypeZone, TypeMetadata as TMHub
from drone import Drone
from mapper import Mapper, MapNode


class RoutePlanner():
    network_zone: NetworkZone
    mapper: Mapper
    drone_list: list[Drone]
    
    def __init__(self, network_zone: NetworkZone) -> None:
        self.network_zone = network_zone
        self.mapper = Mapper(network_zone)
        self.drone_list = self._create_drones()
        self._drone_routes()

    def _create_drones(self) -> list[Drone]:
        list_drones: list[Drone] = []
        for id in range(self.network_zone.drones):
            drone: Drone = Drone(id, self.network_zone.start)
            self.network_zone.start.drones_number += 1
            list_drones.append(drone)
        return list_drones

    def _drone_routes(self) -> None:
        start_cost: int = self.mapper.nodes[self.network_zone.start.name].remaining_cost
        max_iterations: int = start_cost * self.network_zone.drones
        iteration: int = 0
        while any(
            drone.current_zone != self.network_zone.end
            for drone
            in self.drone_list
        ):
            active: list[Drone] = [
                drone
                for drone
                in self.drone_list
                if drone.current_zone != self.network_zone.end
            ]
            if iteration >= max_iterations:
                drones_in_loop: list[str] = [
                    f'{drone.id}:{drone.current_zone.name}'
                    for drone
                    in active
                ]
                raise RuntimeError(f'Infinite loop detected. Stuck drones: {drones_in_loop}')
            active.sort(key=lambda drone: self.mapper.nodes[drone.current_zone.name].remaining_cost)
            iteration_route: dict[str, int] = {}
            for index, drone in enumerate(active):
                self._move_drone(index, drone, iteration_route, iteration)
            iteration += 1

    def _move_drone(
        self,
        drone_position: int,
        drone: Drone,
        iteration_route: dict[str, int],
        iteration: int
    ) -> None:
        if drone.in_transit:
            drone.in_transit = False
            drone.route[iteration] = drone.current_zone.name
            return
        next_node: MapNode = self._search_next_node(drone_position, drone, iteration_route)
        is_restricted: bool = next_node.hub.metadata.get(TMHub.ZONE) == TypeZone.RESTRICTED
        if drone.current_zone == next_node.hub:
            drone.route[iteration] = drone.current_zone.name
        else:
            drone.current_zone.drones_number -= 1
            next_node.hub.drones_number += 1
            key: str = Mapper.connection_key(drone.current_zone.name, next_node.hub.name)
            iteration_route[key] = iteration_route.get(key, 0) + 1
            drone.current_zone = next_node.hub
            drone.route[iteration] = next_node.hub.name
            if is_restricted:
                drone.in_transit = True


    def _search_next_node(
        self,
        drone_position: int,
        drone: Drone,
        iteration_route: dict[str, int]
    ) -> MapNode:
        current_node: MapNode = self.mapper.nodes[drone.current_zone.name]
        valid_nodes: list[MapNode] = []
        for neighbor in current_node.neighbors.values():
            if self._is_valid_neighbor(neighbor):
                key = Mapper.connection_key(current_node.hub.name, neighbor.hub.name)
                if self.mapper.connection_capacity.get(key) > iteration_route.get(key, 0):
                    valid_nodes.append(neighbor)
        if valid_nodes:
            return self._better_node(drone_position, valid_nodes, current_node)
        return current_node

    def _better_node(
        self,
        drone_position: int,
        valid_nodes: list[MapNode],
        current_node: MapNode
    ) -> MapNode:
        is_even = (drone_position % 2 == 0)
        margin = 0 if is_even else (drone_position // 2)
        nodes_low_cost = [
            node
            for node
            in valid_nodes
            if node.remaining_cost <= (
                current_node.remaining_cost + margin
            )
        ]
        if nodes_low_cost:
            return min(
                nodes_low_cost, 
                key=lambda node: (
                    node.remaining_cost,
                    -node.priority_count,
                    node.hub.drones_number
                )
            )
        return current_node  

    def _is_valid_neighbor(self, neighbor: MapNode) -> bool:
        if neighbor.hub.metadata.get(TMHub.ZONE) == TypeZone.BLOCKED:
            return False
        is_limit_nodes: bool = neighbor.hub.name in [
            self.network_zone.start.name,
            self.network_zone.end.name
        ]
        if (
            not is_limit_nodes 
            and neighbor.hub.drones_number >= neighbor.max_drones
        ):
            return False
        return True
    
    def output(self) -> str:
        lines: list[str] = []
        all_keys: list[int] = [key for drone in self.drone_list for key in drone.route.keys()]
        max_turn: int = max(all_keys) + 1 if all_keys else 0
        for turn in range(max_turn):
            movements: list[str] = []
            for drone in self.drone_list:
                if turn in drone.route:
                    value: str = drone.route[turn]
                    movements.append(f'D{drone.id}-{value}')
            if movements:
                lines.append(' '.join(movements))
        return '\n'.join(lines)