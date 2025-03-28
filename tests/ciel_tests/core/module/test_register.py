import unittest
from random import shuffle

from ciel.core.module import ModuleManifest, Module, ModuleRegister  # type: ignore


class TestModuleRegister(unittest.TestCase):

    def test_no_dependencies(self) -> None:
        manifest_a = ModuleManifest("A")
        module_a = Module(manifest_a)
        register = ModuleRegister([module_a])
        self.assertEqual(register.modules, [module_a])

    def test_simple_order(self) -> None:
        manifest_a = ModuleManifest("A")
        manifest_b = ModuleManifest("B", dependencies={manifest_a})
        manifest_c = ModuleManifest("C", dependencies={manifest_b})
        module_a = Module(manifest_a)
        module_b = Module(manifest_b)
        module_c = Module(manifest_c)

        mod = [
            module_a,
            module_b,
            module_c,
        ]

        shuffle(mod)

        register = ModuleRegister(mod)
        modules_order = register.modules

        self.assertLess(modules_order.index(module_a), modules_order.index(module_b))
        self.assertLess(modules_order.index(module_b), modules_order.index(module_c))

    def test_complex_order(self) -> None:
        manifest_a = ModuleManifest("A")
        manifest_b = ModuleManifest("B")
        manifest_c = ModuleManifest("C")
        manifest_d = ModuleManifest("D", dependencies={manifest_a, manifest_b})
        manifest_e = ModuleManifest("E", dependencies={manifest_b, manifest_c})
        manifest_f = ModuleManifest("F", dependencies={manifest_d})
        manifest_g = ModuleManifest("G", dependencies={manifest_d, manifest_e})
        manifest_h = ModuleManifest("H", dependencies={manifest_c, manifest_d})

        module_a = Module(manifest_a)
        module_b = Module(manifest_b)
        module_c = Module(manifest_c)
        module_d = Module(manifest_d)
        module_e = Module(manifest_e)
        module_f = Module(manifest_f)
        module_g = Module(manifest_g)
        module_h = Module(manifest_h)

        mod = [
            module_a,
            module_b,
            module_c,
            module_d,
            module_e,
            module_f,
            module_g,
            module_h,
        ]

        shuffle(mod)

        register = ModuleRegister(mod)
        modules_order = register.modules

        self.assertLess(modules_order.index(module_a), modules_order.index(module_d))
        self.assertLess(modules_order.index(module_b), modules_order.index(module_d))
        self.assertLess(modules_order.index(module_b), modules_order.index(module_e))
        self.assertLess(modules_order.index(module_c), modules_order.index(module_e))
        self.assertLess(modules_order.index(module_d), modules_order.index(module_f))
        self.assertLess(modules_order.index(module_d), modules_order.index(module_g))
        self.assertLess(modules_order.index(module_e), modules_order.index(module_g))
        self.assertLess(modules_order.index(module_c), modules_order.index(module_h))
        self.assertLess(modules_order.index(module_d), modules_order.index(module_h))

    def test_missing_dependency(self) -> None:
        manifest_a = ModuleManifest("A")
        manifest_b = ModuleManifest("B", dependencies={manifest_a})
        module_b = Module(manifest_b)

        with self.assertRaises(ValueError):
            ModuleRegister([module_b])

    def test_cycle(self) -> None:
        manifest_a = ModuleManifest("A")
        manifest_b = ModuleManifest("B")
        # Create a circular dependency:
        manifest_a.dependencies = {manifest_b}
        manifest_b.dependencies = {manifest_a}
        module_a = Module(manifest_a)
        module_b = Module(manifest_b)

        with self.assertRaises(RuntimeError):
            ModuleRegister([module_a, module_b])
