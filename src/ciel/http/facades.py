from .http_objects import Response as ResponseObject
from ciel.core.meta import Facade

class Response(Facade[ResponseObject]):

    @classmethod
    def get_facade_accessor(cls) -> type[ResponseObject]:
        return ResponseObject
