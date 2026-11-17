"""Boundary for future import readers. Preview and persistence are separate."""
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from typing import BinaryIO, Protocol


@dataclass(frozen=True)
class ImportedMovement:
    account_id: str
    charged_on: date
    signed_cents: int
    description: str
    external_id: str | None = None


class MovementReader(Protocol):
    def parse(self, source: BinaryIO, account_id: str) -> Iterable[ImportedMovement]:
        """Read normalized EUR rows without writing to the ledger."""
        ...

