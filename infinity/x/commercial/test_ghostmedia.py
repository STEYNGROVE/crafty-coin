import unittest
from unittest.mock import patch
import ghostmedia as g

class Tests(unittest.TestCase):

    def draft(self):
        return g.draft(
            30,"FACELESS_VIDEO",
            "Synthetic media request"
        )

    def test_locks(self):
        g.locks()

    def test_service_count(self):
        self.assertEqual(len(g.SERVICES),8)

    def test_all_services(self):
        for service in g.SERVICES:
            self.assertEqual(
                g.draft(30,service,"Test request")["status"],
                "LOCAL_DRAFT"
            )

    def test_child_denied(self):
        with self.assertRaises(PermissionError):
            g.draft(17,"SHORTS","Test request")

    def test_adult_boundary(self):
        self.assertEqual(
            g.draft(18,"SHORTS","Test request")["domain"],
            "ADULT"
        )

    def test_invalid_age(self):
        for age in (True,"30",-1,121):
            with self.assertRaises(PermissionError):
                g.draft(age,"SHORTS","Test request")

    def test_invalid_service(self):
        with self.assertRaises(ValueError):
            g.draft(30,"UNKNOWN","Test request")

    def test_invalid_description(self):
        for value in ("","abc",None,123,"x"*1001):
            with self.assertRaises(ValueError):
                g.draft(30,"SHORTS",value)

    def test_invalid_quantity(self):
        for value in (0,-1,101,True,1.5):
            with self.assertRaises(ValueError):
                g.draft(30,"SHORTS","Test request",value)

    def test_zero_expenditure(self):
        self.assertEqual(
            self.draft()["actualExpenditureZAR"],0
        )

    def test_no_generation(self):
        self.assertFalse(self.draft()["generated"])

    def test_no_publishing(self):
        self.assertFalse(self.draft()["published"])

    def test_no_submission(self):
        self.assertFalse(self.draft()["submitted"])

    def test_nonbinding(self):
        self.assertFalse(self.draft()["bindingQuote"])

    def test_generation_blocked(self):
        with self.assertRaises(PermissionError):
            g.generate()

    def test_publishing_blocked(self):
        with self.assertRaises(PermissionError):
            g.publish()

    def test_submission_blocked(self):
        with self.assertRaises(PermissionError):
            g.submit()

    def test_channel_blocked(self):
        with self.assertRaises(PermissionError):
            g.channel_access()

    def test_purchase_blocked(self):
        with self.assertRaises(PermissionError):
            g.purchase()

    def test_child_data_blocked(self):
        with self.assertRaises(PermissionError):
            g.child_data()

    def test_deployment_blocked(self):
        with self.assertRaises(PermissionError):
            g.deployment_change()

    def test_public_health_only(self):
        self.assertEqual(g.HEALTH_URL,g.BASE+"/health")

    def test_provider_outage(self):
        with patch(
            "urllib.request.OpenerDirector.open",
            side_effect=TimeoutError()
        ):
            result=g.health()
            self.assertFalse(result["reachable"])
            self.assertFalse(result["healthSchemaVerified"])
            self.assertEqual(
                self.draft()["status"],"LOCAL_DRAFT"
            )

    def test_draft_has_no_network_dependency(self):
        with patch(
            "urllib.request.OpenerDirector.open",
            side_effect=AssertionError("Network forbidden")
        ):
            self.assertEqual(
                self.draft()["status"],"LOCAL_DRAFT"
            )

if __name__=="__main__":
    unittest.main(verbosity=2)
