"""Module for route planning and drone movement simulation.

Defines the RoutePlanner class, which manages drone fleet initialization,
step-by-step navigation across network hubs using path cost heuristics,
capacity limits, and turn outputs.
"""
from network_zone import NetworkZone
from hub import TypeZone, TypeMetadata as TMHub, TypeConsoleColor, Hub
from drone import Drone
from mapper import Mapper, MapNode


class RoutePlanner():
    """Plans routes and manages discrete simulation steps for a drone fleet.

    Attributes:
        network_zone (NetworkZone):
            Network topology containing start/end nodes and hubs.
        mapper (Mapper):
            Spatial mapping engine holding node costs and connectivity.
        drone_list (list[Drone]): Collection of all active drones in the fleet.
    """
    network_zone: NetworkZone
    mapper: Mapper
    drone_list: list[Drone]

    def __init__(self, network_zone: NetworkZone) -> None:
        """Initializes the RoutePlanner, instantiates drones,
        and computes routes.

        Args:
            network_zone (NetworkZone): The network graph environment
                for drone routing.
        """
        self.network_zone = network_zone
        self.mapper = Mapper(network_zone)
        self.drone_list = self._create_drones()
        self._drone_routes()

    def _create_drones(self) -> list[Drone]:
        """Instantiates all drones assigned to the network and places them
        at start.

        Returns:
            list[Drone]: A list of newly created Drone instances.
        """
        list_drones: list[Drone] = []
        for id in range(self.network_zone.drones):
            drone: Drone = Drone(id, self.network_zone.start)
            self.network_zone.start.drones_number += 1
            list_drones.append(drone)
        return list_drones

    def _drone_routes(self) -> None:
        """Simulates iterative movements for all drones until
        reaching destination.

        Raises:
            RuntimeError: If the iteration count exceeds safety bounds,
                indicating a deadlock.
        """
        start_cost: int = (
            self.mapper.nodes[self.network_zone.start.name].remaining_cost
        )
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
                raise RuntimeError(
                    f'Infinite loop detected. Stuck drones: {drones_in_loop}'
                )
            active.sort(
                key=lambda drone:
                self.mapper.nodes[drone.current_zone.name].remaining_cost
            )
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
        """Executes a single step or transit delay for an individual drone.

        Args:
            drone_position (int):
                Index position of the drone in the active queue.
            drone (Drone): The target drone being moved.
            iteration_route (dict[str, int]):
                Tracked connection usage for current turn.
            iteration (int): Current simulation step index.
        """
        if drone.in_transit:
            drone.in_transit = False
            drone.route[iteration] = drone.current_zone.name
            return
        next_node: MapNode = self._search_next_node(
            drone_position, drone, iteration_route
        )
        is_restricted: bool = (
            next_node.hub.metadata.get(TMHub.ZONE) == TypeZone.RESTRICTED
        )
        if drone.current_zone == next_node.hub:
            drone.route[iteration] = drone.current_zone.name
        else:
            drone.current_zone.drones_number -= 1
            next_node.hub.drones_number += 1
            key: str = Mapper.connection_key(
                drone.current_zone.name, next_node.hub.name
            )
            iteration_route[key] = iteration_route.get(key, 0) + 1
            if is_restricted:
                drone.in_transit = True
                drone.route[iteration] = self._get_connection_name(
                    drone.current_zone.name, next_node.hub.name
                )
            else:
                drone.route[iteration] = next_node.hub.name
            drone.current_zone = next_node.hub

    def _get_connection_name(self, hub_a: str, hub_b: str) -> str:
        """Retrieves the explicit name of a connection between two hubs.

        Args:
            hub_a (str): Name of the first hub.
            hub_b (str): Name of the second hub.

        Returns:
            str: Custom connection name if defined,
                otherwise formatted connection key.
        """
        for conn in self.network_zone.connections:
            if conn.init_hub.name == hub_a and conn.final_hub.name == hub_b:
                return conn.name
            if conn.init_hub.name == hub_b and conn.final_hub.name == hub_a:
                return conn.name
        return Mapper.connection_key(hub_a, hub_b)

    def _search_next_node(
        self,
        drone_position: int,
        drone: Drone,
        iteration_route: dict[str, int]
    ) -> MapNode:
        """Finds valid adjacent neighbor nodes adhering
        to capacity constraints.

        Args:
            drone_position (int):
                Current index of the drone within the turn sequence.
            drone (Drone): The drone attempting to move.
            iteration_route (dict[str, int]):
                Connection passage counts for current turn.

        Returns:
            MapNode: Selected optimal neighbor node,
                or current node if no moves are available.
        """
        current_node: MapNode = self.mapper.nodes[drone.current_zone.name]
        valid_nodes: list[MapNode] = []
        for neighbor in current_node.neighbors.values():
            if self._is_valid_neighbor(neighbor):
                key = Mapper.connection_key(
                    current_node.hub.name, neighbor.hub.name
                )
                if (
                    self.mapper.connection_capacity.get(key, 0) >
                    iteration_route.get(key, 0)
                ):
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
        """Selects the best destination node using cost heuristics
        and priority counts.

        Args:
            drone_position (int):
                Position index used for tie-breaking/margin calculations.
            valid_nodes (list[MapNode]): Candidate adjacent nodes.
            current_node (MapNode): Current node location of the drone.

        Returns:
            MapNode: The best evaluated MapNode for the drone to navigate to.
        """
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
        """Validates if a neighbor node can receive additional drones.

        Args:
            neighbor (MapNode): Neighbor node to evaluate.

        Returns:
            bool: True if the node is accessible and under capacity,
                False otherwise.
        """
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
        """Formats complete turn-by-turn drone flight logs with color coding.

        Returns:
            str: Multi-line string depicting drone movement logs across turns.
        """
        lines: list[str] = []
        hubs_by_name = {h.name: h for h in self.network_zone.all_hubs()}
        max_turns: int = max([len(dron.route) for dron in self.drone_list]) + 1
        for iteration in range(max_turns):
            movements: list[str] = []
            for drone in self.drone_list:
                if iteration in drone.route:
                    last_value: str = drone.route.get(iteration - 1, '')
                    value: str = drone.route.get(iteration, '')
                    if last_value != value and not (
                        value == self.network_zone.start.name and
                        iteration == 0
                    ):
                        hub: Hub | None = hubs_by_name.get(value)
                        if (hub and TMHub.COLOR in hub.metadata):
                            color_name: str | None = (
                                hub.metadata.get(TMHub.COLOR)
                            )
                        else:
                            color_name = None
                        if color_name and color_name.lower() == 'rainbow':
                            colored_value: str = (
                                TypeConsoleColor.rainbow(value)
                            )
                        elif (
                            color_name and
                            color_name.upper()
                            in TypeConsoleColor.__members__
                        ):
                            color: TypeConsoleColor = (
                                TypeConsoleColor[color_name.upper()]
                            )
                            colored_value = (
                                f'{color}{value}{TypeConsoleColor.RESET}'
                            )
                        else:
                            colored_value = value
                        movements.append(f'D{drone.id}-{colored_value}')
            if movements:
                lines.append(' '.join(movements))
        return '\n'.join(lines)
