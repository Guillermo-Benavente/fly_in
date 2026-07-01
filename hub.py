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
        metadata: str
    ) -> bool:
        if not name.__contains__(' ') and not name.__contains__('-'):
            self.name = name
        else:
            raise ValueError('')
        if isinstance(coord_x, int):
            self.coord_x = coord_x
        else:
            raise ValueError('')
        if isinstance(coord_y, int):
            self.coord_y = coord_y
        else:
            raise ValueError('')