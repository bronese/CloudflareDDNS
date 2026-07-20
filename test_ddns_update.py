#!/usr/bin/env python3
"""Regression check: stale Cloudflare DNS is updated on the first loop."""

import io
import os
import runpy
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


class StopLoop(Exception):
    pass


class Response:
    def __init__(self, *, text="", payload=None):
        self.text = text
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


class FakeRequests:
    class exceptions:
        HTTPError = ConnectionError = Timeout = RequestException = Exception

    def __init__(self):
        self.updates = []

    def get(self, url, **kwargs):
        if url.endswith("/dns_records"):
            assert kwargs["headers"] == {
                "Authorization": "Bearer test-token",
                "Content-Type": "application/json",
            }
            return Response(payload={"success": True, "result": [{
                "id": "record-id",
                "name": "home.example.com",
                "type": "A",
                "content": "198.51.100.4",
            }]})
        assert url == "https://ip.test"
        return Response(text="203.0.113.10")

    def patch(self, url, **kwargs):
        self.updates.append(kwargs["json"])
        return Response(payload={"success": True, "result": {
            "id": "record-id",
            "content": kwargs["json"]["content"],
            "comment": kwargs["json"]["comment"],
        }})


def main():
    requests = FakeRequests()
    sys.modules["requests"] = requests
    env = {
        "DOMAIN": "example.com",
        "NAME": "home",
        "TOKEN": "test-token",
        "ZONEID": "zone-id",
        "IPURL": "https://ip.test",
        "UPDATEINTERVAL": "60",
    }
    with patch.dict(os.environ, env, clear=True), \
         patch("time.sleep", side_effect=StopLoop), \
         redirect_stdout(io.StringIO()):
        try:
            runpy.run_path(str(Path(__file__).with_name("DDNS-update.py")), run_name="__main__")
        except StopLoop:
            pass

    assert len(requests.updates) == 1
    assert requests.updates[0]["content"] == "203.0.113.10"
    assert "proxied" not in requests.updates[0]


if __name__ == "__main__":
    main()
