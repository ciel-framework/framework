from typing import Callable, Any, Optional, TypeVar, Generic
from .injector import Injector

T = TypeVar("T")


class BindingIdentifier(Generic[T]):

    @staticmethod
    def gen_name(contract: type) -> str:
        return f"{contract.__module__}.{contract.__qualname__}"

    def __init__(self, contract: type[T]):
        self.contract = contract
        self.name = BindingIdentifier.gen_name(contract)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BindingIdentifier):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


class Binding(Generic[T]):

    def __init__(self, container: "Container", contract: type[T], builder: Optional[Callable[..., T]],
                 singleton: bool = False) -> None:
        if builder is None:
            builder = contract

        self.contract: type = contract
        self.id: BindingIdentifier[T] = BindingIdentifier(contract)
        self.builder: Injector[T] = container ^ builder
        self.singleton: bool = singleton

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        return self.builder(*args, **kwargs)


class Container:
    def __init__(self) -> None:
        self.bindings: dict[BindingIdentifier[Any], Binding[Any]] = dict()
        self.singletons: dict[BindingIdentifier[Any], Any] = dict()
        self.aliases: dict[str, BindingIdentifier[Any]] = dict()

    def transient(
            self,
            contract: type[T],
            builder: Optional[Callable[..., T]] = None,
            aliases: Optional[list[str]] = None) -> None:
        self._bind(contract, builder, aliases, False)

    def singleton(self, contract: type[T], builder: Optional[Callable[..., T]] = None,
                  aliases: Optional[list[str]] = None) -> None:
        self._bind(contract, builder, aliases, True)

    def _bind(self, contract: type[T], builder: Optional[Callable[..., T]], aliases: Optional[list[str]],
              singleton: bool) -> None:
        res = Binding(self, contract, builder, singleton)
        self.bindings[res.id] = res
        if aliases is not None:
            for alias in aliases:
                self.aliases[alias] = res.id

    def get_binding(self, contract: BindingIdentifier[T] | type[T] | str) -> Binding[T]:
        if isinstance(contract, str):
            if contract in self.aliases:
                bind_id = self.aliases[contract]
            else:
                raise KeyError(contract)
        elif isinstance(contract, type):
            bind_id = BindingIdentifier(contract)
        else:
            bind_id = contract

        if bind_id not in self.bindings:
            raise KeyError(bind_id.name)

        return self.bindings[bind_id]

    def is_bound(self, contract: BindingIdentifier[T] | type[T] | str) -> bool:
        if isinstance(contract, str):
            if contract in self.aliases:
                bind_id = self.aliases[contract]
            else:
                raise KeyError(contract)
        elif isinstance(contract, type):
            bind_id = BindingIdentifier(contract)
        else:
            bind_id = contract

        return bind_id in self.bindings

    def make(self, contract: BindingIdentifier[T] | type[T] | str, *args: Any, **kwargs: Any) -> T:
        binding = self.get_binding(contract)
        if binding.singleton and binding.id in self.singletons:
            return self.singletons[binding.id]  # type: ignore
        res = binding(*args, **kwargs)
        if binding.singleton:
            self.singletons[binding.id] = res
        return res

    def instance(self, contract: BindingIdentifier[T] | type[T] | str, value: T) -> None:
        binding = self.get_binding(contract)
        if not binding.singleton:
            raise ValueError("You can only set a instance for singletons.")

        self.singletons[binding.id] = value

    def inject(self, cl: Callable[..., T]) -> Injector[T]:
        return Injector(self, cl)

    def __getitem__(self, binding: str | type[T]) -> T:
        return self.make(binding)

    def __setitem__(self, binding: str | type[T], value: T) -> None:
        self.instance(binding, value)

    def __xor__(self, cl: Callable[..., T] | type) -> Injector[T]:
        return self.inject(cl)
