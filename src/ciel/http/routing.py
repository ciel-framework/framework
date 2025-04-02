from pathlib import PurePosixPath
from typing import Callable

from ciel import Application

class Route:

    def __init__(self, path: PurePosixPath) -> None:
        self.path: PurePosixPath = path
        self.actions: dict[str, Callable[..., None]] = {}
        self.children: dict[PurePosixPath, Route] = {}

    def _fuse(self, node: "Route") -> None:
        assert node.path == self.path
        self.actions |= node.actions
        self.children |= node.children

    def _register(self, node: "Route") -> "Route":
        if not node.path.is_relative_to(self.path):
            raise RuntimeError(f"The route {node.path} was misregistered.")

        sub_path = node.path.relative_to(self.path)
        sub_register: list[PurePosixPath] = []
        sub_registered = False

        if sub_path == PurePosixPath(''):
            self._fuse(node)
            return self

        for child_sub_path, child in self.children.items():
            if sub_path.is_relative_to(child_sub_path):
                child._register(node)
                sub_registered = True
            elif child_sub_path.is_relative_to(sub_path):
                sub_register.append(child_sub_path)

        if not sub_registered:
            self.children[sub_path] = node

        for sub_path in sub_register:
            node._register(self.children[sub_path])
            del self.children[sub_path]

        return node

    def route(self, path: str, method: str, action: Callable[..., None]) -> "Route":
        route_path = PurePosixPath(path)
        route_path = self.path / (route_path.relative_to(PurePosixPath("/")) if route_path.is_absolute() else route_path)
        node = self._register(Route(route_path))
        node.actions[method.upper()] = action
        return node

    def group(self, path:str, routes: list["Route"]) -> "Route":
        pass

    def __repr__(self):
        return f"RouteNode({str(self.path)})"

class Router(Route):

    def __init__(self, app: Application) -> None:
        super().__init__(PurePosixPath(''))
        self.app = app

