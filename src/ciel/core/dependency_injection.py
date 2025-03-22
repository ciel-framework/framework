from typing import Callable, Any
import inspect

class Parameter:

    def __init__(self, name:str) -> None:
        self.name: str = name
        self.has_default: bool = False
        self.default: Any = None
        self.has_annotation: bool = False
        self.annotation: type | str | None = None

    def set_annotation(self, annotation: str | type) -> None:
        self.annotation = annotation
        self.has_annotation = True

    def set_default(self, default: Any) -> None:
        self.default = default
        self.has_default = True

class Injector:

    def __init__(self, container: "Container", cl: Callable | type) -> None:
        self.container: "Container" = container
        self.callable: Callable|type = cl

        if isinstance(cl, type):
            to_inspect = cl.__init__
            skip = True
        else:
            to_inspect = cl
            skip = False

        self.param: dict[str, Parameter] = {}
        self.positional: list[str] = list()
        self.keywords: set[str] = set()
        signature = inspect.signature(to_inspect)
        for name, param in signature.parameters.items():
            if skip:
                skip = False
                continue
            res = Parameter(name)
            if param.default is not param.empty:
                res.set_default(param.default)
            if param.annotation is not param.empty:
                res.set_annotation(param.annotation)

            if param.kind in [inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD]:
                self.positional.append(name)

            if param.kind in [inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD]:
                self.keywords.add(name)

            if param.kind not in [inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL]:
                self.param[name] = res


    def __call__(self, *args, **kwargs) -> Any:
        res_args = list(args)
        res_kwargs = dict(kwargs)
        presence = set()

        for i in range(len(res_args)):
            presence.add(self.positional[i])
        for k in res_kwargs.keys():
            if k in self.keywords:
                presence.add(k)

        for i in range(len(res_args), len(self.positional)):
            if self.positional[i] in presence:
                break
            param = self.param[self.positional[i]]
            if param.has_annotation:
                res_args.append(self.container.make(param.annotation))
                presence.add(param.name)
            else:
                break

        for k in self.keywords:
            if k in presence:
                continue
            param = self.param[k]
            if param.has_annotation:
                res_kwargs[k] = self.container.make(param.annotation)
                presence.add(param.name)

        missing = set(filter(lambda n: not self.param[n].has_default, set(self.param.keys()) - presence))
        if len(missing) > 0:
            raise ValueError(f"Missing parameters: {', '.join(missing)}")
        return self.callable(*res_args, **res_kwargs)


def _binding_name(binding: str | type) -> str:
    if isinstance(binding, type):
        binding = f"{binding.__qualname__}"
    return binding


class Binding:

    def __init__(self, container: "Container", binding: str | type, builder: Callable | type | None,
                 scope: str = "global", singleton: bool = False) -> None:
        if builder is None:
            if not isinstance(binding, type):
                raise TypeError("String bindings must provide a builder")
            builder = binding

        self.name: str = _binding_name(binding)
        self.scope: str = scope
        self.builder: Injector = container ^ builder
        self.singleton: bool = singleton

    def __eq__(self, other: "Binding") -> bool:
        if isinstance(other, Binding):
            return self.name == other.name
        return False

    def __hash__(self) -> int:
        return hash(self.name)

    def __call__(self, *args, **kwargs) -> Any:
        return self.builder(*args, **kwargs)


class Container:
    def __init__(self: "Container", parent: "Container|None" = None) -> None:
        self.parent: Container|None = parent
        self.bindings: dict[str, Binding] = dict()
        self.scopes: dict[str, dict[str, Any]] = {"global": dict()} if parent is None else dict()

    def bind(self, name: str | type, builder: Callable | type | None = None, scope: str = "global") -> None:
        res = Binding(self, name, builder, scope, False)
        self.bindings[res.name] = res

    def singleton(self, name: str | type, builder: Callable | type | None = None, scope: str = "global") -> None:
        res = Binding(self, name, builder, scope, True)
        self.bindings[res.name] = res
    
    def get_binding(self, binding: str | type) -> Binding:
        name = _binding_name(binding)
        if name in self.bindings:
            return self.bindings[name]
        if self.parent is not None:
            return self.parent.get_binding(binding)
        raise KeyError(name)

    def get_scope(self, scope: str) -> dict[str, Any]:
        if scope in self.scopes:
            return self.scopes[scope]
        if self.parent is not None:
            return self.parent.get_scope(scope)
        raise KeyError(scope)

    def init_scope(self, scope: str, value: dict|None = None) -> None:
        if scope == "global":
            raise TypeError("Global scope cannot be initialized")

        if value is None:
            value = dict()

        self.scopes[scope] = value

    def make(self, binding: str | type, *args, **kwargs) -> Any:
        binding = self.get_binding(binding)
        scope = self.get_scope(binding.scope)
        if binding.singleton and binding.name in scope:
            return scope[binding.name]
        res = binding(*args, **kwargs)
        if binding.singleton:
            scope[binding.name] = res
        return res

    def instance(self, binding: str | type, value: Any) -> None:
        binding = self.get_binding(binding)
        if not binding.singleton:
            raise ValueError("You can only set a instance for singletons.")
        scope = self.get_scope(binding.scope)

        scope[binding.name] = value

    def inject(self, cl: Callable | type) -> Injector:
        return Injector(self, cl)

    def branch(self) -> "Container":
        return Container(self)

    def branch_for_scope(self, scope: str, value: dict|None = None) -> "Container":
        res = self.branch()
        res.init_scope(scope, value)
        return res

    def __getitem__(self: "Container", binding: str|type) -> Any:
        return self.make(binding)

    def __setitem__(self: "Container", binding: str|type, value: Any) -> None:
        self.instance(binding, value)

    def __xor__(self, cl: Callable | type) -> Injector:
        return self.inject(cl)

