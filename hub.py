from typing import Any
from strenum import StrEnum


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
    ORANGE = 'orange'
    PURPLE = 'purple'
    BROWN = 'brown'
    MAROON = 'maroon'
    GOLD = 'gold'
    LIME = 'lime'
    CRIMSON = 'crimson'
    VIOLET = 'violet'
    DARKRED = 'darkred'
    RAINBOW = 'rainbow'

class TypeConsoleColor(StrEnum):
    BLACK = '\033[30m'
    WHITE = '\033[97m'
    RED = '\033[31m'
    BLUE = '\033[34m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    ORANGE = '\033[38;5;208m'
    PURPLE = '\033[35m'
    BROWN = '\033[38;5;94m'
    MAROON = '\033[38;5;88m'
    GOLD = '\033[38;5;220m'
    LIME = '\033[92m'
    CRIMSON = '\033[38;5;161m'
    VIOLET = '\033[38;5;129m'
    DARKRED = '\033[38;5;88m'
    RESET = '\033[0m'
    @classmethod
    def rainbow(cls, text: str) -> str:
        palette: list[str] = [
            cls.RED,
            cls.YELLOW,
            cls.GREEN,
            cls.CYAN,
            cls.BLUE,
            cls.MAGENTA,
        ]
        colored_chars: list[str] = []
        num_colors = len(palette)
        for i, char in enumerate(text):
            color = palette[i % num_colors]
            colored_chars.append(f'{color}{char}')
        return ''.join(colored_chars) + cls.RESET

class Hub():
    name: str
    coord_x: int
    coord_y: int
    metadata: dict[str, Any]
    drones_number: int
    
    def __init__(self, name: str, coord_x: str, coord_y: str, metadata: dict[str, Any]) -> None:
        self.parser(name, coord_x, coord_y, metadata)
        self.name = name
        self.coord_x = int(coord_x)
        self.coord_y = int(coord_y)
        self.metadata = metadata
        self.drones_number: int = 0

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
                    try:
                        TypeZone(metadata[data])
                    except ValueError:
                        raise ValueError('Invalid zone')
                case TypeMetadata.COLOR:
                    try:
                        TypeColor(metadata[data])
                    except ValueError:
                        raise ValueError('Invalid color')
                case TypeMetadata.MAX_DRONES:
                    try:
                        max_drones: int = int(metadata[data])
                        if not isinstance(max_drones, int) or max_drones < 1:
                            raise ValueError('max_drones must be an integer greater than 1 if you want to change it')
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
            case _:
                return 1