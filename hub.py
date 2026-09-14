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
        """Apply a cyclic rainbow color effect to each character in the text.

        Args:
            text: Input text to format with rainbow colors.

        Returns:
            An ANSI-formatted string with cyclic rainbow coloring.
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
        metadata: dict[str, Any],
        line: int
    ) -> None:
        """Initialize a Hub instance after validating its data.

        Args:
            name: Hub name identifier.
            coord_x: X coordinate represented as a string.
            coord_y: Y coordinate represented as a string.
            metadata: Configuration parameters for the hub.
            line: Source line number used in validation error messages.

        Raises:
            ValueError: If the name, coordinates, or metadata fail validation.
        """
        self.parser(name, coord_x, coord_y, metadata, line)
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
        metadata: dict[str, Any],
        line: int
    ) -> None:
        """Validate hub naming, coordinates, and metadata.

        Args:
            name: Hub name to validate.
            coord_x: Raw X coordinate input.
            coord_y: Raw Y coordinate input.
            metadata: Hub metadata to validate.
            line: Source line number used in validation error messages.

        Raises:
            ValueError: If the name, coordinates, or metadata do not meet
                the required validation rules.
        """
        if ' ' in name or '-' in name:
            raise ValueError(
                f'Line {line}: '
                f'The name “{name}” cannot contain spaces or dashes'
            )
        try:
            int(coord_x)
        except ValueError:
            raise ValueError(
                f'Line {line}: '
                'The x coordinate must be an integer'
            )
        try:
            int(coord_y)
        except ValueError:
            raise ValueError(
                f'Line {line}: '
                'The y coordinate must be an integer'
            )
        for data in metadata:
            match data:
                case TypeMetadata.ZONE:
                    try:
                        TypeZone(metadata[data])
                    except ValueError:
                        raise ValueError(
                            f'Line {line}: '
                            'Invalid zone'
                        )
                case TypeMetadata.COLOR:
                    try:
                        TypeColor(metadata[data])
                    except ValueError:
                        raise ValueError(
                            f'Line {line}: '
                            'Invalid color'
                        )
                case TypeMetadata.MAX_DRONES:
                    try:
                        max_drones: int = int(metadata[data])
                        if 1 > max_drones:
                            raise ValueError
                    except ValueError:
                        raise ValueError(
                            f'Line {line}: '
                            'max_drones must be an integer '
                            'greater than or equal to 1'
                        )
                case _:
                    raise ValueError(
                        f'Line {line}: '
                        f'That metadata {data} is not valid for the Hub'
                    )

    def get_turn_zone(self) -> int:
        """Determine the turn cost associated with the hub's zone type.

        Returns:
            The turn cost: 1 for normal or priority zones, 2 for restricted
            zones, and -1 for blocked zones.
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
