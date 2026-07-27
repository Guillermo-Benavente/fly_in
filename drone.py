from hub import Hub


class Drone():
    id: int
    current_zone: Hub
    route: dict[int, str]
    zone_route: dict[int, str]
    in_transit: bool
    transit_to: Hub | None
    transit_arrives_at: int
    transit_from: Hub | None
    transit_connection: str | None

    def __init__(self, id: int, current_zone: Hub):
        self.id = id
        self.current_zone = current_zone
        self.route = {}
        self.zone_route = {}
        self.in_transit = False
        self.transit_to = None
        self.transit_arrives_at = -1
        self.transit_from = None
        self.transit_connection = None