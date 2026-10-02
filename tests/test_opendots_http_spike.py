import importlib.util
import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "spikes" / "opendots" / "provider_server.py"
CONFIG_PATH = ROOT / "spikes" / "opendots" / "demo-config.example.json"


def load_server_module():
    spec = importlib.util.spec_from_file_location(
        "truthrail_opendots_provider_server",
        SERVER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def request_json(url, *, payload=None):
    data = None
    headers = {}
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


class OpenDotsHttpSpikeTests(unittest.TestCase):
    def setUp(self):
        module = load_server_module()
        provider = module.load_provider(CONFIG_PATH)
        self.server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            module.build_handler(provider, None),
        )
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def call(self, name, arguments):
        return request_json(
            self.base_url + "/v1/call",
            payload={"name": name, "arguments": arguments},
        )["result"]

    def test_http_status_dispatch_approve_flow(self):
        tools = request_json(self.base_url + "/v1/tools")
        self.assertEqual(
            [tool["name"] for tool in tools],
            [
                "truthrail_status",
                "truthrail_dispatch",
                "truthrail_approve",
            ],
        )

        status = self.call("truthrail_status", {"project": "demo"})
        self.assertEqual(status["state"], "current")
        self.assertEqual(status["live"]["head"], "abc123")

        dispatched = self.call(
            "truthrail_dispatch",
            {
                "project": "demo",
                "requirement": "privileged_mutation",
                "capability": "repo-admin",
                "operation": "deploy",
                "acceptance_proof": ["provider state is visible"],
            },
        )
        self.assertEqual(dispatched["state"], "approval_required")
        self.assertFalse(dispatched["executed"])

        approved = self.call(
            "truthrail_approve",
            {
                "approval_id": dispatched["approval_id"],
                "approve": True,
            },
        )
        self.assertEqual(approved["state"], "approved_for_handoff")
        self.assertFalse(approved["executed"])


if __name__ == "__main__":
    unittest.main()
