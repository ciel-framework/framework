import unittest
from unittest.mock import MagicMock
from ciel.core.meta.container import Container
from ciel.core.meta.facade import Facade

class SampleService:

    def __init__(self) -> None:
        self.test: int = 42

    def method(self, value: int) -> int:
        return self.test + value

class SampleFacade(Facade[SampleService]):
    @classmethod
    def get_facade_accessor(cls) -> type[SampleService]:
        return SampleService


class TestFacade(unittest.TestCase):
    def setUp(self):
        self.container = Container()
        self.container.singleton(SampleService)
        self.service = self.container[SampleService]
        Facade.set_container(self.container)

    def test_facade_root_resolution(self):
        self.assertEqual(SampleFacade.get_facade_root(), self.service)

    def test_dynamic_method_call(self):
        self.assertEqual(SampleFacade.method(69), 42+69)

    def test_container_not_set_raises_exception(self):
        Facade._container = None
        with self.assertRaises(Exception) as context:
            SampleFacade.get_facade_root()
        self.assertEqual(str(context.exception), "Container has not been set on Facade.")
