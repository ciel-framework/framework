import unittest
from ciel.core.dependency_injection.container import Container, BindingIdentifier  # type: ignore


class A:
    pass


class B:
    pass


class TestBindingIdentifier(unittest.TestCase):

    def test_equality(self) -> None:
        id_a_1 = BindingIdentifier(A)
        id_a_2 = BindingIdentifier(A)
        id_b = BindingIdentifier(B)

        self.assertEqual(id_a_1, id_a_2)
        self.assertNotEqual(id_a_1, id_b)
        self.assertNotEqual(id_a_1, "invalid")

    def test_hash(self) -> None:
        id_a_1 = BindingIdentifier(A)
        id_a_2 = BindingIdentifier(A)
        id_b = BindingIdentifier(B)

        self.assertEqual(hash(id_a_1), hash(id_a_2))
        self.assertNotEqual(hash(id_a_1), hash(id_b))


class TestContainer(unittest.TestCase):
    def setUp(self) -> None:
        self.container = Container()

    def test_bind_and_make(self) -> None:
        class Dummy:
            pass

        self.container.transient(Dummy)
        instance = self.container.make(Dummy)
        self.assertIsInstance(instance, Dummy)

    def test_singleton(self) -> None:
        class Dummy:
            pass

        self.container.singleton(Dummy)
        instance1 = self.container.make(Dummy)
        instance2 = self.container.make(Dummy)

        self.assertIs(instance1, instance2)

    def test_transient(self) -> None:
        class Dummy:
            pass

        self.container.transient(Dummy)
        instance1 = self.container.make(Dummy)
        instance2 = self.container.make(Dummy)

        self.assertIsNot(instance1, instance2)

    def test_builder(self) -> None:
        class Dummy:
            def __init__(self, test: int = 1) -> None:
                self.test = test

        self.container.transient(Dummy, lambda: Dummy(2))
        instance = self.container.make(Dummy)

        self.assertEqual(instance.test, 2)

    def test_binding_not_found(self) -> None:
        class Dummy:
            pass

        with self.assertRaises(KeyError):
            self.container.make(Dummy)

    def test_transient_aliases(self) -> None:
        class Dummy:
            pass

        self.container.transient(Dummy, aliases=["dummy_transient"])
        instance1 = self.container.make(Dummy)
        instance2: Dummy = self.container.make("dummy_transient")

        self.assertIsInstance(instance2, Dummy)
        self.assertIsNot(instance1, instance2)

    def test_singleton_alias(self) -> None:
        class Dummy:
            pass

        self.container.singleton(Dummy, aliases=["dummy_singleton"])
        instance1 = self.container.make(Dummy)
        instance2: Dummy = self.container.make("dummy_singleton")

        self.assertIs(instance1, instance2)

    def test_instance(self) -> None:
        class Dummy:
            pass

        obj = Dummy()
        self.container.singleton(Dummy)
        self.container.instance(Dummy, obj)

        self.assertIs(self.container.make(Dummy), obj)

    def test_instance_non_singleton(self) -> None:
        class Dummy:
            pass

        obj = Dummy()
        self.container.transient(Dummy)
        with self.assertRaises(ValueError):
            self.container.instance(Dummy, obj)

    def test_getitem_setitem(self) -> None:
        class Dummy:
            pass

        obj = Dummy()
        self.container.singleton(Dummy)
        self.container[Dummy] = obj
        self.assertIs(self.container[Dummy], obj)

    def test_injection(self) -> None:
        class Dummy1:
            def __init__(self, test: int = 1) -> None:
                self.test = test

        class Dummy2:
            def __init__(self, test: Dummy1) -> None:
                self.test = test

        self.container.transient(Dummy1, lambda: Dummy1(2))
        self.container.transient(Dummy2)
        instance = self.container.make(Dummy2)

        self.assertEqual(instance.test.test, 2)
