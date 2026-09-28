import sqlite3
import unittest
from firebird_continuity import SCHEMA, enqueue, pulse, FEATURES

class QueueTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:");self.db.executescript(SCHEMA)
    def test_25_features(self): self.assertEqual(len(set(FEATURES)),25)
    def test_source_required(self):
        with self.assertRaises(ValueError):enqueue(self.db,"x","N95","draft","")
    def test_no_live_scope(self):
        with self.assertRaises(ValueError):enqueue(self.db,"x","N95","send","ref","external_write")
    def test_priority_and_pause(self):
        enqueue(self.db,"later","N95","later","ref")
        enqueue(self.db,"early","N95","early","ref",due="2026-10-01T00:00:00+00:00")
        self.assertEqual(pulse(self.db)["next"]["id"],"early")
        with self.db:self.db.execute("INSERT INTO settings VALUES('paused','1')")
        self.assertEqual(pulse(self.db)["state"],"PAUSED")
    def test_expired_claim_held(self):
        enqueue(self.db,"x","N95","draft","ref")
        with self.db:self.db.execute("UPDATE tasks SET state='claimed',lease_until='2020-01-01T00:00:00+00:00' WHERE id='x'")
        self.assertEqual(pulse(self.db)["held"],1)
        self.assertEqual(pulse(self.db)["next"],None)

if __name__=="__main__":unittest.main()
