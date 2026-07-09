from typing import Any
from hub import Hub


class Connection():
    init_hub: Hub
    final_hub: Hub
    metadata: dict[str, Any]

    def __init__(self, connection: str, metadata: dict[str, Any], hubs: list[Hub]):
        self.parser(connection, metadata, hubs)
        init_hub, final_hub = connection.split('-')
        self.metadata = metadata
        for hub in hubs:
            if hub.name == init_hub:
                self.init_hub = hub
            if hub.name == final_hub:
                self.final_hub = hub

    @staticmethod
    def parser(
        connection: str,
        metadata: dict[str, Any],
        hubs: list[Hub]
    ) -> None:
        init_hub, final_hub = connection.split('-')
        existing_hub_names: set[str] = {hub.name for hub in hubs}
        if init_hub not in existing_hub_names or final_hub not in existing_hub_names:
            raise ValueError('Hubs must exist to create a connection')
        for data in metadata:
            if data != 'max_link_capacity':
                raise ValueError(f'That metadata {data} is not valid for the Connection')
            else:
                try:
                    max_link_capacity: int = int(metadata[data])
                    if not isinstance(max_link_capacity, int) or max_link_capacity < 1:
                        raise ValueError( 'max_link_capacity must be an integer greater than 1 if you want to change it')
                except ValueError as e:
                    if str(e):
                            raise e
                    raise ValueError('max_link_capacity must be an positive integer')