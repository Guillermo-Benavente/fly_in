from typing import Any
from hub import Hub


class Connection():
    init_hub: Hub
    final_hub: Hub
    metadata: dict[str,str]

    @classmethod
    def parser(
        metadata: dict[str, Any]
    ) -> None:
        for data in metadata:
            if data != 'max_link_capacity':
                raise ValueError(f'That metadata {data} is not valid for the Connection')