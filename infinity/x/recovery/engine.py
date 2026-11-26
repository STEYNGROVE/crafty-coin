import sqlite3
import hashlib
import json
import tempfile
import os
from pathlib import Path

NAMES=(
    "education.db",
    "squad.db",
    "life.db"
)

TABLES={
    "education.db":{
        "learners","progress"
    },
    "squad.db":{
        "learners","achievements"
    },
    "life.db":{
        "players","decisions","missions"
    }
}

def digest(path):

    h=hashlib.sha256()

    with Path(path).open("rb") as f:
        for block in iter(
            lambda:f.read(65536),b""
        ):
            h.update(block)

    return h.hexdigest()

def verify_database(path,name):

    path=Path(path)

    if name not in NAMES:
        raise ValueError("Unknown database")

    if not path.is_file():
        raise FileNotFoundError(path)

    db=sqlite3.connect(
        path.resolve().as_uri()+"?mode=ro",
        uri=True
    )

    try:
        integrity=db.execute(
            "PRAGMA integrity_check"
        ).fetchall()

        if integrity!=[("ok",)]:
            raise ValueError("Database integrity failed")

        if db.execute(
            "PRAGMA foreign_key_check"
        ).fetchall():
            raise ValueError("Foreign key failure")

        tables={
            row[0]
            for row in db.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table'"
            )
        }

        if not TABLES[name].issubset(tables):
            raise ValueError("Missing database tables")

        return {
            "integrity":"PASS",
            "tables":sorted(TABLES[name]),
            "sha256":digest(path)
        }

    finally:
        db.close()

def backup(source,destination):

    source=Path(source)
    destination=Path(destination)

    if destination.exists():
        raise FileExistsError(destination)

    destination.parent.mkdir(
        parents=True,exist_ok=True
    )

    destination.parent.chmod(0o700)

    for name in NAMES:
        verify_database(source/name,name)

    with tempfile.TemporaryDirectory(
        dir=destination.parent
    ) as temporary:

        stage=Path(temporary)/"snapshot"
        stage.mkdir(mode=0o700)

        report={
            "mode":"LOCAL_SYNTHETIC",
            "databases":{},
            "requiresStoppedApplication":True
        }

        for name in NAMES:

            src=sqlite3.connect(
                (source/name).resolve().as_uri()
                +"?mode=ro",
                uri=True
            )

            dst=sqlite3.connect(stage/name)

            try:
                src.backup(dst)
            finally:
                dst.close()
                src.close()

            (stage/name).chmod(0o600)

            report["databases"][name]=verify_database(
                stage/name,name
            )

        manifest=stage/"manifest.json"

        manifest.write_text(
            json.dumps(report,indent=2)
        )

        manifest.chmod(0o600)

        verify_snapshot(stage)

        os.rename(stage,destination)

    return report

def verify_snapshot(directory):

    directory=Path(directory)

    manifest=json.loads(
        (directory/"manifest.json").read_text()
    )

    if set(manifest["databases"])!=set(NAMES):
        raise ValueError("Incomplete snapshot")

    for name in NAMES:

        actual=verify_database(
            directory/name,name
        )

        expected=manifest["databases"][name]

        if actual["sha256"]!=expected["sha256"]:
            raise ValueError("Checksum mismatch")

    return True

def restore_trial(snapshot,destination):

    verify_snapshot(snapshot)

    return backup(snapshot,destination)

def overwrite_live(*args,**kwargs):
    raise PermissionError(
        "Automatic live restoration prohibited"
    )
