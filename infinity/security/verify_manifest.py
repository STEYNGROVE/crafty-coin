import json
import hashlib
import sys
from pathlib import Path

root=Path(sys.argv[1]).resolve()

manifest=json.loads(
    (root/"security/manifest.json").read_text()
)

for name,expected in manifest.items():
    p=(root/name).resolve()

    assert p.is_relative_to(root)
    assert p.is_file()

    actual=hashlib.sha256(
        p.read_bytes()
    ).hexdigest()

    assert actual==expected,name

print(
    "PASS: Manifest integrity:",
    len(manifest),"files"
)
