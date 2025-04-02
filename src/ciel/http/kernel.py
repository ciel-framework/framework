from ciel import Application
from ciel.asgi.typing import HTTPScope, ASGIReceiveCallable, ASGISendCallable
from .http_objects import Request, Response
from .routing import Router


class HTTPKernel:

    def __init__(self, app: Application, router: Router) -> None:
        self.app: Application = app
        self.router: Router = router

    async def handle(self, scope: HTTPScope, receive: ASGIReceiveCallable, send: ASGISendCallable) -> None:
        self.app[Request] = await Request.fetch(scope, receive)
        await self.app[Response].send(send)
