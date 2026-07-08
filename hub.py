from typing import Any
from enum import Enum


class TypeZone(Enum):
    NORMAL = 'normal'
    BLOCKED = 'blocked'
    RESTRICTED = 'restricted'
    PRIORITY = 'priority'


class TypeColor(Enum):
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

    @classmethod
    def parser(
        name: str,
        coord_x: str,
        coord_y: str,
        metadata: dict[str, Any]
    ) -> None:
        if name.__contains__(' ') and name.__contains__('-'):
            raise ValueError(f'The name “{name}” cannot contain spaces or dashes')
        if not isinstance(coord_x, int):
            raise ValueError('The x coordinate must be an integer')
        if not isinstance(coord_y, int):
            raise ValueError('The y coordinate must be an integer')
        for data in metadata:
            match data:
                case 'zone':
                    if metadata[data] not in TypeZone:
                        raise ValueError('Invalid zone')
                case 'color':
                    if metadata[data] not in TypeColor:
                        raise ValueError('Invalid color')
                case 'max_drones':
                    if not isinstance(metadata[data], int) or metadata[data] < 1:
                        raise ValueError('max_drones must be an integer greater than 1 if you want to change it')
                case _:
                    raise ValueError(f'That metadata {data} is not valid for the Hub')