from typing import Callable, Any, TypeVar, Generic, TYPE_CHECKING
import inspect

T = TypeVar("T")

if TYPE_CHECKING:
    from .container import Container

class Parameter:

    def __init__(self, name:str) -> None:
        self.name: str = name
        self.has_default: bool = False
        self.default: Any = None
        self.annotation: type | str | None = None

    def set_default(self, default: Any) -> None:
        self.default = default
        self.has_default = True

class Injector(Generic[T]):

    def __init__(self, container: "Container", cl: Callable[..., T]) -> None:
        self.container: "Container" = container
        self.callable: Callable[..., T] = cl

        if isinstance(cl, type):
            to_inspect = cl.__init__  # type: ignore
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
                res.annotation = param.annotation

            if param.kind in [inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD]:
                self.positional.append(name)

            if param.kind in [inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD]:
                self.keywords.add(name)

            if param.kind not in [inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL]:
                self.param[name] = res


    def __call__(self, *args: Any, **kwargs: Any) -> T:
        res_args: list[Any] = list(args)
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
            if param.annotation and self.container.is_bound(param.annotation):
                res_args.append(self.container[param.annotation])
                presence.add(param.name)
            else:
                break

        for k in self.keywords:
            if k in presence:
                continue
            param = self.param[k]
            if param.annotation and self.container.is_bound(param.annotation):
                res_kwargs[k] = self.container[param.annotation]
                presence.add(param.name)

        missing = set(filter(lambda n: not self.param[n].has_default, set(self.param.keys()) - presence))
        if len(missing) > 0:
            raise ValueError(f"Missing parameters: {', '.join(missing)}")
        return self.callable(*res_args, **res_kwargs)
