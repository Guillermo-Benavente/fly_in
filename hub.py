from typing import Any
from enum import StrEnum


class TypeMetadata(StrEnum):
    ZONE = 'zone'
    COLOR = 'color'
    MAX_DRONES = 'max_drones'


class TypeZone(StrEnum):
    NORMAL = 'normal'
    BLOCKED = 'blocked'
    RESTRICTED = 'restricted'
    PRIORITY = 'priority'


class TypeColor(StrEnum):
    BLACK = 'black'
    WHITE = 'white'
    RED = 'red'
    BLUE = 'blue'
    GREEN = 'green'
    YELLOW = 'yellow'
    MAGENTA = 'magenta'
    CYAN = 'cyan'


class Hub():
    name: str
    coord_x: int
    coord_y: int
    metadata: dict[str, Any]
    
    def __init__(self, name: str, coord_x: str, coord_y: str, metadata: dict[str, Any]) -> None:
        self.parser(name, coord_x, coord_y, metadata)
        self.name = name
        self.coord_x = int(coord_x)
        self.coord_y = int(coord_y)
        self.metadata = metadata

    @staticmethod
    def parser(
        name: str,
        coord_x: str,
        coord_y: str,
        metadata: dict[str, Any]
    ) -> None:
        if ' ' in name or '-' in name:
            raise ValueError(f'The name “{name}” cannot contain spaces or dashes')
        try:
            int(coord_x)
        except ValueError:
            raise ValueError('The x coordinate must be an integer')
        try:
            int(coord_y)
        except ValueError:
            raise ValueError('The y coordinate must be an integer')
        for data in metadata:
            match data:
                case TypeMetadata.ZONE:
                    if metadata[data] not in TypeZone:
                        raise ValueError('Invalid zone')
                case TypeMetadata.COLOR:
                    if metadata[data] not in TypeColor:
                        raise ValueError('Invalid color')
                case TypeMetadata.MAX_DRONES:
                    try:
                        max_drones: int = int(metadata[data])
                        if not isinstance(max_drones, int) or max_drones < 1:
                            raise ValueError( 'max_drones must be an integer greater than 1 if you want to change it')
                    except ValueError as e:
                        if str(e):
                                raise e
                        raise ValueError('max_drones must be an positive integer')
                case _:
                    raise ValueError(f'That metadata {data} is not valid for the Hub')

    def get_turn_zone(self) -> int:
        match self.metadata.get(TypeMetadata.ZONE):
            case TypeZone.NORMAL:
                return 1
            case TypeZone.BLOCKED:
                return -1
            case TypeZone.RESTRICTED:
                return 2
            case TypeZone.PRIORITY:
                return 1