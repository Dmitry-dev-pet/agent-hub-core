import unittest
from importlib.resources import files

import agent_hub_core
from agent_hub_core.validation import CONTINUITY_SCHEMA_FILES, SCHEMA_FILES


class PackagingTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(agent_hub_core.__version__, "0.2.0")

    def test_all_schemas_are_packaged(self):
        root = files("agent_hub_core.schemas.v0_1")
        for filename in SCHEMA_FILES.values():
            with self.subTest(version="0.1", filename=filename):
                self.assertTrue(root.joinpath(filename).is_file())

        root_v02 = files("agent_hub_core.schemas.v0_2")
        for filename in CONTINUITY_SCHEMA_FILES.values():
            with self.subTest(version="0.2", filename=filename):
                self.assertTrue(root_v02.joinpath(filename).is_file())


if __name__ == "__main__":
    unittest.main()
