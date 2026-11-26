import unittest
from router import (
    route,build_prompt,request_live,
    POLICY,VISION
)

class Tests(unittest.TestCase):

    def test_discover(self):
        self.assertEqual(
            route(5,"TUTOR","en")["level"],
            "DISCOVER"
        )

    def test_explorer(self):
        self.assertEqual(
            route(10,"TECH","en")["level"],
            "EXPLORER"
        )

    def test_future(self):
        self.assertEqual(
            route(16,"CREATOR","en")["level"],
            "FUTURE"
        )

    def test_adult(self):
        self.assertEqual(
            route(25,"PROFESSIONAL","en")["level"],
            "ADULT"
        )

    def test_minor_professional_block(self):
        with self.assertRaises(PermissionError):
            route(17,"PROFESSIONAL","en")

    def test_invalid_age(self):
        with self.assertRaises(ValueError):
            route(3,"TUTOR","en")

    def test_invalid_role(self):
        with self.assertRaises(ValueError):
            route(10,"UNKNOWN","en")

    def test_invalid_language(self):
        with self.assertRaises(ValueError):
            route(10,"TUTOR","unknown")

    def test_all_languages(self):
        for language in POLICY["languages"]:
            route(10,"TUTOR",language)

    def test_all_academies(self):
        for academy in VISION["academies"]:
            route(10,"TUTOR","en",academy)

    def test_invalid_academy(self):
        with self.assertRaises(ValueError):
            route(10,"TUTOR","en","UNKNOWN")

    def test_character(self):
        self.assertEqual(
            route(10,"TUTOR","en")["character"],
            "Crafty"
        )

    def test_child_domain(self):
        self.assertEqual(
            route(10,"TUTOR","en")["domain"],
            "EDUCATION"
        )

    def test_adult_domain(self):
        self.assertEqual(
            route(25,"TECH","en")["domain"],
            "ADULT"
        )

    def test_empty_question(self):
        with self.assertRaises(ValueError):
            build_prompt(10,"TUTOR","en","")

    def test_input_limit(self):
        with self.assertRaises(ValueError):
            build_prompt(10,"TUTOR","en","x"*2001)

    def test_child_crypto_policy(self):
        p=build_prompt(
            10,"TUTOR","en","Teach mathematics"
        )

        self.assertIn(
            "No cryptocurrency promotion",
            p[0]["content"]
        )

    def test_message_separation(self):
        p=build_prompt(
            10,"TUTOR","en","Explain gravity"
        )

        self.assertEqual(p[0]["role"],"system")
        self.assertEqual(p[1]["role"],"user")

    def test_live_disabled(self):
        with self.assertRaises(PermissionError):
            request_live()

    def test_financial_disabled(self):
        self.assertFalse(
            route(25,"PROFESSIONAL","en")
            ["financialActions"]
        )

    def test_policy_locks(self):
        for key in [
            "liveRequestsEnabled",
            "childLiveAIEnabled",
            "automaticFinancialActions",
            "automaticPublishing",
            "persistentConversationStorage"
        ]:
            self.assertIs(POLICY[key],False)

if __name__=="__main__":
    unittest.main(verbosity=2)
