"""Module for representing and validating network connections between hubs.

Defines the metadata types allowed for connections and the Connection class,
which handles modeling and validating links between two hubs in the network.
"""

from typing import Any
from hub import Hub
from strenum import StrEnum


class TypeMetadata(StrEnum):
    """Enumeration of valid metadata types applicable to a connection."""
    MAX_LINK_CAPACITY = 'max_link_capacity'


class Connection():
    """Represents a connection between two hubs.

    Attributes:
        name (str): Connection identifier formatted as 'StartHub-EndHub'.
        init_hub (Hub): Instance of the source hub.
        final_hub (Hub): Instance of the destination hub.
        metadata (dict[str, Any]):
            Connection metadata (e.g. 'max_link_capacity').
    """
    name: str
    init_hub: Hub
    final_hub: Hub
    metadata: dict[str, Any]

    def __init__(
        self,
        connection: str,
        metadata: dict[str, Any],
        hubs: list[Hub]
    ) -> None:
        """Initializes a Connection instance after validation.

        Args:
            connection (str): Connection string using 'StartHub-EndHub' syntax.
            metadata (dict[str, Any]):
                Dictionary containing connection metadata.
            hubs (list[Hub]):
                List of existing network hubs to bind with the connection.

        Raises:
            ValueError: If connection syntax, hubs, or metadata are invalid.
        """
        self.parser(connection, metadata, hubs)
        init_hub, final_hub = connection.split('-')
        self.name = connection
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
        """Validates connection syntax, hub existence, and metadata parameters.

        Args:
            connection (str): Connection string formatted as 'StartHub-EndHub'.
            metadata (dict[str, Any]): Metadata dictionary to check.
            hubs (list[Hub]): List of registered hubs in the system.

        Raises:
            ValueError:
                If connection syntax is invalid, any hub does not exist,
                or metadata contains unknown keys or non-positive
                integer values.
        """
        parts: list[str] = connection.split('-')
        if len(parts) != 2:
            raise ValueError(f'Invalid connection syntax: {connection}')
        init_hub, final_hub = parts
        existing_hub_names: set[str] = {hub.name for hub in hubs}
        if (
            init_hub not in existing_hub_names
            or final_hub not in existing_hub_names
        ):
            raise ValueError('Hubs must exist to create a connection')
        for data in metadata:
            if data != 'max_link_capacity':
                raise ValueError(
                    f'That metadata {data} is not valid for the Connection'
                )
            else:
                try:
                    max_link_capacity: int = int(metadata[data])
                    if (
                        not isinstance(max_link_capacity, int)
                        or max_link_capacity < 1
                    ):
                        raise ValueError(
                            'max_link_capacity must be an integer ',
                            'greater than 1 if you want to change it'
                        )
                except ValueError as e:
                    if str(e):
                        raise e
                    raise ValueError(
                        'max_link_capacity must be an positive integer'
                    )
