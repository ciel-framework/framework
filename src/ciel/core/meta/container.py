from typing import Callable, Any, Optional, TypeVar, Generic

from mypy.memprofile import defaultdict

from .injector import Injector

T = TypeVar("T")

class BindingIdentifier(Generic[T]):

    @staticmethod
    def gen_name(contract: type) -> str:
        return f"{contract.__module__}.{contract.__qualname__}"

    def __init__(self, contract: type[T]) -> None:
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
        self._bindings: dict[BindingIdentifier[Any], Binding[Any]] = dict()
        self._singletons: dict[BindingIdentifier[Any], list[Any]] = defaultdict(list)
        self._aliases: dict[str, BindingIdentifier[Any]] = dict()

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
        self._bindings[res.id] = res
        if aliases is not None:
            for alias in aliases:
                self._aliases[alias] = res.id

    def resolve_contract(self, contract: BindingIdentifier[T] | type[T] | str) -> BindingIdentifier[T]:
        if isinstance(contract, str):
            if contract in self._aliases:
                bind_id = self._aliases[contract]
            else:
                raise KeyError(contract)
        elif isinstance(contract, type):
            bind_id = BindingIdentifier(contract)
        else:
            bind_id = contract
        return bind_id

    def get_binding(self, contract: BindingIdentifier[T] | type[T] | str) -> Binding[T]:
        bind_id = self.resolve_contract(contract)

        if bind_id not in self._bindings:
            raise KeyError(bind_id.name)

        return self._bindings[bind_id]

    def is_bound(self, contract: BindingIdentifier[T] | type[T] | str) -> bool:
        bind_id = self.resolve_contract(contract)

        return bind_id in self._bindings

    def make(self, contract: BindingIdentifier[T] | type[T] | str, *args: Any, **kwargs: Any) -> T:
        binding = self.get_binding(contract)
        if binding.singleton and self._singletons[binding.id]:
            return self._singletons[binding.id][-1]  # type: ignore
        res = binding(*args, **kwargs)
        if binding.singleton:
            self._singletons[binding.id].append(res)
        return res

    def instance(self, contract: BindingIdentifier[T] | type[T] | str, value: T) -> None:
        binding = self.get_binding(contract)
        if not binding.singleton:
            raise RuntimeError("You can only set an instance for singletons.")

        self._singletons[binding.id].append(value)

    def pop(self, contract: BindingIdentifier[T] | type[T] | str) -> T:
        binding = self.get_binding(contract)
        if not binding.singleton:
            raise RuntimeError("You can only pop an instance for singletons.")

        return self._singletons[binding.id].pop()

    def inject(self, cl: Callable[..., T]) -> Injector[T]:
        return Injector(self, cl)

    def __getitem__(self, binding: str | type[T]) -> T:
        return self.make(binding)

    def __setitem__(self, binding: str | type[T], value: T) -> None:
        self.instance(binding, value)

    def __delitem__(self, binding: str | type[T]) -> None:
        self.pop(binding)

    def __xor__(self, cl: Callable[..., T] | type) -> Injector[T]:
        return self.inject(cl)
