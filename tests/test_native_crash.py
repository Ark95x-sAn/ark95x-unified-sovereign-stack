"""Process-crash checks for synthetic receipts; not device or job execution proof."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from n95_native.bridge import Store, init_state, make_envelope


class NativeCrashTests(unittest.TestCase):
    def test_commit_survives_abrupt_exit_and_retry_is_duplicate(self):
        with tempfile.TemporaryDirectory(prefix="n95-crash-") as temp:
            state = Path(temp) / "state"
            init_state(state)
            now = time.time()
            event = make_envelope(state, "GM700", now=now, synthetic=True)
            child = subprocess.run(
                [sys.executable, "-c", """
import json, os, sys
from n95_native.bridge import Store
p = json.load(sys.stdin)
Store(p['state']).accept(p['event'], now=p['now'])
os._exit(73)
"""], input=json.dumps(dict(state=str(state), event=event, now=now)),
                text=True, capture_output=True, timeout=15,
                cwd=Path(__file__).resolve().parents[1])
            self.assertEqual(child.returncode, 73, child.stderr)
            reopened = Store(state)
            self.assertEqual(reopened.audit()["events"], 1)
            receipt = reopened.accept(event, now=now)
            self.assertTrue(receipt["duplicate"])
            self.assertEqual(reopened.audit()["events"], 1)
            self.assertEqual(reopened.route("inference", now=now)["status"], "blocked")

    def test_uncommitted_mutation_rolls_back_after_abrupt_exit(self):
        with tempfile.TemporaryDirectory(prefix="n95-crash-") as temp:
            state = Path(temp) / "state"
            init_state(state)
            now = time.time()
            event = make_envelope(state, "GM700", now=now, synthetic=True)
            receipt = Store(state).accept(event, now=now)
            child = subprocess.run(
                [sys.executable, "-c", """
import os, sqlite3, sys
db = sqlite3.connect(sys.argv[1])
db.execute('BEGIN IMMEDIATE')
db.execute('UPDATE events SET chain_hash = ?', ('interrupted-write',))
os._exit(74)
""", str(state / "evidence.sqlite3")], capture_output=True, text=True,
                timeout=15, cwd=Path(__file__).resolve().parents[1])
            self.assertEqual(child.returncode, 74, child.stderr)
            audit = Store(state).audit()
            self.assertEqual(audit["events"], 1)
            self.assertEqual(audit["head_sha256"], receipt["receipt_sha256"])


if __name__ == "__main__":
    unittest.main()
