import unittest
from importlib.resources import files

import agent_hub_core
import truthrail_core
from agent_hub_core.reference import ReferenceAdapter as LegacyReferenceAdapter
from agent_hub_core.validation import CONTINUITY_SCHEMA_FILES, SCHEMA_FILES
from truthrail_core.reference import ReferenceAdapter as CanonicalReferenceAdapter
from truthrail_core.validation import validate_document as canonical_validate_document


class PackagingTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(truthrail_core.__version__, "0.4.1")
        self.assertEqual(agent_hub_core.__version__, truthrail_core.__version__)

    def test_canonical_namespace_reuses_legacy_implementation(self):
        self.assertIs(CanonicalReferenceAdapter, LegacyReferenceAdapter)
        self.assertIs(canonical_validate_document, agent_hub_core.validate_document)

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
