import unittest
from importlib.resources import files

import agent_hub_core
from agent_hub_core.validation import SCHEMA_FILES


class PackagingTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(agent_hub_core.__version__, "0.1.0")

    def test_all_schemas_are_packaged(self):
        root = files("agent_hub_core.schemas.v0_1")
        for filename in SCHEMA_FILES.values():
            with self.subTest(filename=filename):
                self.assertTrue(root.joinpath(filename).is_file())


if __name__ == "__main__":
    unittest.main()
