from enum import Enum
from network_zone import NetworkZone
from hub import Hub
from connection import Connection


class TypeData(Enum):
	NUMBER_DRONES = 'nb_drones'
	START_HUB = 'start_hub'
	END_HUB = 'end_hub'
	HUB = 'hub'
	CONNECTION = 'connection'


class Parser():
	file: str

	def __init__(self, file: str) -> None:
		self.file = file

	def paser(self) -> None:
		with open(self.file) as file:
			lines: list[str] = file.readlines()
			network_zone: NetworkZone = NetworkZone()
			for line in lines:
				key, value = line.split(':', 1)
				match key:
					case TypeData.NUMBER_DRONES:
						try:
							nb_dron: int = int(value.strip())
							if network_zone.drones == None:
								if nb_dron >= 0:
									network_zone.drones = nb_dron
								else:
									raise ValueError('Invalid drone count, the number must be positive')
							else:
								raise ValueError('Value of number drones already set')
						except Exception:
								raise ValueError('The value of number drones must be an int')
					case TypeData.START_HUB:
						if network_zone.start == None:
							network_zone.start == Hub(value.strip().split(' '))
						else:
							raise ValueError('Value of start hub already set')
					case TypeData.END_HUB:
						if network_zone.end == None:
							network_zone.end == Hub(value.strip().split(' '))
						else:
							raise ValueError('Value of end hub already set')
					case TypeData.HUB:
						network_zone.hubs.append(Hub(value.strip().split(' ')))
					case TypeData.CONNECTION:
						network_zone.connections.append(Connection(value.strip().split(' ')))

class ParserHub():
	def __init__(
		self,
		name: str,
		coord_x: str,
		coord_y: str,
		metadata: str
	) -> Hub:
		pass


class ParserConnection():
	def __init__(self, connection: str, metadata: str):
		pass