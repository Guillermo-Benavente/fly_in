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
        self.paser()

    def paser(self) -> None:
        with open(self.file) as file:
            lines: list[str] = file.readlines()
            if not self.first_drones_line(lines[0]):
                raise ValueError('The first line should be the number of drones.')
            if not self.extreme_zones(lines):
                raise ValueError('There must be an entrance and an exit.')
            network_zone: NetworkZone = NetworkZone()
            for line in lines:
                key, value = line.split(':', 1)
                match key:
                    case TypeData.NUMBER_DRONES:
                        try:
                            nb_dron: int = int(value.strip())
                            if network_zone.drones == None:
                                if nb_dron >= 0 and isinstance(nb_dron, int):
                                    network_zone.drones = nb_dron
                                else:
                                    raise ValueError('Invalid drone count, the number must be positive integer.')
                            else:
                                raise ValueError('Value of number drones already set.')
                        except Exception:
                            raise ValueError('The value of number drones must be an int.')
                    case TypeData.START_HUB:
                        if network_zone.start == None:
                            network_zone.start == Hub.parser(value.strip().split(' '))
                        else:
                            raise ValueError('Value of start hub already set.')
                    case TypeData.END_HUB:
                        if network_zone.end == None:
                            network_zone.end == Hub.parser(value.strip().split(' '))
                        else:
                            raise ValueError('Value of end hub already set.')
                    case TypeData.HUB:
                        network_zone.hubs.append(Hub.parser(value.strip().split(' ')))
                    case TypeData.CONNECTION:
                        network_zone.connections.append(Connection(value.strip().split(' ')))
            
            if len(hub_names) != len(set(hub_names)):
                raise ValueError('All zones must have unique names.')

    def first_drones_line(line: str) -> bool:
        if TypeData.NUMBER_DRONES.value in line:
            return True
        else:
            return False

    def extreme_zones(lines: list[str]) -> bool:
        if (
            any(TypeData.START_HUB.value in line for line in lines) 
            and any(TypeData.END_HUB.value in line for line in lines)
        ):
            return True
        else:
            return False

    def hub_data(network_zone: NetworkZone):
        hubs: list[Hub] = network_zone.hubs
        hubs.append(network_zone.start)
        hubs.append(network_zone.end)


    def hub_names(lines: list[str]):
        hub_names: list[str] = []
        for line in lines:
            key, value = line.split(':', 1)
            if (
                key == TypeData.HUB
                or key == TypeData.START_HUB
                or key == TypeData.END_HUB
            ):
                hub_names.append(value.strip().split(' ')[0])

    def hub_coords(lines: list[str]):
        hub_coords: list[tuple[int, int]] = []
        for line in lines:
            key, value = line.split(':', 1)
            if (
                key == TypeData.HUB
                or key == TypeData.START_HUB
                or key == TypeData.END_HUB
            ):
                

class ParserConnection():
    def __init__(self, connection: str, metadata: str) -> None:
        pass