import json
import unittest
from pathlib import Path
import provider

ROOT=Path(__file__).resolve().parent

REGISTRY=json.loads(
    (ROOT/"model-registry.json").read_text()
)

class Tests(unittest.TestCase):

    def test_provider_locks(self):
        provider.verify_locks()

    def test_generation_denied(self):
        with self.assertRaises(PermissionError):
            provider.generate("test")

    def test_child_ai_disabled(self):
        self.assertFalse(REGISTRY["childLiveAIEnabled"])

    def test_live_generation_disabled(self):
        self.assertFalse(REGISTRY["liveGenerationEnabled"])

    def test_cloud_speech_disabled(self):
        self.assertFalse(REGISTRY["cloudSpeechEnabled"])

    def test_microphone_upload_disabled(self):
        self.assertFalse(REGISTRY["microphoneUploadEnabled"])

    def test_financial_actions_disabled(self):
        self.assertFalse(
            REGISTRY["automaticFinancialActions"]
        )

    def test_publishing_disabled(self):
        self.assertFalse(
            REGISTRY["automaticPublishing"]
        )

    def test_paid_upgrade_disabled(self):
        self.assertFalse(
            REGISTRY["automaticPaidUpgrade"]
        )

    def test_zero_budget(self):
        self.assertEqual(
            REGISTRY["maximumAuthorizedExpenditureZAR"],0
        )

    def test_roles_registered(self):
        self.assertEqual(len(REGISTRY["roles"]),11)

    def test_all_roles_disabled(self):
        for role in REGISTRY["roles"].values():
            self.assertFalse(role["enabled"])

    def test_no_false_capability_claims(self):
        for role in REGISTRY["roles"].values():
            self.assertFalse(role["capabilityVerified"])

    def test_discovery_only(self):
        self.assertEqual(
            REGISTRY["mode"],"DISCOVERY_ONLY"
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
