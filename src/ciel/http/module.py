from ciel import Application
from ciel.core.module import Module, ModuleManifest
from .http_objects import Request, Response
from .kernel import HTTPKernel
from .routing import Router, Route


class HTTPModule(Module):

    def __init__(self) -> None:
        super().__init__(
            ModuleManifest("http", (0,0,1))
        )

    def register(self, app: Application) -> None:
        app.singleton(Request)
        app.singleton(Response)
        app.singleton(Route, Router)
        app.transient(HTTPKernel)
