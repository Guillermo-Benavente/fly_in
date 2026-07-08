from enum import StrEnum
from typing import Any
from network_zone import NetworkZone
from hub import Hub
from connection import Connection


class TypeData(StrEnum):
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
            lines: list[str] = [ line for line in file.readlines() if not line.startswith('#')]
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
                            data: list[Any] = value.strip().split(' ')
                            data.append(self.metadata_valid(data.pop()))
                            Hub.parser(data)
                            network_zone.start == Hub(data)
                        else:
                            raise ValueError('Value of start hub already set.')
                    case TypeData.END_HUB:
                        if network_zone.end == None:
                            data: list[Any] = value.strip().split(' ')
                            data.append(self.metadata_valid(data.pop()))
                            Hub.parser(data)
                            network_zone.end == Hub(data)
                        else:
                            raise ValueError('Value of end hub already set.')
                    case TypeData.HUB:
                        data: list[Any] = value.strip().split(' ')
                        data.append(self.metadata_valid(data.pop()))
                        Hub.parser(data)
                        network_zone.hubs.append(Hub(data))
                    case TypeData.CONNECTION:
                        data: list[Any] = value.strip().split(' ')
                        data.append(self.metadata_valid(data.pop()))
                        Connection.parser(data)
                        network_zone.connections.append(Connection(data))
            hubs: list[Hub] = self.hub_data(network_zone)
            hub_names: list[str] = [hub.name for hub in hubs]
            hub_coords: list[tuple[int, int]] = [(hub.coord_x, hub.coord_y)for hub in hubs]
            if len(hub_names) != len(set(hub_names)):
                raise ValueError('All zones must have unique names.')
            if len(hub_coords) != len(set(hub_coords)):
                raise ValueError('All zones must have unique coords.')

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

    def hub_data(network_zone: NetworkZone) -> list[Hub]:
        hubs: list[Hub] = network_zone.hubs
        hubs.append(network_zone.start)
        hubs.append(network_zone.end)
        return hubs
    
    def metadata_valid(metadata: str) -> dict[str, Any]:
        metadata_valid: dict[str, Any] = {}
        for data in metadata[1:-1].split(' '):
            split_data = data.split('=')
            if len(split_data) < 2 or split_data[1] == '':
                raise ValueError(
                    'The metadata is invalid.'
                    'It requires a key or value separated by an equals sign to be valid.'
                    'For more than one argument, separate them with spaces.'
                )
            else:
                key, val = split_data
                metadata_valid[key] = val
        return metadata_valid

class ParserConnection():
    def __init__(self, connection: str, metadata: str) -> None:
        pass