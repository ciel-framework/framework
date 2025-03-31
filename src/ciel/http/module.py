from ciel import Application
from ciel.core.module import Module, ModuleManifest

class HttpModule(Module):

    def __init__(self) -> None:
        super().__init__(
            ModuleManifest("http", (0,0,1))
        )

    def register(self, app: Application) -> None:
        pass