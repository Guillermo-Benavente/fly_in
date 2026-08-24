from network_zone import NetworkZone
from hub import TypeZone, TypeMetadata as TMHub
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

    def _is_valid_neighbor(self, drone: Drone, current_node: MapNode, neighbor: MapNode, turn: int) -> bool:
        if neighbor.remaining_cost == -1:
            return False
        is_special: bool = neighbor.hub.name == self.network_zone.end.name or neighbor.hub.name == self.network_zone.start.name
        if not is_special:
            hub_occupancy: int = sum(
                1 for d in self.drone_list
                if d.current_zone.name == neighbor.hub.name
                or (d.in_transit and d.transit_to is not None and d.transit_to.name == neighbor.hub.name)
            )
            if hub_occupancy >= neighbor.max_drones:
                return False
        max_cap: int = self.mapper.connection_capacity.get(
            self._edge_key(current_node.hub.name, neighbor.hub.name), 1
        )
        link_key: str = self._edge_key(current_node.hub.name, neighbor.hub.name)
        link_occupancy: int = sum(
            1 for d in self.drone_list
            if d.id != drone.id
            and (
                (turn in d.route
                 and d.route[turn] == neighbor.hub.name
                 and (turn == 0 or d.route.get(turn - 1) == current_node.hub.name))
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
        static_cost: int = neighbor.remaining_cost
        is_special: bool = (
            neighbor.hub.name == self.network_zone.end.name
            or neighbor.hub.name == self.network_zone.start.name
        )
        traffic_penalty: int = 0 if is_special else sum(
            1 for d in self.drone_list
            if d.current_zone.name == neighbor.hub.name
            and not d.in_transit
        )
        backtrack_penalty: int = 10 if prev_node_name == neighbor.hub.name else 0
        visit_penalty: int = 5 * max(0, visits.get(neighbor.hub.name, 0) - 1)
        return static_cost + traffic_penalty + backtrack_penalty + visit_penalty

    def _pick_best(self, candidates: list[tuple[float, MapNode]], avoid_name: str | None = None, drone_id: int = 0) -> MapNode:
        min_score: float = min(candidate[0] for candidate in candidates)
        best_candidates: list[tuple[float, MapNode]] = [
            candidate
            for candidate
            in candidates
            if candidate[0] == min_score
        ]
        is_one_candidate: int = len(best_candidates) == 1
        if not is_one_candidate and avoid_name:
            moved: list[tuple[float, MapNode]] = [
                candidate
                for candidate
                in best_candidates
                if candidate[1].hub.name != avoid_name
            ]
            if moved:
                best_candidates = moved
        if not is_one_candidate:
            priority: list[tuple[float, MapNode]] = [
                candidate
                for candidate
                in best_candidates
                if candidate[1].hub.metadata.get(TMHub.ZONE) == TypeZone.PRIORITY
            ]
            if priority:
                best_candidates = priority
            if not is_one_candidate:
                max_pc: int = max(candidate[1].priority_count for candidate in best_candidates)
                best_candidates = [candidate for candidate in best_candidates if candidate[1].priority_count == max_pc]
            if not is_one_candidate:
                names: list[str] = sorted(set(candidate[1].hub.name for candidate in best_candidates))
                offset: int = drone_id % len(names)
                rotated: list[str] = names[offset:] + names[:offset]
                best_candidates.sort(key=lambda candidate: rotated.index(candidate[1].hub.name))
        return best_candidates[0][1]

    def _stuck_turns(self, drone: Drone) -> int:
        current: str = drone.current_zone.name
        count: int = 0
        for turn_key in sorted(drone.route.keys(), reverse=True):
            if drone.route[turn_key] == current:
                count += 1
            else:
                break
        return count

    def _plan_move(self, drone: Drone, turn: int) -> MapNode:
        current_node: MapNode = self.mapper.nodes[drone.current_zone.name]
        visits: dict[str, int] = self.visit_counter[drone.id]
        prev_node_name: str | None = list(drone.route.values())[-1] if drone.route else None
        stuck: int = self._stuck_turns(drone)
        candidates: list[tuple[float, MapNode]] = []
        for neighbor in current_node.neighbors.values():
            if not self._is_valid_neighbor(drone, current_node, neighbor, turn):
                continue
            score: float = self._score_neighbor(drone, neighbor, visits, prev_node_name)
            if neighbor.remaining_cost < current_node.remaining_cost:
                score -= 3
            if stuck > 2:
                score -= min(stuck, 5)
            candidates.append((score + drone.id * 0.0001, neighbor))
        stay_score: float = current_node.remaining_cost + 0.99 + drone.id * 0.0001
        if drone.current_zone.name == self.network_zone.start.name:
            stay_score += 2
        candidates.append((stay_score, current_node))
        avoid: str | None = drone.current_zone.name if stuck == 0 else None
        return self._pick_best(candidates, avoid, drone.id)

    def _execute_move(self, drone: Drone, target: MapNode, turn: int) -> None:
        is_restricted: bool = target.hub.metadata.get(TMHub.ZONE) == TypeZone.RESTRICTED
        if target.hub.name == drone.current_zone.name:
            drone.route[turn] = drone.current_zone.name
            drone.zone_route[turn] = drone.current_zone.name
        else:
            if is_restricted:
                drone.current_zone = target.hub
                drone.route[turn] = target.hub.name
                drone.zone_route[turn] = target.hub.name
                drone.in_transit = True
                drone.transit_to = target.hub
                drone.transit_arrives_at = turn + 1
            else:
                drone.current_zone = target.hub
                drone.route[turn] = target.hub.name
                drone.zone_route[turn] = target.hub.name
            self.visit_counter[drone.id][target.hub.name] += 1

    def _move(self, drone: Drone, turn: int) -> None:
        target: MapNode = self._plan_move(drone, turn)
        self._execute_move(drone, target, turn)

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
