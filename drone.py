"""Module for representing individual drones in the routing system.

Defines the Drone class, which tracks a drone's identifier,
current hub location, scheduled flight route per turn, and transit state.
"""
from hub import Hub


class Drone():
    """Represents an autonomous drone navigating through network hubs.

    Attributes:
        id (int): Unique numerical identifier for the drone.
        current_zone (Hub): The current hub where the drone is located.
        route (dict[int, str]):
            Map of turn numbers to assigned hub names or connection links.
        in_transit (bool):
            Flag indicating whether the drone is currently moving between hubs.
    """
    id: int
    current_zone: Hub
    route: dict[int, str]
    in_transit: bool

    def __init__(self, id: int, current_zone: Hub):
        """Initializes a new Drone instance.

        Args:
            id (int): Unique identifier for the drone.
            current_zone (Hub): The initial starting hub for the drone.
        """
        self.id = id
        self.current_zone = current_zone
        self.route = {}
        self.in_transit = False
