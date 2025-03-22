from ciel import Application
from ciel.core.service_provider import ServiceProvider


class HttpService(ServiceProvider):

    def register(self, app: Application):
        app.container.singleton()
