import unittest
from unittest.mock import AsyncMock

from ciel.http import Request, Response
from ciel.http.http_objects import HttpData


class TestHttpData(unittest.TestCase):

    def test_from_query_string(self):
        data = b"key1=value1&key2=value2"
        http_data = HttpData.from_query_string(data)
        self.assertEqual(http_data["key1"], "value1")
        self.assertEqual(http_data["key2"], "value2")

    def test_from_headers(self):
        headers = [(b"Content-Type", b"application/json")]
        http_data = HttpData.from_headers(headers)
        self.assertEqual(http_data["Content-Type"], "application/json")

    def test_get(self):
        http_data = HttpData({"key": ["value"]})
        self.assertEqual(http_data.get("key"), "value")
        self.assertIsNone(http_data.get("missing"))

    def test_get_all(self):
        http_data = HttpData({"key": ["value1", "value2"]})
        self.assertEqual(http_data.get_all("key"), ["value1", "value2"])

    def test_setitem(self):
        http_data = HttpData()
        http_data["key"] = "value"
        self.assertEqual(http_data["key"], "value")

    def test_readonly_setitem(self):
        http_data = HttpData(readonly=True)
        with self.assertRaises(ValueError):
            http_data["key"] = "value"

    def test_to_headers(self):
        http_data = HttpData({"Content-Type": ["application/json"]})
        headers = list(http_data.to_headers())
        self.assertIn((b"Content-Type", b"application%2Fjson"), headers)


class TestRequest(unittest.IsolatedAsyncioTestCase):

    async def test_fetch(self):
        scope = {
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "https",
            "path": "/test",
            "raw_path": b"/test",
            "query_string": b"key=value&foo=bar",
            "headers": [
                (b"host", b"example.com"),
                (b"content-type", b"application/json")
            ],
            "client": ("127.0.0.1", 12345),
            "server": ("example.com", 443),
            "root_path": "/app",
            "state": {"user": "tester"},
            "extensions": {"ext1": {"key": "value"}},
        }

        # Simulate receiving the body in multiple parts
        receive_mock = AsyncMock()
        receive_mock.side_effect = [
            {"type": "http.request", "body": b"Hello, ", "more_body": True},
            {"type": "http.request", "body": b"World!", "more_body": False},
        ]

        request = await Request.fetch(scope, receive_mock)

        # Check basic scope values
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.path, "/test")
        self.assertEqual(request.raw_path, b"/test")
        self.assertEqual(request.query_string, b"key=value&foo=bar")
        self.assertEqual(request.client, ("127.0.0.1", 12345))
        self.assertEqual(request.server, ("example.com", 443))
        self.assertEqual(request.root_path, "/app")
        self.assertEqual(request.state, {"user": "tester"})
        self.assertEqual(request.extensions, {"ext1": {"key": "value"}})
        self.assertEqual(request.body, b"Hello, World!")


class TestResponse(unittest.IsolatedAsyncioTestCase):

    async def test_send(self):
        response = Response()
        response.status = 200
        response.body = b"Hello, World!"
        response.headers["Content-Type"] = "text/plain"

        send_mock = AsyncMock()
        await response.send(send_mock)

        send_mock.assert_any_call({
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text%2Fplain")],
            "trailers": False,
        })
        send_mock.assert_any_call({
            "type": "http.response.body",
            "body": b"Hello, World!",
            "more_body": False,
        })