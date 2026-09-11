"""Module for parsing network layout configuration files.

Defines data types and file parsing logic to extract network parameters, hubs,
connections, and metadata into a validated NetworkZone structure.
"""
from strenum import StrEnum
from typing import Any
from network_zone import NetworkZone
from hub import Hub
from connection import Connection


class TypeData(StrEnum):
    """Enumeration of valid line prefix keys in the configuration file."""
    NUMBER_DRONES = 'nb_drones'
    START_HUB = 'start_hub'
    END_HUB = 'end_hub'
    HUB = 'hub'
    CONNECTION = 'connection'


class Parser():
    """Handles the parsing and validation of network topology text files.

    Attributes:
        file (str): Path to the configuration file to be processed.
    """
    file: str

    def __init__(self, file: str) -> None:
        """Initializes the Parser instance with a target file path.

        Args:
            file (str): Path to the network configuration file.
        """
        self.file = file

    def parser(self) -> NetworkZone:
        """Reads, validates, and builds a complete NetworkZone object
        from the file.

        Parses line by line, creating start, end, and intermediate hubs as well
        as verifying connection uniqueness, node coordinate integrity,
        and name conflicts.

        Returns:
            NetworkZone:
                Fully instantiated and validated network topology object.

        Raises:
            ValueError: If file content violates syntax rules,
                missing required hubs, contains duplicated hub
                names/coordinates, or duplicated connections.
        """
        with open(self.file) as file:
            drones: int | None = None
            start: Hub | None = None
            end: Hub | None = None
            hubs: list[Hub] = []
            connections: list[Connection] = []
            lines: list[str] = file.readlines()
            is_first_line: bool = True
            num_line: int = 0
            for num_line, line in enumerate(lines, start=1):
                if line.strip().startswith('#') or line.strip() == '':
                    continue
                if is_first_line:
                    if not self.first_drones_line(line):
                        raise ValueError(
                            f'Line {num_line}: '
                            'The first line should be the number of drones.'
                        )
                    is_first_line = False
                if not self.extreme_zones(lines):
                    raise ValueError(
                        f'Line {num_line}: '
                        'There must be an entrance and an exit.'
                    )
                try:
                    key, value = line.strip().split(':', 1)
                except:
                    raise ValueError(f'Line {num_line}: Invalid line.')
                net_hubs: list[Hub] = [hub for hub in hubs + [start, end] if hub is not None]
                hub_names: list[str] = []
                hub_coords: list[tuple[int, int]] = []
                match key:
                    case TypeData.NUMBER_DRONES:
                        try:
                            nb_dron: int = int(value.strip())
                        except ValueError:
                            raise ValueError(
                                f'Line {num_line}: '
                                'The value of number drones must be an int.'
                            )
                        if drones is not None:
                            raise ValueError(
                                f'Line {num_line}: '
                                'Value of number drones already set.'
                            )
                        if nb_dron < 0:
                            raise ValueError(
                                f'Line {num_line}: '
                                'Invalid drone count, the number '
                                'must be positive integer.'
                            )
                        elif nb_dron == 0:
                            raise ValueError(
                                f'Line {num_line}: '
                                'Invalid drone count, the number must '
                                'be at least 1.'
                            )
                        drones = nb_dron
                    case TypeData.START_HUB | TypeData.END_HUB | TypeData.HUB:
                        data: dict[str, Any] = self.extract_data(value, num_line)
                        if len(data['values']) < 3:
                            raise ValueError(
                                f'Line {num_line}: '
                                'Hub line requires a name, '
                                'X coordinate, and Y coordinate.'
                            )
                        name, x, y = data['values']
                        hub: Hub = Hub(name, x, y, data['metadata'], num_line)
                        if key == TypeData.START_HUB:
                            if start is not None:
                                raise ValueError(
                                    f'Line {num_line}: '
                                    'Value of start hub already set.'
                                )
                            start = hub
                        elif key == TypeData.END_HUB:
                            if end is not None:
                                raise ValueError(
                                    f'Line {num_line}: '
                                    'Value of end hub already set.'
                                )
                            end = hub
                        else:
                            hubs.append(hub)
                        net_hubs.append(hub)
                    case TypeData.CONNECTION:
                        data = self.extract_data(value, num_line)
                        connections.append(
                            Connection(
                                ' '.join(data['values']),
                                data['metadata'], net_hubs, num_line
                            )
                        )
                if net_hubs:
                    hub_names = [hub.name for hub in net_hubs]
                    hub_coords = [
                        (hub.coord_x, hub.coord_y)for hub in net_hubs
                    ]
                    if len(hub_names) != len(set(hub_names)):
                        raise ValueError(
                            f'Line {num_line}: '
                            'All zones must have unique names.'
                        )
                    if len(hub_coords) != len(set(hub_coords)):
                        raise ValueError(
                            f'Line {num_line}: '
                            'All zones must have unique coords.'
                        )
                if connections:
                    net_connections: list[tuple[str, str]] = [
                        (
                            min(connection.init_hub.name, connection.final_hub.name),
                            max(connection.init_hub.name, connection.final_hub.name)
                        )
                        for connection in connections
                    ]
                    if len(net_connections) != len(set(net_connections)):
                        raise ValueError(
                            f'Line {num_line}: '
                            'All connections must have unique.'
                        )
            if is_first_line:
                raise ValueError(
                    f'Line {num_line + 1 if num_line > 0 else 1}: '
                    'The first line should be the number of drones.'
                )
            return NetworkZone(
                drones, start, end, hubs, connections
            )

    def first_drones_line(self, line: str) -> bool:
        """Verifies if the specified lines list starts with the drone count
        directive.

        Args:
            lines (str): List of configuration file lines.

        Returns:
            bool: True if the first line contains the NUMBER_DRONES key,
                False otherwise.
        """
        if not line:
            return False
        elif TypeData.NUMBER_DRONES in line:
            return True
        else:
            return False

    def extreme_zones(self, lines: list[str]) -> bool:
        """Checks whether both start and end hub definitions exist
        in the file content.

        Args:
            lines (list[str]):
                List of stripped lines from the configuration file.

        Returns:
            bool: True if both START_HUB and END_HUB keys are present,
                False otherwise.
        """
        if (
            any(TypeData.START_HUB in line for line in lines)
            and any(TypeData.END_HUB in line for line in lines)
        ):
            return True
        else:
            return False

    def extract_data(self, crude_data: str, num_line: int) -> dict[str, Any]:
        """Splits raw hub or connection line strings into arguments
        and metadata dictionaries.

        Args:
            crude_data (str): Unparsed value portion of a configuration line.

        Returns:
            dict[str, Any]: Dictionary containing 'values' list and
                'metadata' dict.

        Raises:
            ValueError: If parameters are missing before metadata or if
                more than one metadata block (`[...]`) is detected.
        """
        if crude_data.strip().startswith('['):
            raise ValueError(
                f'Line {num_line}: '
                'Missing parameters before metadata block.'
            )
        all_data: list[str] = crude_data.strip().split(' [')
        if len(all_data) > 2:
            raise ValueError(
                f'Line {num_line}: '
                'There can only be one metadata box'
            )
        data: list[str] = all_data[0].strip().split(' ')
        if len(data) > 3:
            raw_y: str = data.pop()
            raw_x: str = data.pop()
            name: str = ' '.join(data)
            data = [name, raw_x, raw_y]
        if len(all_data) == 2:
            if not all_data[1].endswith(']'):
                raise ValueError(
                    f'Line {num_line}: '
                    'Invalid metadata format.'
                )
            metadata = self.metadata_valid(all_data[1][:-1], num_line)
        else:
            if ']' in all_data[0] or '=' in all_data[0]:
                raise ValueError(
                    f'Line {num_line}: '
                    'Invalid metadata format.'
                )
            metadata = {}
        return {
            'values': [*data],
            'metadata': metadata
        }

    def metadata_valid(self, metadata: str, num_line: int) -> dict[str, Any]:
        """Parses key-value metadata strings inside square brackets
        into a dictionary.

        Args:
            metadata (str): Raw string of key=value pairs separated by spaces.

        Returns:
            dict[str, Any]: Key-value mappings of parsed metadata attributes.

        Raises:
            ValueError: If a pair lacks a key or value around the equals sign.
        """
        metadata_valid: dict[str, Any] = {}
        for data in metadata.split(' '):
            split_data = data.split('=')
            if len(split_data) != 2 or split_data[1] == '':
                raise ValueError(
                    f'Line {num_line}: '
                    'The metadata is invalid.\n'
                    'It requires a key or value separated by '
                    'an equals sign to be valid.\n'
                    'For more than one argument, separate them with spaces.'
                )
            else:
                key, val = split_data
                metadata_valid[key] = val
        return metadata_valid
