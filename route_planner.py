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
            for drone in active:
                self._move_drone(drone, iteration)
            iteration += 1

    def _move_drone(self, drone: Drone, iteration: int) -> None:
        next_node: MapNode = self._search_next_node(drone)
        # is_restricted: bool = next_node.hub.metadata.get(TMHub.ZONE) == TypeZone.RESTRICTED
        if drone.current_zone == next_node.hub:
            drone.route[iteration] = drone.current_zone.name
            drone.zone_route[iteration] = drone.current_zone.name
        else:
            drone.current_zone.drones_number -= 1
            next_node.hub.drones_number += 1
            drone.current_zone = next_node.hub
            drone.route[iteration] = next_node.hub.name
            drone.zone_route[iteration] = next_node.hub.name
            # if is_restricted:
            #     drone.in_transit = True
            #     drone.transit_to = next_node.hub
            #     drone.transit_arrives_at = iteration + 1
            

    def _search_next_node(self, drone: Drone) -> MapNode:
        current_node: MapNode = self.mapper.nodes[drone.current_zone.name]
        valid_nodes: list[MapNode] = []
        for neighbor in current_node.neighbors.values():
            if self._is_valid_neighbor(neighbor):
                valid_nodes.append(neighbor)
        if valid_nodes:
            return self._better_node(valid_nodes, current_node)
        return current_node

    def _better_node(self, valid_nodes: list[MapNode], current_node: MapNode) -> MapNode:
        nodes_low_cost = [
            node
            for node
            in valid_nodes
            if node.remaining_cost <= current_node.remaining_cost
        ]
        if nodes_low_cost:
            return min(
                nodes_low_cost, 
                key=lambda node: (node.remaining_cost, -node.priority_count)
            )
        return current_node  

    def _is_valid_neighbor(self, neighbor: MapNode) -> bool:
        if neighbor.hub.metadata.get(TMHub.ZONE) == TypeZone.BLOCKED:
            return False
        is_limit_nodes: bool = neighbor.hub.name in [
            self.network_zone.start.name,
            self.network_zone.end.name
        ]
        if not is_limit_nodes:
            if neighbor.hub.drones_number >= neighbor.max_drones:
                return False
        return True