from connection import Connection
from hub import Hub


class NetworkZone():
	drones: int | None
	start: Hub | None
	end: Hub | None
	hubs: list[Hub]
	connections: list[Connection]

	def __init__(self):
		self.drones = None
		self.start = None
		self.end = None
		self.hubs = []
		self.connections = []