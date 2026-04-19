from collections.abc import Sequence
from typing import Protocol

from hermes_pulse.models import CollectedItem, SourceRegistryEntry


class Connector(Protocol):
    id: str
    source_family: str

    def collect(self, entries: Sequence[SourceRegistryEntry]) -> list[CollectedItem]:
        ...
