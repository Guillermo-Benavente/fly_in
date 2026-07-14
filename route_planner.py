from network_zone import NetworkZone
from drone import Drone
from hub import Hub, TypeMetadata


class RoutePlanner():
    network_zone: NetworkZone
    
    def __init__(self, network_zone: NetworkZone) -> None:
        self.network_zone = network_zone
        self.routes()

    def routes(self):
        drones: list[Drone] = self.drones()
        map: dict[str, int] = self.map()
        while any(drone.route[-1] != 'goal' for drone in drones):
            for drone in drones:
                self.move(drone, drones)

    def drones(self) -> list[Drone]:
        list_drones: list[Drone] = []
        for id in range(self.network_zone.drones):
            drone: Drone = Drone(id, self.network_zone.start)
            list_drones.append(drone)
        return list_drones

    def move(self, drone: Drone, drones: list[Drone]):
        pass

    def map(self) -> dict[str, int]:
        map: dict[str, dict[str, int]] = {}
        queue: list[Hub] = [self.network_zone.end]
        while queue:
            current_node = queue.pop(0)
            for connection in self.network_zone.find_connection(current_node):
                if connection.final_hub == current_node:
                    init_weight: int = connection.init_hub.get_turn_zone()
                    new_weight: int = map[current_node.name] or 0
                    if init_weight == -1:
                        new_weight = -1
                    else:
                        new_weight += init_weight
                    map[connection.init_hub.name][current_node.name] = new_weight
                    queue.append(connection.init_hub)
        return map
{start:{waypoint1:3}}
{waypoint1:{start:-2,waypoint2:2}}
{waypoint2:{waypoint1:-3,goal:1}}
{goal:{waypoint2:-4, goal:-1}}