from strenum import StrEnum
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

    def paser(self) -> NetworkZone:
        with open(self.file) as file:
            lines: list[str] = [line for line in file.readlines() if not line.startswith('#') and line.strip()]
            if not self.first_drones_line(lines[0]):
                raise ValueError('The first line should be the number of drones.')
            if not self.extreme_zones(lines):
                raise ValueError('There must be an entrance and an exit.')
            network_zone: NetworkZone = NetworkZone()
            for line in lines:
                if line.strip() == '':
                    continue
                key, value = line.strip().split(':', 1)
                match key:
                    case TypeData.NUMBER_DRONES:
                        try:
                            nb_dron: int = int(value.strip())
                            if network_zone.drones is not None:
                                raise ValueError('Value of number drones already set.')
                            if nb_dron < 0:
                                raise ValueError('Invalid drone count, the number must be positive integer.')
                            network_zone.drones = nb_dron
                        except ValueError as e:
                            if str(e):
                                raise e
                            raise ValueError('The value of number drones must be an int.')
                    case TypeData.START_HUB:
                        if network_zone.start == None:
                            data: list[Any] = self.extract_data(value)
                            network_zone.start = Hub(*data)
                        else:
                            raise ValueError('Value of start hub already set.')
                    case TypeData.END_HUB:
                        if network_zone.end == None:
                            data: list[Any] = self.extract_data(value)
                            network_zone.end = Hub(*data)
                        else:
                            raise ValueError('Value of end hub already set.')
                    case TypeData.HUB:
                        data: list[Any] = self.extract_data(value)
                        network_zone.hubs.append(Hub(*data))
                    case TypeData.CONNECTION:
                        data: list[Any] = self.extract_data(value)
                        network_zone.connections.append(Connection(*data, self.hub_data(network_zone)))
            hubs: list[Hub] = self.hub_data(network_zone)
            hub_names: list[str] = [hub.name for hub in hubs]
            hub_coords: list[tuple[int, int]] = [(hub.coord_x, hub.coord_y)for hub in hubs]
            if len(hub_names) != len(set(hub_names)):
                raise ValueError('All zones must have unique names.')
            if len(hub_coords) != len(set(hub_coords)):
                raise ValueError('All zones must have unique coords.')
            connections: list[tuple[str, str]] = [
                tuple(
                    sorted(
                        [connection.init_hub.name, connection.final_hub.name]
                    )
                ) 
                for connection in network_zone.connections
            ]
            if len(connections) != len(set(connections)):
                raise ValueError('All connections must have unique.')
            return network_zone

    def first_drones_line(self, line: str) -> bool:
        if TypeData.NUMBER_DRONES in line:
            return True
        else:
            return False

    def extreme_zones(self, lines: list[str]) -> bool:
        if (
            any(TypeData.START_HUB in line for line in lines) 
            and any(TypeData.END_HUB in line for line in lines)
        ):
            return True
        else:
            return False

    def hub_data(self, network_zone: NetworkZone) -> list[Hub]:
        hubs: list[Hub] = [*network_zone.hubs]
        hubs.append(network_zone.start)
        hubs.append(network_zone.end)
        return hubs

    def extract_data(self, crude_data: str) -> list[Any]:
        all_data: list[str] = crude_data.strip().split('[')
        if len(all_data) > 2:
            raise ValueError('There can only be one metadata box')
        data: list[str] = all_data[0].strip().split(' ')
        if len(all_data) == 2:
            return [*data, self.metadata_valid(all_data[1][:-1])]
        else:
            return [*data, {}]


    def metadata_valid(self, metadata: str) -> dict[str, Any]:
        metadata_valid: dict[str, Any] = {}
        for data in metadata.split(' '):
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