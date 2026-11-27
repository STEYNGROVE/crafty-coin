import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import guard as g

class Tests(unittest.TestCase):

    def setUp(self):
        self.now=0
        self.guard=g.Guard(clock=lambda:self.now)
        self.token=self.guard.issue(
            "SIM-ADULT",30,"CUSTOMER"
        )

    def test_01_locks(self):
        self.assertEqual(len(g.FLAGS),12)
        g.locks()

    def test_02_session(self):
        self.assertEqual(
            self.guard.authorize(
                self.token,"ADULT"
            )["role"],"CUSTOMER"
        )

    def test_03_expiry(self):
        self.now=1800
        with self.assertRaises(PermissionError):
            self.guard.authorize(self.token,"ADULT")

    def test_04_before_expiry(self):
        self.now=1799
        self.guard.authorize(self.token,"ADULT")

    def test_05_revocation(self):
        self.guard.revoke(self.token)
        with self.assertRaises(PermissionError):
            self.guard.authorize(self.token,"ADULT")

    def test_06_unknown_token(self):
        with self.assertRaises(PermissionError):
            self.guard.authorize("invalid","ADULT")

    def test_07_domain_isolation(self):
        with self.assertRaises(PermissionError):
            self.guard.authorize(
                self.token,"EDUCATION"
            )

    def test_08_role_isolation(self):
        with self.assertRaises(PermissionError):
            self.guard.authorize(
                self.token,"ADULT",["OPERATOR"]
            )

    def test_09_child_adult_role(self):
        with self.assertRaises(PermissionError):
            self.guard.issue(
                "SIM-CHILD",12,"CUSTOMER"
            )

    def test_10_learner(self):
        token=self.guard.issue(
            "SIM-CHILD",12,"LEARNER"
        )
        self.guard.authorize(token,"EDUCATION")

    def test_11_learner_isolation(self):
        token=self.guard.issue(
            "SIM-CHILD",12,"LEARNER"
        )
        with self.assertRaises(PermissionError):
            self.guard.authorize(token,"ADULT")

    def test_12_real_identity(self):
        with self.assertRaises(PermissionError):
            self.guard.issue("REAL",30,"CUSTOMER")

    def test_13_invalid_role(self):
        with self.assertRaises(PermissionError):
            self.guard.issue("SIM-ADULT",30,"ADMIN")

    def test_14_boolean_age(self):
        with self.assertRaises(PermissionError):
            self.guard.issue(
                "SIM-ADULT",True,"CUSTOMER"
            )

    def test_15_rate_limit(self):
        for i in range(60):
            self.guard.rate_limit(self.token,"ADULT")
        with self.assertRaises(PermissionError):
            self.guard.rate_limit(self.token,"ADULT")

    def test_16_rate_window(self):
        for i in range(60):
            self.guard.rate_limit(self.token,"ADULT")
        self.now=60
        self.guard.rate_limit(self.token,"ADULT")

    def test_17_identity_rate_limit(self):
        for i in range(60):
            self.guard.rate_limit(self.token,"ADULT")
        token=self.guard.issue(
            "SIM-ADULT",30,"CUSTOMER"
        )
        with self.assertRaises(PermissionError):
            self.guard.rate_limit(token,"ADULT")

    def test_18_replay(self):
        self.guard.replay("SIM-REQUEST")
        with self.assertRaises(PermissionError):
            self.guard.replay("SIM-REQUEST")

    def test_19_invalid_replay(self):
        with self.assertRaises(ValueError):
            self.guard.replay("REAL")

    def test_20_provider_locks(self):
        for provider in (
            "GROQ","PIXELPUNK",
            "GPU_COMPUTE","GHOSTMEDIA"
        ):
            with self.assertRaises(PermissionError):
                self.guard.provider(provider)

    def test_21_unknown_provider(self):
        with self.assertRaises(PermissionError):
            self.guard.provider("UNKNOWN")

    def test_22_finance(self):
        with self.assertRaises(PermissionError):
            self.guard.financial_action()

    def test_23_child_export(self):
        with self.assertRaises(PermissionError):
            self.guard.child_export()

    def test_24_valid_request(self):
        self.assertEqual(
            g.validate_request(
                b'{"action":"test"}',
                ["action"],["action"]
            ),
            {"action":"test"}
        )

    def test_25_unknown_field(self):
        with self.assertRaises(ValueError):
            g.validate_request(
                b'{"extra":1}',["action"],[]
            )

    def test_26_missing_field(self):
        with self.assertRaises(ValueError):
            g.validate_request(
                b'{}',["action"],["action"]
            )

    def test_27_duplicate_field(self):
        with self.assertRaises(ValueError):
            g.validate_request(
                b'{"a":1,"a":2}',["a"],[]
            )

    def test_28_oversized(self):
        with self.assertRaises(ValueError):
            g.validate_request(b'x'*4097,[],[])

    def test_29_invalid_json(self):
        with self.assertRaises(ValueError):
            g.validate_request(b'broken',[],[])

    def test_30_non_object(self):
        with self.assertRaises(ValueError):
            g.validate_request(b'[]',[],[])

    def test_31_nan(self):
        with self.assertRaises(ValueError):
            g.validate_request(
                b'{"a":NaN}',["a"],[]
            )

    def test_32_token_not_stored(self):
        self.assertNotIn(
            self.token,self.guard.sessions
        )

    def test_33_adult_learner_denied(self):
        with self.assertRaises(PermissionError):
            self.guard.issue(
                "SIM-ADULT",30,"LEARNER"
            )

    def test_34_provider_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"policy.json"
            data=g.locks()
            data["providers"]["GROQ"]=True
            p.write_text(json.dumps(data))
            with patch.object(g,"POLICY",p):
                with self.assertRaises(PermissionError):
                    g.locks()

    def test_35_missing_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"policy.json"
            data=g.locks()
            del data["providers"]["GROQ"]
            p.write_text(json.dumps(data))
            with patch.object(g,"POLICY",p):
                with self.assertRaises(PermissionError):
                    g.locks()

    def test_36_missing_financial_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"config"
            p.mkdir()
            data=json.loads(
                (g.ROOT/"config/security.json").read_text()
            )
            del data["mainnetEnabled"]
            (p/"security.json").write_text(
                json.dumps(data)
            )
            with patch.object(g,"ROOT",Path(tmp)):
                with self.assertRaises(PermissionError):
                    g.locks()

if __name__=="__main__":
    unittest.main(verbosity=2)
