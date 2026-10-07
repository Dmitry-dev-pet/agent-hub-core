import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class SkillBundleTests(unittest.TestCase):
    def test_declared_skills_resolve_to_matching_contracts(self):
        bundle = yaml.safe_load(
            (ROOT / "skills" / "default-assistant.yaml").read_text(encoding="utf-8")
        )

        groups = ("default_skills", "setup_skills", "optional_skills")
        skill_ids = [
            skill_id
            for group in groups
            for skill_id in bundle.get(group, [])
        ]

        self.assertEqual(len(skill_ids), len(set(skill_ids)))

        for skill_id in skill_ids:
            with self.subTest(skill=skill_id):
                path = ROOT / "skills" / skill_id / "SKILL.md"
                self.assertTrue(path.is_file(), f"missing contract for {skill_id}")

                text = path.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"))
                parts = text.split("---", 2)
                self.assertGreaterEqual(len(parts), 3)
                metadata = yaml.safe_load(parts[1])
                self.assertEqual(metadata["name"], skill_id)


if __name__ == "__main__":
    unittest.main()
