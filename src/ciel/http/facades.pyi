from .http_objects import Response as ResponseObject
from ciel.core.meta import Facade

class Response(Facade[ResponseObject]):
    def response(self, body: str | bytes, status: int = 200) -> ResponseObject: ...

    def header(self, key: str, value: str) -> ResponseObject: ...