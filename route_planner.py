from network_zone import NetworkZone
from drone import Drone
from mapper import Mapper, MapNode


class RoutePlanner():
    network_zone: NetworkZone
    mapper: Mapper
    
    def __init__(self, network_zone: NetworkZone) -> None:
        self.network_zone = network_zone
        self.mapper = Mapper(network_zone)
        self.routes()

    def routes(self):
        drones: list[Drone] = self.drones()
        while any(drone.current_zone != self.network_zone.end for drone in drones):
            for drone in drones:
                if drone.current_zone != self.network_zone.end:
                    self.move(drone, drones)

    def drones(self) -> list[Drone]:
        list_drones: list[Drone] = []
        for id in range(self.network_zone.drones):
            drone: Drone = Drone(id, self.network_zone.start)
            list_drones.append(drone)
        return list_drones

    def move(self, drone: Drone, drones: list[Drone]) -> None:
        current_node = self.mapper.nodes[drone.current_zone.name]
        best_neighbor: MapNode | None = None
        best_score: int | None = None
        last_visited_name = None
        if hasattr(drone, 'route') and drone.route:
            if isinstance(drone.route, list) and len(drone.route) > 1:
                last_visited_name = drone.route[-2]
            elif isinstance(drone.route, dict) and len(drone.route) > 1:
                last_turn = max(drone.route.keys())
                last_visited_name = drone.route.get(last_turn - 1)
        for neighbor in current_node.neighbors.values():
            if neighbor.remaining_cost == -1:
                continue
            static_cost = neighbor.remaining_cost + neighbor.hub.get_turn_zone()
            traffic_penalty = sum(1 for d in drones if d.current_zone == neighbor.hub)
            backtrack_penalty = 0
            if neighbor.hub.name == last_visited_name:
                backtrack_penalty = 15
            total_score = static_cost + traffic_penalty + backtrack_penalty
            if best_score is None or total_score < best_score:
                best_score = total_score
                best_neighbor = neighbor
        if best_neighbor:
            drone.current_zone = best_neighbor.hub