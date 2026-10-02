from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from agent_hub_core.reference import ReferenceAdapter
from agent_hub_core.tool_provider import ToolProviderError, TruthrailToolProvider


def load_provider(path: Path) -> TruthrailToolProvider:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "instance",
        "live_state",
        "control_plane_contracts",
        "actor",
        "owner",
    }
    if set(payload) != required:
        raise ValueError(
            "config must contain exactly: "
            + ", ".join(sorted(required))
        )
    adapter = ReferenceAdapter(
        payload["instance"],
        payload["live_state"],
        payload["control_plane_contracts"],
    )
    return TruthrailToolProvider(
        adapter,
        payload["control_plane_contracts"],
        actor=payload["actor"],
        owner=payload["owner"],
    )


def build_handler(provider: TruthrailToolProvider, token: str | None):
    class Handler(BaseHTTPRequestHandler):
        server_version = "TruthrailToolProvider/0.1"

        def _json(self, status: int, payload: dict[str, Any] | list[Any]) -> None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _authorized(self) -> bool:
            if token is None:
                return True
            return self.headers.get("Authorization") == f"Bearer {token}"

        def do_GET(self) -> None:
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            if self.path == "/v1/tools":
                self._json(200, provider.list_tools())
                return
            self._json(404, {"error": "not found"})

        def do_POST(self) -> None:
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            if self.path != "/v1/call":
                self._json(404, {"error": "not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._json(400, {"error": "invalid content length"})
                return
            if length <= 0 or length > 1_000_000:
                self._json(413, {"error": "invalid request size"})
                return
            try:
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ToolProviderError("request body must be an object")
                if set(payload) != {"name", "arguments"}:
                    raise ToolProviderError(
                        "request body must contain name and arguments"
                    )
                result = provider.call(payload["name"], payload["arguments"])
            except (json.JSONDecodeError, ToolProviderError, TypeError, ValueError) as exc:
                self._json(400, {"error": str(exc)})
                return
            self._json(200, {"result": result})

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Local HTTP boundary for the OpenDots/Truthrail spike."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args(argv)

    token = os.environ.get("TRUTHRAIL_PROVIDER_TOKEN")
    if args.host not in {"127.0.0.1", "::1", "localhost"} and not token:
        parser.error(
            "TRUTHRAIL_PROVIDER_TOKEN is required when binding beyond loopback"
        )

    provider = load_provider(args.config)
    server = ThreadingHTTPServer(
        (args.host, args.port),
        build_handler(provider, token),
    )
    print(f"Truthrail tool provider listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
