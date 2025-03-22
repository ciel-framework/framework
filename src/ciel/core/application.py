from .config import Config
from .dependency_injection import Container
from pathlib import Path

from .service_provider import ServiceProvider


class ApplicationBuilder:

    def __init__(self: "ApplicationBuilder", base_path: Path) -> None:
        self.config_path = base_path / "config"

    def build(self):
        app = Application(
            self.config_path
        )
        app.setup()

class Application:

    def __init__(self: "Application", config_path: Path) -> None:
        self.container: Container = Container()
        self.config_path: Path = config_path
        self.services: list[ServiceProvider] = []

    def _initialize_container(self):
        self.container.singleton(self.__class__, lambda app: None)
        self.container[self.__class__] = self

        self.container.singleton(Config)

    def _register_services(self):
        for service in self.container[Config].get('app.services'):
            serv: ServiceProvider = service()
            (self.container ^ serv.register)()
            self.services.append(serv)

    def _boot(self):
        for service in self.services:
            (self.container ^ service.boot)()

    def setup(self) -> None:
        self._initialize_container()
        self._register_services()

    @staticmethod
    def configure(base_path: Path) -> ApplicationBuilder:
        return ApplicationBuilder(base_path)

    async def handle(self, scope, receive, send) -> None:
        pass


