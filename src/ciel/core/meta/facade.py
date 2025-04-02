from typing import Any, Callable, Generic, Optional, Type, TypeVar
from .container import Container

T = TypeVar("T")

class FacadeMeta(type, Generic[T]):
    def __getattr__(cls, name: str) -> Any:
        instance: T = cls.get_facade_root()
        return getattr(instance, name)


class Facade(Generic[T], metaclass=FacadeMeta):
    _container: Optional[Container] = None

    @classmethod
    def set_container(cls, container: Container) -> None:
        Facade._container = container

    @classmethod
    def get_facade_accessor(cls) -> type[T]|str:
        raise NotImplementedError("Subclasses must implement get_facade_accessor.")

    @classmethod
    def get_facade_root(cls) -> T:
        if Facade._container is None:
            raise Exception("Container has not been set on Facade.")
        return Facade._container[cls.get_facade_accessor()]

