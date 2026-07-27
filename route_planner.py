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
        self.visit_counter = {
            drone.id: {
                node.hub.name: 0
                for node
                in self.mapper.nodes.values()
            }
            for drone
            in self.drone_list
        }
        self._route()

    def _route(self) -> None:
        start_cost: int = self.mapper.nodes[self.network_zone.start.name].remaining_cost
        max_iterations: int = start_cost * self.network_zone.drones * 2
        iteration: int = 0
        while any(
            drone.current_zone != self.network_zone.end
            for drone
            in self.drone_list
        ):
            arrived_ids: set[int] = set()
            for drone in self.drone_list:
                if drone.in_transit:
                    self._arrive(drone, iteration)
                    arrived_ids.add(drone.id)
            active: list[Drone] = [
                drone
                for drone
                in self.drone_list
                if drone.current_zone != self.network_zone.end
                and not drone.in_transit
                and drone.id not in arrived_ids
            ]
            if iteration >= max_iterations:
                stuck: list[str] = [
                    f'{drone.id}:{drone.current_zone.name}'
                    for drone
                    in self.drone_list
                    if drone.current_zone != self.network_zone.end
                ]
                raise RuntimeError(f'Infinite loop detected. Stuck drones: {stuck}')
            active.sort(key=lambda drone: self.mapper.nodes[drone.current_zone.name].remaining_cost)
            for drone in active:
                self._move(drone, iteration)
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

    def _arrive(self, drone: Drone, turn: int) -> None:
        if drone.in_transit and turn >= drone.transit_arrives_at:
            drone.current_zone = drone.transit_to
            drone.route[turn] = drone.transit_to.name
            drone.zone_route[turn] = drone.transit_to.name
            drone.in_transit = False
            drone.transit_to = None
            drone.transit_arrives_at = -1
            drone.transit_from = None
            drone.transit_connection = None

    def _is_valid_neighbor(self, drone: Drone, current_node: MapNode, neighbor: MapNode) -> bool:
        if neighbor.remaining_cost == -1:
            return False
        is_special: bool = neighbor.hub == self.network_zone.end or neighbor.hub == self.network_zone.start
        if not is_special:
            hub_occupancy: int = sum(
                1 for d in self.drone_list
                if d.current_zone == neighbor.hub
                or (d.in_transit and d.transit_to == neighbor.hub)
            )
            if hub_occupancy >= neighbor.max_drones:
                return False
        max_cap: int = self.mapper.link_capacity.get(
            self._edge_key(current_node.hub.name, neighbor.hub.name), 1
        )
        link_key: str = self._edge_key(current_node.hub.name, neighbor.hub.name)
        link_occupancy: int = sum(
            1 for d in self.drone_list
            if d.id != drone.id
            and (
                (d.current_zone == current_node.hub
                 and d.route
                 and list(d.route.values())[-1] == neighbor.hub.name)
                or (d.in_transit and d.transit_connection == link_key)
            )
        )
        if link_occupancy >= max_cap:
            return False
        return True

    def _score_neighbor(
        self, drone: Drone, neighbor: MapNode,
        visits: dict[str, int], prev_node_name: str | None
    ) -> float:
        static_cost: int = neighbor.remaining_cost + neighbor.hub.get_turn_zone()
        is_special: bool = (
            neighbor.hub == self.network_zone.end
            or neighbor.hub == self.network_zone.start
        )
        traffic_penalty: int = 0 if is_special else sum(
            1 for d in self.drone_list
            if d.current_zone == neighbor.hub
            and not d.in_transit
        )
        backtrack_penalty: int = 10 if prev_node_name == neighbor.hub.name else 0
        visit_penalty: int = 5 * max(0, visits.get(neighbor.hub.name, 0) - 1)
        return static_cost + traffic_penalty + backtrack_penalty + visit_penalty

    def _pick_best(self, candidates: list[tuple[float, MapNode]]) -> MapNode:
        min_score: float = min(c[0] for c in candidates)
        best: list[tuple[float, MapNode]] = [c for c in candidates if c[0] == min_score]
        if len(best) > 1:
            priority: list[tuple[float, MapNode]] = [
                c for c in best
                if c[1].hub.metadata.get('zone') == 'priority'
            ]
            if priority:
                best = priority
            if len(best) > 1:
                random.shuffle(best)
        return best[0][1]

    def _move(self, drone: Drone, turn: int) -> None:
        current_node: MapNode = self.mapper.nodes[drone.current_zone.name]

        visits: dict[str, int] = self.visit_counter[drone.id]
        prev_node_name: str | None = list(drone.route.values())[-1] if drone.route else None

        candidates: list[tuple[float, MapNode]] = []
        for neighbor in current_node.neighbors.values():
            if not self._is_valid_neighbor(drone, current_node, neighbor):
                continue
            score: float = self._score_neighbor(drone, neighbor, visits, prev_node_name)
            candidates.append((score, neighbor))

        stay_score: float = current_node.remaining_cost + 0.1
        has_progress: bool = any(
            n.remaining_cost < current_node.remaining_cost
            for _, n in candidates
        )
        if not has_progress:
            candidates.append((stay_score, current_node))

        best_neighbor: MapNode = self._pick_best(candidates)
        is_restricted: bool = best_neighbor.hub.metadata.get('zone') == 'restricted'

        if best_neighbor == current_node:
            drone.route[turn] = current_node.hub.name
            drone.zone_route[turn] = current_node.hub.name
            return

        if is_restricted:
            drone.in_transit = True
            drone.transit_to = best_neighbor.hub
            drone.transit_arrives_at = turn + 1
            drone.transit_from = drone.current_zone
            drone.transit_connection = self._edge_key(drone.current_zone.name, best_neighbor.hub.name)
            drone.route[turn] = drone.transit_connection
            drone.zone_route[turn] = drone.transit_connection
        else:
            drone.current_zone = best_neighbor.hub
            drone.route[turn] = best_neighbor.hub.name
            drone.zone_route[turn] = best_neighbor.hub.name
        self.visit_counter[drone.id][best_neighbor.hub.name] += 1

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
