import unittest

from engine import Platform

class Tests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.p=Platform()
        cls.t=cls.p.bootstrap()

    @classmethod
    def tearDownClass(cls):

        cls.p.close()

    def test_01_parent_dashboard(self):

        r=self.p.dashboard(
            self.t["SIM-PARENT"],"EDUCATION"
        )

        self.assertEqual(r["guide"],"Crafty")

    def test_02_adult_dashboard(self):

        r=self.p.dashboard(
            self.t["SIM-CUSTOMER"],"ADULT"
        )

        self.assertEqual(r["actualRevenueZAR"],0)

    def test_03_child_adult_denied(self):

        with self.assertRaises(PermissionError):

            self.p.dashboard(
                self.t["SIM-LEARNER"],"ADULT"
            )

    def test_04_adult_education_denied(self):

        with self.assertRaises(PermissionError):

            self.p.dashboard(
                self.t["SIM-CUSTOMER"],"EDUCATION"
            )

    def test_05_invalid_session(self):

        with self.assertRaises(PermissionError):

            self.p.dashboard("INVALID","ADULT")

    def test_06_parent_report(self):

        self.p.learning_report(
            self.t["SIM-PARENT"],"SIM-LEARNER"
        )

    def test_07_teacher_without_consent(self):

        with self.assertRaises(PermissionError):

            self.p.learning_report(
                self.t["SIM-TEACHER"],"SIM-LEARNER"
            )

    def test_08_consent_lifecycle(self):

        self.p.parent_grant(
            self.t["SIM-PARENT"],
            "SIM-LEARNER","SIM-TEACHER"
        )

        self.p.learning_report(
            self.t["SIM-TEACHER"],"SIM-LEARNER"
        )

        self.p.parent_revoke(
            self.t["SIM-PARENT"],
            "SIM-LEARNER","SIM-TEACHER"
        )

        with self.assertRaises(PermissionError):

            self.p.learning_report(
                self.t["SIM-TEACHER"],"SIM-LEARNER"
            )

    def test_09_teacher_cannot_grant(self):

        with self.assertRaises(PermissionError):

            self.p.parent_grant(
                self.t["SIM-TEACHER"],
                "SIM-LEARNER","SIM-TEACHER"
            )

    def test_10_learning_record(self):

        self.p.learning_record(
            self.t["SIM-PARENT"],
            "SIM-LEARNER","SIM-PLATFORM-ACTIVITY"
        )

        r=self.p.learning_report(
            self.t["SIM-PARENT"],"SIM-LEARNER"
        )

        self.assertEqual(
            r["completedActivities"],1
        )

    def test_11_learner_cannot_purchase(self):

        with self.assertRaises(PermissionError):

            self.p.market_order(
                self.t["SIM-LEARNER"],
                "SIM-ORDER","BUSINESS_PRO"
            )

    def test_12_parent_cannot_purchase(self):

        with self.assertRaises(PermissionError):

            self.p.market_order(
                self.t["SIM-PARENT"],
                "SIM-ORDER","BUSINESS_PRO"
            )

    def test_13_market_lifecycle(self):

        token=self.t["SIM-CUSTOMER"]

        self.p.market_order(
            token,"SIM-MARKET-13","BUSINESS_PRO"
        )

        self.assertFalse(
            self.p.market_access(token,"BUSINESS_PRO")
        )

        self.p.market_activate(
            token,"SIM-MARKET-13"
        )

        self.assertTrue(
            self.p.market_access(token,"BUSINESS_PRO")
        )

        self.p.market_cancel(
            token,"SIM-MARKET-13"
        )

        self.assertFalse(
            self.p.market_access(token,"BUSINESS_PRO")
        )

    def test_14_wrong_customer(self):

        self.p.market_order(
            self.t["SIM-CUSTOMER"],
            "SIM-MARKET-14","BUSINESS_BASIC"
        )

        with self.assertRaises(PermissionError):

            self.p.market_activate(
                self.t["SIM-OTHER"],
                "SIM-MARKET-14"
            )

    def test_15_entitlement_isolation(self):

        self.p.market_order(
            self.t["SIM-CUSTOMER"],
            "SIM-MARKET-15","CREATOR_PRO"
        )

        self.p.market_activate(
            self.t["SIM-CUSTOMER"],
            "SIM-MARKET-15"
        )

        self.assertFalse(
            self.p.market_access(
                self.t["SIM-OTHER"],"CREATOR_PRO"
            )
        )

    def test_16_service_request(self):

        self.p.service_draft(
            self.t["SIM-CUSTOMER"],
            "SIM-SERVICE-16","PIXELPUNK",150000
        )

        self.p.service_review(
            self.t["SIM-CUSTOMER"],
            "SIM-SERVICE-16"
        )

    def test_17_service_child_denied(self):

        with self.assertRaises(PermissionError):

            self.p.service_draft(
                self.t["SIM-LEARNER"],
                "SIM-SERVICE-17","GPU_COMPUTE",100
            )

    def test_18_service_wrong_owner(self):

        self.p.service_draft(
            self.t["SIM-CUSTOMER"],
            "SIM-SERVICE-18","GHOSTMEDIA",100
        )

        with self.assertRaises(PermissionError):

            self.p.service_review(
                self.t["SIM-OTHER"],
                "SIM-SERVICE-18"
            )

    def test_19_unknown_domain(self):

        with self.assertRaises(PermissionError):

            self.p.dashboard(
                self.t["SIM-CUSTOMER"],"UNKNOWN"
            )

    def test_20_financial_activation(self):

        with self.assertRaises(PermissionError):

            self.p.financial_activation()

    def test_21_adult_cannot_read_child(self):

        with self.assertRaises(PermissionError):

            self.p.learning_report(
                self.t["SIM-CUSTOMER"],
                "SIM-LEARNER"
            )

    def test_22_learner_cannot_grant(self):

        with self.assertRaises(PermissionError):

            self.p.parent_grant(
                self.t["SIM-LEARNER"],
                "SIM-LEARNER","SIM-TEACHER"
            )

    def test_23_revoked_session(self):

        token=self.p.auth.login(
            "SIM-CUSTOMER",
            "Synthetic-Platform-Demo-2026"
        )

        self.p.auth.revoke(token)

        with self.assertRaises(PermissionError):

            self.p.market_order(
                token,"SIM-REVOKED","BUSINESS_PRO"
            )

    def test_24_event_integrity(self):

        self.assertTrue(
            self.p.auth.verify_events()
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
