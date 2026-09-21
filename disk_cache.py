"""
disk_cache.py — tiny on-disk JSON cache for slow / quota-limited work
(OCR, AI document analysis). Keyed by the SHA-256 of the file bytes plus a
version tag, so a rerun of the pipeline never pays twice for the same file,
and changing a prompt (bump the tag) invalidates old answers.

Cache folder: SDOC_CACHE_DIR (default ".sdoc_cache"). Add it to .gitignore.
Set SDOC_NO_CACHE=1 to disable.
"""
import hashlib
import json
import os
from pathlib import Path


def _enabled():
    return os.environ.get("SDOC_NO_CACHE", "").strip().lower() not in ("1", "true", "yes")


def _dir():
    return Path(os.environ.get("SDOC_CACHE_DIR", ".sdoc_cache"))


def key_for(data, tag):
    raw = data if isinstance(data, bytes) else str(data).encode("utf-8", "replace")
    return f"{tag}-{hashlib.sha256(raw).hexdigest()[:32]}"


def get(key):
    if not _enabled():
        return None
    path = _dir() / f"{key}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def put(key, value):
    if not _enabled():
        return
    try:
        folder = _dir()
        folder.mkdir(parents=True, exist_ok=True)
        tmp = folder / f"{key}.json.tmp"
        tmp.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        tmp.replace(folder / f"{key}.json")
    except Exception:
        pass  # a cache must never break the pipeline