import sys
import tempfile
import unittest
import json
from pathlib import Path

import engine as recovery

sys.path.insert(
    0,str(Path(__file__).resolve().parent.parent/"backend")
)

import importlib.util

spec=importlib.util.spec_from_file_location(
    "learning_backend",
    Path(__file__).resolve().parent.parent/
    "backend/engine.py"
)

backend=importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)

class Tests(unittest.TestCase):

    def setUp(self):

        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)

        self.source=self.root/"source"
        self.snapshot=self.root/"snapshot"

        app=backend.Learning(self.source)

        app.complete(
            "DISCOVER","ACA-01-DISCOVER"
        )

        app.complete(
            "DISCOVER","SQUAD-01-DISCOVER",1
        )

        app.complete(
            "DISCOVER","LIFE-CITY-DISCOVER"
        )

        app.decide("DISCOVER","GARDEN")
        app.close()

    def tearDown(self):
        self.tmp.cleanup()

    def create(self):
        return recovery.backup(
            self.source,self.snapshot
        )

    def test_01_backup(self):
        r=self.create()
        self.assertEqual(len(r["databases"]),3)

    def test_02_integrity(self):
        self.create()
        self.assertTrue(
            recovery.verify_snapshot(self.snapshot)
        )

    def test_03_restore(self):

        self.create()

        target=self.root/"restored"

        recovery.restore_trial(
            self.snapshot,target
        )

        app=backend.Learning(target)

        try:
            self.assertEqual(
                app.progress("DISCOVER")["count"],3
            )
        finally:
            app.close()

    def test_04_resources(self):

        self.create()

        target=self.root/"restored"

        recovery.restore_trial(
            self.snapshot,target
        )

        app=backend.Learning(target)

        try:
            self.assertEqual(
                app.progress("DISCOVER")[
                    "virtualLife"
                ]["learning"],55
            )
        finally:
            app.close()

    def test_05_existing_destination(self):
        self.create()
        with self.assertRaises(FileExistsError):
            self.create()

    def test_06_missing_database(self):

        (self.source/"life.db").unlink()

        with self.assertRaises(FileNotFoundError):
            self.create()

    def test_07_corruption(self):

        self.create()

        with (self.snapshot/"life.db").open("ab") as f:
            f.write(b"corruption")

        with self.assertRaises(ValueError):
            recovery.verify_snapshot(self.snapshot)

    def test_08_missing_manifest(self):

        self.create()

        (self.snapshot/"manifest.json").unlink()

        with self.assertRaises(FileNotFoundError):
            recovery.verify_snapshot(self.snapshot)

    def test_09_incomplete_manifest(self):

        self.create()

        p=self.snapshot/"manifest.json"
        data=json.loads(p.read_text())

        del data["databases"]["life.db"]

        p.write_text(json.dumps(data))

        with self.assertRaises(ValueError):
            recovery.verify_snapshot(self.snapshot)

    def test_10_no_live_overwrite(self):

        with self.assertRaises(PermissionError):
            recovery.overwrite_live()

    def test_11_source_preserved(self):

        before={
            name:recovery.digest(self.source/name)
            for name in recovery.NAMES
        }

        self.create()

        after={
            name:recovery.digest(self.source/name)
            for name in recovery.NAMES
        }

        self.assertEqual(before,after)

    def test_12_permissions(self):

        self.create()

        for name in recovery.NAMES:
            self.assertEqual(
                (self.snapshot/name).stat().st_mode
                &0o777,0o600
            )

if __name__=="__main__":
    unittest.main(verbosity=2)
