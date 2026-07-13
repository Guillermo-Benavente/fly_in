from hub import Hub


class Drone():
    id: int
    current_zone: Hub
    route: dict[int, str]
    
    def __init__(self, id: int, current_zone: Hub):
        self.id = id
        self.current_zone = current_zone
        self.route = {}