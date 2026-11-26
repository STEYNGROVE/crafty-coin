import json
import hashlib
import subprocess
import tempfile
from pathlib import Path

root=Path(__file__).resolve().parent

catalogue=json.loads(
    (root/"catalogue.json").read_text()
)

voices=subprocess.check_output(
    ["espeak-ng","--voices"],
    text=True
)

available={
    line.split()[1]
    for line in voices.splitlines()[1:]
    if len(line.split())>=2
}

manifest={}
missing=[]

for lang,messages in catalogue.items():

    candidates=sorted(
        v for v in available
        if v==lang or v.startswith(lang+"-")
    )

    if not candidates:
        missing.append(lang)
        print("UNAVAILABLE:",lang)
        continue

    voice=lang if lang in candidates else candidates[0]

    print("SELECTED VOICE:",lang,voice)

    directory=root/"audio"/lang
    directory.mkdir(parents=True,exist_ok=True)

    manifest[lang]={}

    for key,message in messages.items():

        output=directory/f"{key}.mp3"

        with tempfile.TemporaryDirectory() as tmp:

            wav=Path(tmp)/"crafty.wav"

            subprocess.run([
                "espeak-ng",
                "-v",voice,
                "-s","145",
                "-p","58",
                "-w",str(wav),
                message
            ],check=True)

            subprocess.run([
                "ffmpeg",
                "-hide_banner",
                "-loglevel","error",
                "-y",
                "-i",str(wav),
                "-af","loudnorm=I=-18:TP=-2:LRA=7",
                "-codec:a","libmp3lame",
                "-b:a","64k",
                str(output)
            ],check=True)

        duration=float(
            subprocess.check_output([
                "ffprobe",
                "-v","error",
                "-show_entries","format=duration",
                "-of","default=noprint_wrappers=1:nokey=1",
                str(output)
            ],text=True).strip()
        )

        assert duration>0
        assert output.stat().st_size>100

        manifest[lang][key]={
            "file":str(output.relative_to(root)),
            "durationSeconds":round(duration,2),
            "sha256":hashlib.sha256(
                output.read_bytes()
            ).hexdigest()
        }

        print("PASS:",lang,key,round(duration,2))

report={
    "mode":"OFFLINE_SYNTHETIC_SPEECH",
    "guide":"Crafty",
    "engine":"eSpeak NG",
    "status":"PASS" if not missing else "PARTIAL",
    "languages":list(manifest),
    "unavailableLanguages":missing,
    "audioFiles":sum(map(len,manifest.values())),
    "nativeSpeakerReview":"PENDING",
    "browserPlaybackVerified":False,
    "microphoneRecording":False,
    "cloudSpeech":False,
    "actualExpenditureZAR":0,
    "audio":manifest
}

(root/"audio-manifest.json").write_text(
    json.dumps(report,indent=2)
)

(root.parent/"reports/voice.json").write_text(
    json.dumps(report,indent=2)
)

print(json.dumps(report,indent=2))

assert report["audioFiles"]>0
