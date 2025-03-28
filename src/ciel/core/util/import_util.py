import sys
from pathlib import Path
from typing import Any
import importlib.util


def dyn_import(name: str, path: Path, remember: bool = True) -> Any:
    spec = importlib.util.spec_from_file_location(name, str(path.absolute()))
    if not spec:
        raise ImportError(f"Can't find module {name}")
    module = importlib.util.module_from_spec(spec)
    if remember:
        sys.modules[name] = module
    loader = spec.loader
    if not loader:
        raise ImportError(f"Can't find module {name}")
    loader.exec_module(module)
    return module
