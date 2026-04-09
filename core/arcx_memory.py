#!/usr/bin/env python3
"""ArcX Memory Engine - Sovereign Hot Cache & Long-Term Storage"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

MEMORY_DIR = Path(os.getenv("ARCX_MEMORY_DIR", "/data/memory"))
HOT_CACHE_FILE = MEMORY_DIR / "hot_cache.json"
LONG_TERM_FILE = MEMORY_DIR / "long_term.json"
INDEX_FILE = MEMORY_DIR / "index.json"

class ArcXMemory:
    def __init__(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self.hot_cache = self._load(HOT_CACHE_FILE, {})
        self.long_term = self._load(LONG_TERM_FILE, [])
        self.index = self._load(INDEX_FILE, {})

    def _load(self, path, default):
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return default

    def _save(self, path, data):
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _hash(self, content):
        return hashlib.sha256(str(content).encode()).hexdigest()[:12]

    def store_hot(self, key, value, ttl_hours=24):
        entry = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "expires": (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat(),
            "hash": self._hash(value)
        }
        self.hot_cache[key] = entry
        self._save(HOT_CACHE_FILE, self.hot_cache)
        return entry

    def get_hot(self, key):
        entry = self.hot_cache.get(key)
        if not entry:
            return None
        if datetime.fromisoformat(entry["expires"]) < datetime.utcnow():
            del self.hot_cache[key]
            self._save(HOT_CACHE_FILE, self.hot_cache)
            return None
        return entry["value"]

    def store_long_term(self, category, content, tags=None):
        record = {
            "id": self._hash(content),
            "category": category,
            "content": content,
            "tags": tags or [],
            "timestamp": datetime.utcnow().isoformat()
        }
        self.long_term.append(record)
        self._save(LONG_TERM_FILE, self.long_term)
        for tag in record["tags"]:
            self.index.setdefault(tag, []).append(record["id"])
        self._save(INDEX_FILE, self.index)
        return record

    def search(self, query, limit=10):
        results = []
        q = query.lower()
        for record in self.long_term:
            score = 0
            if q in str(record.get("content", "")).lower():
                score += 2
            if q in str(record.get("tags", [])).lower():
                score += 3
            if q in record.get("category", "").lower():
                score += 1
            if score > 0:
                results.append((score, record))
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:limit]]

    def flush_expired(self):
        now = datetime.utcnow()
        expired = [k for k, v in self.hot_cache.items()
                   if datetime.fromisoformat(v["expires"]) < now]
        for k in expired:
            del self.hot_cache[k]
        self._save(HOT_CACHE_FILE, self.hot_cache)
        return len(expired)

    def stats(self):
        return {
            "hot_cache_entries": len(self.hot_cache),
            "long_term_records": len(self.long_term),
            "index_tags": len(self.index),
            "memory_dir": str(MEMORY_DIR)
        }

if __name__ == "__main__":
    mem = ArcXMemory()
    print(json.dumps(mem.stats(), indent=2))
