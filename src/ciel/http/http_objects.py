from collections import defaultdict
from typing import Optional, Any, Tuple, Iterable, Dict
from urllib.parse import quote, unquote

from ciel.asgi.typing import HTTPScope, ASGIVersions, ASGIReceiveCallable, ASGISendCallable


class HttpData:

    @staticmethod
    def from_query_string(data: bytes, readonly: bool = True) -> "HttpData":
        res: Dict[str, list[Optional[str]]] = defaultdict(list)
        for group in data.split(b"&"):
            kv = group.split(b"=", 1)
            res[unquote(kv[0].strip())].append(None if len(kv) == 1 else unquote(kv[1].strip()))
        return HttpData(res, readonly, False)

    @staticmethod
    def from_headers(data: Iterable[Tuple[bytes, bytes]], readonly: bool = True) -> "HttpData":
        res: Dict[str, list[Optional[str]]] = defaultdict(list)
        for key, value in data:
            res[unquote(key.strip())].append(unquote(value.strip()))
        return HttpData(res, readonly, True)

    def __init__(self, data: Optional[dict[str, list[Optional[str]]]] = None, readonly: bool = False,
                 case_insensitive: bool = False) -> None:
        self.case_insensitive: bool = case_insensitive
        if data is None:
            self.data: Dict[str, list[Optional[str]]] = defaultdict(list)
        else:
            if self.case_insensitive:
                self.data = defaultdict(list, {k.lower(): v for k, v in data.items()})
            else:
                self.data = data
        self.readonly: bool = readonly

    def __getitem__(self, key: str) -> Optional[str]:
        key = key.lower() if self.case_insensitive else key
        if key not in self.data:
            raise KeyError(key)
        return self.data[key][0]

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        key = key.lower() if self.case_insensitive else key
        if key not in self.data:
            return default
        return self.data[key][0]

    def get_all(self, key: str) -> list[Optional[str]]:
        key = key.lower() if self.case_insensitive else key
        if key not in self.data:
            return []
        return list(self.data[key]) if self.readonly else self.data[key]

    def __contains__(self, key: str) -> bool:
        key = key.lower() if self.case_insensitive else key
        return key in self.data

    def __setitem__(self, key: str, value: Optional[list[Optional[str]] | str]) -> None:
        if self.readonly:
            raise ValueError("Data is read-only")
        key = key.lower() if self.case_insensitive else key
        if isinstance(value, list):
            self.data[key] = value
        else:
            self.data[key].append(value)

    def to_headers(self) -> Iterable[Tuple[bytes, bytes]]:
        res : list[tuple[bytes, bytes]] = []
        for key, values in self.data.items():
            for value in values:
                res.append((quote(key, safe="").encode(), quote(value, safe="").encode() if value else b""))
        return res

class Request:

    @staticmethod
    async def fetch(scope: HTTPScope, receive: ASGIReceiveCallable) -> "Request":
        res = Request(scope)
        await res.fetch_body(receive)
        return res

    def __init__(self, scope: HTTPScope) -> None:
        self.asgi: ASGIVersions = scope["asgi"]
        self.http_version: str = scope["http_version"]
        self.method: str = scope["method"]
        self.scheme: str = scope["scheme"]
        self.path: str = scope["path"]
        self.raw_path: Optional[bytes] = scope.get("raw_path")
        self.query_string: bytes = scope["query_string"]
        self.query_data: HttpData = HttpData.from_query_string(self.query_string)
        self.root_path: str = scope.get("root_path", "")
        self.headers_raw: Iterable[Tuple[bytes, bytes]] = scope["headers"]
        self.headers: HttpData = HttpData.from_headers(self.headers_raw)
        self.client: Optional[Tuple[str, int]] = scope.get("client")
        self.server: Optional[Tuple[str, Optional[int]]] = scope.get("server")
        self.state: Optional[Dict[str, Any]] = scope.get("state")
        self.extensions: Optional[Dict[str, Dict[object, object]]] = scope.get("extensions")
        self.body: bytes = b""

    async def fetch_body(self, receive: ASGIReceiveCallable) -> None:

        while (res := await receive())["type"] == "http.request":
            self.body += res["body"]
            if not res["more_body"]:
                break


class Response:

    def __init__(self) -> None:
        self.status: int = 200
        self.headers: HttpData = HttpData(case_insensitive=True)
        self.body: bytes = b""

    async def send(self, send: ASGISendCallable):

        await send({
            "type": "http.response.start",
            "status": self.status,
            "headers": self.headers.to_headers(),
            "trailers": False
        })

        await send({
            "type": "http.response.body",
            "body": self.body,
            "more_body": False,
        })