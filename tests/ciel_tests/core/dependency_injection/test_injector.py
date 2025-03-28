import unittest
from ciel.core.dependency_injection.container import Container  # type: ignore
from ciel.core.dependency_injection.injector import Injector  # type: ignore


class TestInjector(unittest.TestCase):

    def setUp(self) -> None:
        self.container = Container()
        self.container.singleton(str)
        self.container.singleton(int)
        self.container[str] = "Hello"
        self.container[int] = 42

    def test_function_no_parameters(self) -> None:
        def func() -> str:
            return "World"

        injector = Injector(self.container, func)
        result = injector()
        self.assertEqual(result, "World")

    def test_function_injection(self) -> None:
        def func(a: int, b: str) -> tuple[int, str]:
            return a, b

        injector = Injector(self.container, func)
        result = injector()
        self.assertEqual(result, (42, "Hello"))

    def test_function_with_default(self) -> None:
        def func(a: float = 69.0, b: str = "default") -> tuple[float, str]:
            return a, b

        injector = Injector(self.container, func)
        result1 = injector()
        self.assertEqual(result1, (69.0, "Hello"))

        result2 = injector(b="World")
        self.assertEqual(result2, (69.0, "World"))

    def test_missing_parameter_raises_error(self) -> None:
        def func(a, b: int) -> int:  # type: ignore
            return a + b  # type: ignore

        injector = Injector(self.container, func)

        with self.assertRaises(ValueError) as context:
            injector()
        self.assertIn("a", str(context.exception))

        res = injector(69)
        self.assertEqual(res, 42 + 69)

    def test_class_injection(self) -> None:
        # A class whose __init__ requires injection. The first parameter ("self") is skipped.
        class A:
            def __init__(self, x: int):
                self.x = x

        injector = Injector(self.container, A)
        instance = injector()
        self.assertIsInstance(instance, A)
        self.assertEqual(instance.x, 42)
