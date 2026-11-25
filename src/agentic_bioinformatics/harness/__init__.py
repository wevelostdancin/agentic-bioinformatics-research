from typing import Protocol, runtime_checkable


@runtime_checkable
class HarnessAdapter(Protocol):
    def run(self, config: dict) -> dict: ...
