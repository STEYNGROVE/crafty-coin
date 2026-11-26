import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent

I=json.loads(
    (ROOT/"identity.json").read_text()
)

P=json.loads(
    (ROOT/"profiles.json").read_text()
)

class Tests(unittest.TestCase):

    def test_character(self):
        self.assertEqual(I["name"],"Crafty")

    def test_preserve_original(self):
        self.assertTrue(
            I["preserveOriginalCharacter"]
        )

    def test_applications(self):
        self.assertEqual(len(P),11)

    def test_unique_apps(self):
        self.assertEqual(
            len({p["application"] for p in P}),11
        )

    def test_crafty_everywhere(self):
        self.assertTrue(all(
            p["character"]=="Crafty" for p in P
        ))

    def test_education_theme(self):
        for p in P:
            if p["domain"]=="EDUCATION":
                self.assertEqual(p["theme"],"RAINBOW")

    def test_adult_theme(self):
        for p in P:
            if p["domain"]=="ADULT":
                self.assertEqual(
                    p["theme"],"PROFESSIONAL"
                )

    def test_no_crypto_promotion(self):
        self.assertTrue(all(
            p["cryptoPromotion"] is False for p in P
        ))

    def test_no_financial_actions(self):
        self.assertTrue(all(
            p["financialActions"] is False for p in P
        ))

    def test_no_fake_integrations(self):
        self.assertTrue(all(
            p["liveIntegration"] is False for p in P
        ))

    def test_safety(self):
        self.assertTrue(all(
            v is False for v in I["safety"].values()
        ))

    def test_palette(self):
        self.assertEqual(len(I["palette"]),9)

    def test_placements(self):
        self.assertEqual(len(I["placements"]),9)

    def test_artwork_pending(self):
        self.assertEqual(
            I["masterArtwork"],
            "PENDING_ORIGINAL_ASSET"
        )

    def test_slogan(self):
        self.assertEqual(
            I["slogan"],"Stay Crafty. Think Infinite."
        )

    def test_css(self):
        self.assertTrue(
            (ROOT/"components/crafty.css").is_file()
        )

    def test_accessibility(self):
        self.assertIn(
            "prefers-reduced-motion",
            (ROOT/"components/crafty.css").read_text()
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
