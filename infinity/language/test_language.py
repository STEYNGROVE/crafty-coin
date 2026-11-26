import unittest

from engine import (
    CATALOGUE,LANGUAGES,translate,
    speech_plan,active_recall,
    request_cloud_voice,record_microphone,
    upload_audio,request_live_ai
)

class Tests(unittest.TestCase):

    def test_languages(self):
        self.assertEqual(
            set(CATALOGUE),{"en","af","st","zu"})

    def test_locale_count(self):
        self.assertEqual(len(LANGUAGES),4)

    def test_translation_count(self):
        self.assertEqual(
            sum(map(len,CATALOGUE.values())),48)

    def test_key_parity(self):
        for lang in CATALOGUE:
            self.assertEqual(
                set(CATALOGUE[lang]),
                set(CATALOGUE["en"]))

    def test_nonempty(self):
        for messages in CATALOGUE.values():
            for value in messages.values():
                self.assertTrue(value.strip())

    def test_english(self):
        self.assertIn(
            "Welcome",translate("welcome","en"))

    def test_afrikaans(self):
        self.assertIn(
            "Welkom",translate("welcome","af"))

    def test_sesotho(self):
        self.assertIn(
            "amohela",translate("welcome","st"))

    def test_zulu(self):
        self.assertIn(
            "Siyakwamukela",translate("welcome","zu"))

    def test_unknown_language(self):
        with self.assertRaises(ValueError):
            translate("welcome","xx")

    def test_unknown_key(self):
        with self.assertRaises(ValueError):
            translate("unknown","en")

    def test_locale(self):
        self.assertEqual(
            speech_plan("welcome","af")["locale"],
            "af-ZA")

    def test_crafty(self):
        self.assertEqual(
            speech_plan("welcome")["guide"],
            "Crafty")

    def test_rate(self):
        self.assertEqual(
            speech_plan("welcome",rate=0.8)["rate"],
            0.8)

    def test_invalid_rate(self):
        with self.assertRaises(ValueError):
            speech_plan("welcome",rate=2)

    def test_invalid_rate_type(self):
        with self.assertRaises(ValueError):
            speech_plan("welcome",rate=True)

    def test_user_initiated(self):
        self.assertTrue(
            speech_plan("welcome")["userInitiated"])

    def test_local_voice(self):
        self.assertTrue(
            speech_plan("welcome")["localVoiceOnly"])

    def test_microphone_disabled(self):
        self.assertFalse(
            speech_plan("welcome")["microphoneRequired"])

    def test_recording_disabled(self):
        self.assertFalse(
            speech_plan("welcome")["recordingEnabled"])

    def test_cloud_disabled(self):
        self.assertFalse(
            speech_plan("welcome")["cloudSpeechEnabled"])

    def test_live_ai_disabled(self):
        self.assertFalse(
            speech_plan("welcome")["liveAIEnabled"])

    def test_recall(self):
        self.assertEqual(
            active_recall("af")["instruction"],
            translate("reflect","af"))

    def test_no_transcript(self):
        self.assertFalse(
            active_recall()["storeTranscript"])

    def test_no_assessment(self):
        self.assertFalse(
            active_recall()["automaticAssessment"])

    def test_cloud_block(self):
        with self.assertRaises(PermissionError):
            request_cloud_voice()

    def test_recording_block(self):
        with self.assertRaises(PermissionError):
            record_microphone()

    def test_upload_block(self):
        with self.assertRaises(PermissionError):
            upload_audio()

    def test_ai_block(self):
        with self.assertRaises(PermissionError):
            request_live_ai()

if __name__=="__main__":
    unittest.main(verbosity=2)
