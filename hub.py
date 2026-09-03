"""Module for representing hubs, hub metadata, and console color formatting.

Defines enumerations for hub metadata types, zone behaviors, color themes,
ANSI console color codes, and the Hub class responsible
for modeling network nodes.
"""
from typing import Any
from strenum import StrEnum


class TypeMetadata(StrEnum):
    """Enumeration of valid metadata keys applicable to a Hub."""
    ZONE = 'zone'
    COLOR = 'color'
    MAX_DRONES = 'max_drones'


class TypeZone(StrEnum):
    """Enumeration of zone accessibility types for hubs."""
    NORMAL = 'normal'
    BLOCKED = 'blocked'
    RESTRICTED = 'restricted'
    PRIORITY = 'priority'


class TypeColor(StrEnum):
    """Enumeration of supported color themes for hub visualization."""
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
    """Enumeration of ANSI escape codes for formatted terminal output."""
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
        """Applies a multi-color rainbow gradient
        across individual characters of text.

        Args:
            text (str): The input text string to format with rainbow colors.

        Returns:
            str: An ANSI-formatted string with cyclic rainbow coloring
                per character.
        """
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
    """Represents a network hub (node) with spatial coordinates
    and metadata rules.

    Attributes:
        name (str): Unique name identifier for the hub.
        coord_x (int): Horizontal X coordinate on the grid.
        coord_y (int): Vertical Y coordinate on the grid.
        metadata (dict[str, Any]): Dictionary containing hub configuration
            (e.g. zone, color, max_drones).
        drones_number (int): Current count of drones parked at this hub.
    """
    name: str
    coord_x: int
    coord_y: int
    metadata: dict[str, Any]
    drones_number: int

    def __init__(
        self,
        name: str,
        coord_x: str,
        coord_y: str,
        metadata: dict[str, Any]
    ) -> None:
        """Initializes a Hub instance after validating name, coordinates,
        and metadata.

        Args:
            name (str): Hub name identifier.
            coord_x (str): X coordinate represented as a string.
            coord_y (str): Y coordinate represented as a string.
            metadata (dict[str, Any]): Configuration parameters for the hub.

        Raises:
            ValueError: If name syntax, coordinates,
                or metadata fail validation rules.
        """
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
        """Validates naming constraints, integer coordinate parsing,
        and metadata key/values.

        Args:
            name (str): Hub name string to check.
            coord_x (str): Raw string input for X coordinate.
            coord_y (str): Raw string input for Y coordinate.
            metadata (dict[str, Any]): Dictionary containing
                metadata to validate.

        Raises:
            ValueError: If the name contains spaces/dashes, coordinates
                are non-integers, or metadata keys and values do not
                conform to allowed enumerations and limits.
        """
        if ' ' in name or '-' in name:
            raise ValueError(
                f'The name “{name}” cannot contain spaces or dashes'
            )
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
                            raise ValueError(
                                'max_drones must be an integer greater '
                                'than 1 if you want to change it'
                            )
                    except ValueError as e:
                        if str(e):
                            raise e
                        raise ValueError(
                            'max_drones must be an positive integer'
                        )
                case _:
                    raise ValueError(
                        f'That metadata {data} is not valid for the Hub'
                    )

    def get_turn_zone(self) -> int:
        """Determines the turn duration cost required to navigate through this
            hub's zone type.

        Returns:
            int: Turn cost based on zone type
                (1 for normal/priority, 2 for restricted, -1 for blocked).
        """
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
