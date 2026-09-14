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
        hubs: list[Hub],
        line: int
    ) -> None:
        """Initialize a Connection instance after validation.

        Args:
            connection: Connection string using ``StartHub-EndHub`` syntax.
            metadata: Dictionary containing connection metadata.
            hubs: List of existing network hubs to bind with the connection.
            line: Source line number used in validation error messages.

        Raises:
            ValueError: If the connection syntax, hubs, or metadata are
            invalid.
        """
        self.parser(connection, metadata, hubs, line)
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
        hubs: list[Hub],
        line: int
    ) -> None:
        """Validate connection syntax, hub existence, and metadata parameters.

        Args:
            connection: Connection string formatted as ``StartHub-EndHub``.
            metadata: Dictionary containing connection metadata to validate.
            hubs: List of registered hubs in the network.
            line: Source line number used in validation error messages.

        Raises:
            ValueError: If the connection syntax is invalid, a hub does not
                exist, or metadata contains unknown keys or invalid values.
        """
        parts: list[str] = connection.split('-')
        if len(parts) != 2 or any(' ' in p for p in parts):
            raise ValueError(
                f'Line {line}: '
                f'Invalid connection syntax: {connection}'
            )
        init_hub, final_hub = parts
        if init_hub == final_hub:
            raise ValueError(
                f'Line {line}: '
                f'Duplicate connection: {connection}'
            )
        existing_hub_names: set[str] = {hub.name for hub in hubs}
        if (
            init_hub not in existing_hub_names
            or final_hub not in existing_hub_names
        ):
            raise ValueError(
                f'Line {line}: '
                f'Hubs must exist to create a connection "{connection}"'
            )
        for data in metadata:
            if data != 'max_link_capacity':
                raise ValueError(
                    f'Line {line}: '
                    f'That metadata {data} is not valid for the Connection'
                )
            else:
                try:
                    max_link_capacity: int = int(metadata[data])
                    if 1 > max_link_capacity:
                        raise ValueError
                except ValueError:
                    raise ValueError(
                        f'Line {line}: '
                        'max_link_capacity must be an '
                        'integer greater than or equal to 1'
                    )
