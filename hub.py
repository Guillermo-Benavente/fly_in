from typing import Any


class Hub():
    name: str
    coord_x: int
    coord_y: int
    metadata: dict[str,str]

    @classmethod
    def parser(
        self,
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
        
