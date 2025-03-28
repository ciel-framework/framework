from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, Optional, Self

if TYPE_CHECKING:
    from ..application import Application

@dataclass
class ModuleManifest:
    name: str
    version: tuple[int, int, int] = (0,0,0)
    dependencies: set[Self] = field(default_factory=set)

    def __repr__(self) -> str:
        return f"{self.name} v{'.'.join([str(v) for v in self.version])}"

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ModuleManifest):
            return False
        return self.name == other.name and self.version == other.version

class Module:

    def __init__(self, manifest: ModuleManifest) -> None:
        self.manifest = manifest

    def __repr__(self) -> str:
        return repr(self.manifest)

    def register(self, app: "Application") -> None:
        pass

    def boot(self, *args: Any, **kwargs: Any) -> None:
        pass

