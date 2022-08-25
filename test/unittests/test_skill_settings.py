# write your first unittest!
import unittest

from ovos_local_backend.database.settings import SkillSettings


class TestSkillSettings(unittest.TestCase):

    def test_deserialize(self):
        meta = {"sections": [
            {
                "fields": [
                    {"name": "test", "value": True}
                ]
            }
        ]}

        data = {
            "skillMetadata": meta,
            "display_name": "Test Skill",
            "skill_gid": "test_skill",
            "identifier": "test_skill"
        }
        s = SkillSettings.deserialize(data)

        self.assertEqual(s.display_name, "Test Skill")
        self.assertEqual(s.skill_id, "test_skill")
        self.assertEqual(s.settings, {"test": True})
        self.assertEqual(s.meta, meta)

    def test_serialize(self):
        meta = {"sections": [
            {
                "fields": [
                    {"name": "test", "value": False}
                ]
            }
        ]}
        settings = {"test": True}
        updated_meta = {"sections": [
            {
                "fields": [
                    {"name": "test", "value": True}
                ]
            }
        ]}

        s = SkillSettings("test_skill", settings, meta, "Test Skill")
        self.assertEqual(s.settings, settings)
        self.assertEqual(s.meta, meta)
        self.assertEqual(s.display_name, "Test Skill")
        self.assertEqual(s.skill_id, "test_skill")

        s2 = s.serialize()
        self.assertEqual(s.meta, meta)
        self.assertEqual(s2["display_name"], "Test Skill")
        self.assertEqual(s2["skill_gid"], "test_skill")
        self.assertEqual(s2['skillMetadata'], updated_meta)
