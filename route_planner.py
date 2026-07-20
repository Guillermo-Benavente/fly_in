import random
from network_zone import NetworkZone
from drone import Drone
from mapper import Mapper, MapNode


class RoutePlanner():
    network_zone: NetworkZone
    mapper: Mapper
    drone_list: list[Drone]
    visit_counter: dict[int, dict[str, int]]

    def __init__(self, network_zone: NetworkZone) -> None:
        self.network_zone = network_zone
        self.mapper = Mapper(network_zone)
        self.drone_list = self._create_drones()
        self.visit_counter = {d.id: {node.hub.name: 0 for node in self.mapper.nodes.values()} for d in self.drone_list}
        self._route()

    def _route(self) -> None:
        max_iterations = 20000
        iteration = 0
        while any(d.current_zone != self.network_zone.end for d in self.drone_list):
            if iteration >= max_iterations:
                stuck = [f'{d.id}:{d.current_zone.name}' for d in self.drone_list if d.current_zone != self.network_zone.end]
                raise RuntimeError(f'Infinite loop detected. Stuck drones: {stuck}')
            active = [d for d in self.drone_list if d.current_zone != self.network_zone.end]
            active.sort(key=lambda d: self.mapper.nodes[d.current_zone.name].remaining_cost)
            for drone in active:
                self._move(drone)
            iteration += 1

    def _create_drones(self) -> list[Drone]:
        list_drones: list[Drone] = []
        for id in range(self.network_zone.drones):
            drone: Drone = Drone(id, self.network_zone.start)
            list_drones.append(drone)
        return list_drones

    @staticmethod
    def _edge_key(a: str, b: str) -> str:
        return f'{min(a, b)}-{max(a, b)}'

    def _move(self, drone: Drone) -> None:
        current_node = self.mapper.nodes[drone.current_zone.name]

        self.visit_counter[drone.id][drone.current_zone.name] += 1
        visits = self.visit_counter[drone.id]

        prev_node_name = list(drone.route.values())[-1] if drone.route else None

        candidates: list[tuple[float, MapNode]] = []
        for neighbor in current_node.neighbors.values():
            if neighbor.remaining_cost == -1:
                continue
            is_special = neighbor.hub == self.network_zone.end or neighbor.hub == self.network_zone.start
            if not is_special:
                hub_occupancy = sum(1 for d in self.drone_list if d.current_zone == neighbor.hub)
                if hub_occupancy >= neighbor.max_drones:
                    continue
            max_cap = self.mapper.link_capacity.get(
                self._edge_key(current_node.hub.name, neighbor.hub.name), 1
            )
            link_occupancy = sum(
                1 for d in self.drone_list
                if d.id != drone.id
                and d.current_zone == current_node.hub
                and d.route
                and list(d.route.values())[-1] == neighbor.hub.name
            )
            if link_occupancy >= max_cap:
                continue
            static_cost = neighbor.remaining_cost + neighbor.hub.get_turn_zone()
            traffic_penalty = sum(1 for d in self.drone_list if d.current_zone == neighbor.hub)

            backtrack_penalty = 10 if prev_node_name == neighbor.hub.name else 0
            visit_penalty = 5 * max(0, visits.get(neighbor.hub.name, 0) - 1)

            total_score = static_cost + traffic_penalty + backtrack_penalty + visit_penalty
            candidates.append((total_score, neighbor))

        if not candidates:
            return

        min_score = min(c[0] for c in candidates)
        best = [c for c in candidates if c[0] == min_score]
        if len(best) > 1:
            random.shuffle(best)
        best_neighbor = best[0][1]
        drone.current_zone = best_neighbor.hub
        drone.route[len(drone.route)] = best_neighbor.hub.name

    def output(self) -> str:
        lines: list[str] = []
        max_turn = max(len(d.route) for d in self.drone_list) if self.drone_list else 0
        for turn in range(max_turn):
            movements: list[str] = []
            for d in self.drone_list:
                if turn in d.route:
                    movements.append(f'D{d.id}-{d.route[turn]}')
            if movements:
                lines.append(' '.join(movements))
        return '\n'.join(lines)
