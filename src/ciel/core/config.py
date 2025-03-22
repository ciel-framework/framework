from typing import Any
from pathlib import Path
from ciel.meta.import_util import dyn_import

class Config:

    def __init__(self, app: "Application") -> None:
        super().__init__({})
        self.path: Path = app.config_path
        self.data: dict[str, Any] = dict()

    def load(self, conf_name:str) -> None:
        file = self.path / f"{conf_name}.py"
        if not file.exists() or not file.is_file():
            raise KeyError(conf_name)
        self.data[conf_name] = dyn_import(f"__config__.{conf_name}", file, False).conf


    def get(self, item: str) -> Any:
        path = item.split(".")

        if not item[0] in self.data:
            self.load(item[0])

        res = self.data
        for p in path:
            res = res[p]
        return res

    def get_or(self, item: str, default: Any) -> Any:
        try:
            return self.get(item)
        except KeyError as e:
            return default

