import unittest

from agent_hub_core.conformance import run_scenario


class ConformanceTests(unittest.TestCase):
    def test_reference_scenario(self):
        result = run_scenario()
        self.assertEqual(result["read_level"], "L0")
        self.assertEqual(result["direct_mutation_level"], "L1")
        self.assertEqual(result["privileged_level"], "L2")
        self.assertEqual(result["runtime_level"], "L3")
        self.assertEqual(result["coding_agent_level"], "L4")
        self.assertEqual(result["machine_bound_level"], "L5")
        self.assertTrue(result["operator_only_rejected"])
        self.assertEqual(result["receipt_status"], "executed")
        self.assertEqual(result["verification_status"], "verified")
        self.assertTrue(result["fresh_recovery_matches"])


if __name__ == "__main__":
    unittest.main()
