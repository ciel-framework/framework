from .dependency_injection import Container
from pathlib import Path
from .module import ModuleRegister, ModuleManifest


class Application(Container, ModuleRegister):

    def _initialize_container(self) -> None:
        self.singleton(Application, aliases=["Application"])
        self[Application] = self

        for mod in self.modules:
            mod.register(self)

    def _boot(self) -> None:
        for mod in self.modules:
            (self ^ mod.boot)()

    def __init__(self, base_path: Path, modules: list[ModuleManifest]) -> None:
        self.base_path: Path = base_path

        Container.__init__(self)
        ModuleRegister.__init__(self, modules)

        self._initialize_container()


