import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

CATALOGUE=json.loads(
    (ROOT/"catalogue.json").read_text()
)

LANGUAGES={
    "en":"en-ZA",
    "af":"af-ZA",
    "st":"st-ZA",
    "zu":"zu-ZA"
}

def validate_language(language):
    if not isinstance(language,str) or \
       language not in LANGUAGES:
        raise ValueError("Unsupported language")
    return language

def translate(key,language="en"):
    validate_language(language)

    if not isinstance(key,str) or \
       key not in CATALOGUE[language]:
        raise ValueError("Unknown message")

    return CATALOGUE[language][key]

def speech_plan(key,language="en",rate=1.0):
    validate_language(language)

    if type(rate) not in (int,float) or \
       not 0.6<=rate<=1.2:
        raise ValueError("Invalid speech rate")

    return {
        "guide":"Crafty",
        "text":translate(key,language),
        "locale":LANGUAGES[language],
        "rate":rate,
        "userInitiated":True,
        "localVoiceOnly":True,
        "microphoneRequired":False,
        "recordingEnabled":False,
        "cloudSpeechEnabled":False,
        "liveAIEnabled":False
    }

def active_recall(language="en"):
    return {
        "guide":"Crafty",
        "instruction":translate("reflect",language),
        "responseMode":"OFFLINE_VERBAL_OR_TEXT",
        "recordAudio":False,
        "storeTranscript":False,
        "automaticAssessment":False
    }

def request_cloud_voice(*args):
    raise PermissionError("Cloud voice disabled")

def record_microphone(*args):
    raise PermissionError("Recording disabled")

def upload_audio(*args):
    raise PermissionError("Audio upload disabled")

def request_live_ai(*args):
    raise PermissionError("Live AI disabled")
