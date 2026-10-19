"""Bounded, read-only folder extraction; no model, network, subprocess or watcher."""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import unicodedata

VERSION = "0.1.0"
IS_WINDOWS = os.name == "nt"
MAX_FILES = 50
MAX_BYTES = 1024 * 1024
MAX_OBSERVATIONS = 10000
TASK = re.compile(r"^ {0,3}[-*+]\s+\[([ xX])\](?:[ \t]+(.*)|$)")
FIELD = re.compile(r"\[(id|due|owner):([^\]\r\n]*)\]")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
OUTPUT_NAMES = {"brief.md", "observations.json", "manifest.json"}


class WorkflowError(ValueError):
    pass


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def iso_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise WorkflowError("as-of and due dates require YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise WorkflowError("invalid calendar date") from exc


def fingerprint(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns,
            getattr(info, "st_file_attributes", 0))


def reject_link(info):
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise WorkflowError("symlinks and reparse points are not accepted")


def windows_drive_type(anchor):
    import ctypes
    query = ctypes.WinDLL("kernel32", use_last_error=True).GetDriveTypeW
    query.argtypes = [ctypes.c_wchar_p]
    query.restype = ctypes.c_uint
    return query(anchor)


def checked_path(value, *, allow_missing=False):
    # Do not resolve links: inspect each lexical ancestor before following paths.
    raw = os.fspath(value)
    if raw.startswith(("\\\\", "//")):
        raise WorkflowError("UNC and device-prefixed paths are not accepted")
    path = Path(os.path.abspath(os.path.expanduser(raw)))
    if IS_WINDOWS and windows_drive_type(path.anchor) not in (2, 3, 5, 6):
        raise WorkflowError("only known local Windows drives are accepted")
    for current in (*reversed(path.parents), path):
        try:
            info = current.lstat()
        except FileNotFoundError:
            if allow_missing:
                continue
            raise WorkflowError("selected path does not exist")
        reject_link(info)
        if current != path and not stat.S_ISDIR(info.st_mode):
            raise WorkflowError("path ancestor is not a directory")
    return path


def output_path(value, source):
    path = checked_path(value, allow_missing=True)
    if path == source or source in path.parents or path in source.parents:
        raise WorkflowError("input and output folders must not overlap")
    for parent in (path, *path.parents):
        # A git worktree's .git can be a file rather than a directory.
        if os.path.lexists(parent / ".git"):
            raise WorkflowError("output must be outside every git checkout")
    if path.exists() and not path.is_dir():
        raise WorkflowError("output parent is not a directory")
    return path


def inventory(source):
    source = checked_path(source)
    root_info = source.lstat()
    if not stat.S_ISDIR(root_info.st_mode):
        raise WorkflowError("input must be a directory")
    entries = []
    with os.scandir(source) as directory:
        for entry in directory:
            entries.append(source / entry.name)
            if len(entries) > MAX_FILES:
                raise WorkflowError("input requires 1 to 50 files")
    entries.sort(key=lambda entry: entry.name)
    if not entries:
        raise WorkflowError("input requires 1 to 50 files")
    files, total = [], 0
    for entry in entries:
        info = entry.lstat()
        reject_link(info)
        if not stat.S_ISREG(info.st_mode):
            raise WorkflowError("nested directories and special files are not accepted")
        if entry.suffix.lower() not in (".txt", ".md"):
            raise WorkflowError("only .txt and .md input files are accepted")
        total += info.st_size
        if total > MAX_BYTES:
            raise WorkflowError("combined input exceeds 1 MiB")
        files.append((entry, fingerprint(info)))
    return fingerprint(root_info), files


def read_checked(path, expected, limit):
    checked_path(path)
    initial = path.lstat()
    reject_link(initial)
    if not stat.S_ISREG(initial.st_mode) or fingerprint(initial) != expected:
        raise WorkflowError("source changed before read")
    flags = (os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
             | getattr(os, "O_NONBLOCK", 0))
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        reject_link(before)
        if not stat.S_ISREG(before.st_mode) or fingerprint(before) != expected:
            raise WorkflowError("source changed before read")
        chunks, size = [], 0
        while True:
            chunk = os.read(descriptor, min(65536, limit + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > limit:
                raise WorkflowError("input grew beyond its bound")
        if fingerprint(os.fstat(descriptor)) != expected or fingerprint(path.lstat()) != expected:
            raise WorkflowError("source changed during read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def collect(source):
    root_fingerprint, entries = inventory(source)
    contents, used = [], 0
    for index, (path, info) in enumerate(entries, 1):
        raw = read_checked(path, info, MAX_BYTES - used)
        used += len(raw)
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise WorkflowError("input is not valid UTF-8") from exc
        contents.append({"source_id": f"S{index:03d}", "filename": path.name,
                         "sha256": digest(raw), "bytes": len(raw), "text": text})
    return root_fingerprint, entries, contents


def verify_sources(source, root_fingerprint, entries, contents):
    current_root, current_entries = inventory(source)
    if current_root != root_fingerprint or current_entries != entries:
        raise WorkflowError("input folder changed during extraction")
    for (path, info), content in zip(entries, contents):
        if digest(read_checked(path, info, MAX_BYTES)) != content["sha256"]:
            raise WorkflowError("source content changed during extraction")


def safe_display(text):
    # Exact quotes remain in JSON; render controls/bidi visibly in the brief.
    return "".join(f"\\u{ord(char):04x}" if unicodedata.category(char) in ("Cc", "Cf")
                   else char for char in text)


def literal(text):
    text = safe_display(text)
    runs = [len(match.group()) for match in re.finditer(r"`+", text)]
    fence = "`" * max(3, max(runs, default=0) + 1)
    return f"{fence}text\n{text}\n{fence}\n"


def parse_fields(body):
    values, warnings = {}, []
    for key, value in FIELD.findall(body):
        values.setdefault(key, []).append(value)
    parsed = {"id": None, "due": None, "owner": None}
    for key, items in values.items():
        if len(items) != 1:
            warnings.append("ambiguous_" + key + "_field")
            continue
        value = items[0]
        valid = bool(value)
        if key == "id":
            valid = bool(re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value))
        elif key == "due":
            try:
                iso_date(value)
            except WorkflowError:
                valid = False
        else:
            valid = bool(value.strip()) and len(value) <= 80
        if valid:
            parsed[key] = value
        else:
            warnings.append("invalid_" + key + "_field")
    return parsed, warnings


def extract(contents, as_of, context_lines):
    observations, excerpts, warnings = [], [], []
    for source in contents:
        fence = None
        context_count = 0
        for number, raw_line in enumerate(source["text"].split("\n"), 1):
            line = raw_line[:-1] if raw_line.endswith("\r") else raw_line
            marker = FENCE.match(line)
            if fence:
                if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1] and not marker[2].strip():
                    fence = None
                match = None
            elif marker:
                fence = (marker[1][0], len(marker[1]))
                match = None
            else:
                match = TASK.match(line)
            reference = {"source_id": source["source_id"], "filename": source["filename"],
                         "line": number, "sha256": source["sha256"]}
            if match:
                if len(observations) >= MAX_OBSERVATIONS:
                    raise WorkflowError("input exceeds 10000 checkbox observations")
                body = match[2] or ""
                fields, field_warnings = parse_fields(body)
                observation = {"observation_id": f"O{len(observations) + 1:04d}",
                               "state": "open" if match[1] == " " else "completed",
                               "text": body, "task_text": re.sub(r"[ \t]+", " ", FIELD.sub("", body)).strip(),
                               "quote": line, **fields, "source": reference,
                               "warnings": field_warnings}
                observations.append(observation)
                for warning in field_warnings:
                    warnings.append({"code": warning, "observation_id": observation["observation_id"]})
            elif line.strip() and context_count < context_lines:
                excerpts.append({"quote": line[:240], "truncated": len(line) > 240,
                                 "source": reference})
                context_count += 1
    grouped = {}
    for observation in observations:
        key = ("id:" + observation["id"] if observation["id"] else
               "source:" + digest(encoded(observation["source"])))
        grouped.setdefault(key, []).append(observation)
    tasks = []
    for key, records in sorted(grouped.items()):
        states = sorted({record["state"] for record in records})
        dues = sorted({record["due"] for record in records if record["due"]})
        owners = sorted({record["owner"] for record in records if record["owner"]})
        texts = sorted({record["task_text"] for record in records})
        conflicts = [name for name, values in (("state", states), ("due", dues), ("owner", owners), ("text", texts))
                     if len(values) > 1]
        state = states[0] if len(states) == 1 else "conflict"
        due = dues[0] if len(dues) == 1 else None
        due_status = ("conflict" if conflicts else "completed" if state == "completed" else
                      "unspecified" if due is None else "overdue" if due < as_of else
                      "due_today" if due == as_of else "upcoming")
        signatures = {encoded({k: r[k] for k in ("state", "text", "due", "owner")}) for r in records}
        tasks.append({"task_key": key, "id": records[0]["id"], "state": state,
                      "due_values": dues, "owner_values": owners, "conflicts": conflicts,
                      "due_status": due_status, "repeated_occurrences": len(records) - len(signatures),
                      "observation_ids": [r["observation_id"] for r in records]})
        if conflicts:
            warnings.append({"code": "conflicting_explicit_id", "task_key": key, "fields": conflicts})
    if not observations:
        warnings.append({"code": "no_explicit_checkbox_tasks"})
    return {"observations": observations, "tasks": tasks, "excerpts": excerpts, "warnings": warnings}


def render(document):
    lines = ["# Local operational brief\n", f"As of: {document['as_of']}\n",
             "Deterministic extraction of explicit checkbox lines. No AI model was used.\n",
             "Source statements remain unverified. This is a snapshot, not live task state.\n",
             "Non-task notes are not summarized or fully understood; excerpts are bounded context.\n",
             f"Content ID: {document['content_id']}\n"]
    records = {record["observation_id"]: record for record in document["observations"]}
    for heading, predicate in (
            ("Conflicts requiring review", lambda task: bool(task["conflicts"])),
            ("Open tasks", lambda task: not task["conflicts"] and task["state"] == "open"),
            ("Completed context", lambda task: not task["conflicts"] and task["state"] == "completed")):
        lines.append("## " + heading + "\n")
        selected = [task for task in document["tasks"] if predicate(task)]
        if not selected:
            lines.append("None explicitly extracted.\n")
        for index, task in enumerate(selected, 1):
            lines.append(f"### Item {index} · {task['due_status']}\n")
            if task["conflicts"]:
                lines.append("Conflicting fields: " + ", ".join(task["conflicts"]) + ". No resolution inferred.\n")
            if task["repeated_occurrences"]:
                lines.append(f"Repeated occurrences retained: {task['repeated_occurrences']}.\n")
            for observation_id in task["observation_ids"]:
                record = records[observation_id]
                ref = record["source"]
                lines.append(f"[{ref['source_id']}, line {ref['line']}](#source-{ref['source_id'].lower()}) · {record['state']}\n")
                lines.append(literal(record["quote"]))
    lines.append("## Bounded non-task excerpts\n")
    for excerpt in document["excerpts"]:
        ref = excerpt["source"]
        suffix = " · excerpt truncated at 240 characters" if excerpt["truncated"] else ""
        lines.append(f"[{ref['source_id']}, line {ref['line']}](#source-{ref['source_id'].lower()}){suffix}\n")
        lines.append(literal(excerpt["quote"]))
    if not document["excerpts"]:
        lines.append("No excerpts selected.\n")
    lines.append("## Warnings\n")
    for warning in document["warnings"]:
        lines.append(literal(json.dumps(warning, ensure_ascii=True, sort_keys=True)))
    if not document["warnings"]:
        lines.append("No metadata or explicit-ID conflicts detected within the extraction rules.\n")
    lines.append("## Source inventory\n")
    for source in document["sources"]:
        lines.append(f"### Source {source['source_id']}\n")
        lines.append(literal(source["filename"]))
        lines.append(f"SHA256: {source['sha256']} · Bytes: {source['bytes']}\n")
    return ("\n".join(lines) + "\n").encode("utf-8")


def verify_existing(target, artifacts):
    checked_path(target)
    names = set()
    if not target.is_dir():
        raise WorkflowError("existing output does not match the completed artifact set")
    with os.scandir(target) as directory:
        for entry in directory:
            names.add(entry.name)
            if len(names) > len(OUTPUT_NAMES):
                raise WorkflowError("existing output has unexpected artifacts")
    if names != OUTPUT_NAMES:
        raise WorkflowError("existing output does not match the completed artifact set")
    for name, expected in artifacts.items():
        path = target / name
        info = path.lstat()
        reject_link(info)
        if not stat.S_ISREG(info.st_mode) or info.st_size != len(expected):
            raise WorkflowError("existing output was modified")
        if read_checked(path, fingerprint(info), len(expected)) != expected:
            raise WorkflowError("existing output was modified")


def run(input_path, output, as_of, *, context_lines=1):
    iso_date(as_of)
    if type(context_lines) is not int or not 0 <= context_lines <= 3:
        raise WorkflowError("context-lines must be between 0 and 3")
    source = checked_path(input_path)
    destination = output_path(output, source)
    root_info, entries, contents = collect(source)
    sources = [{k: value for k, value in item.items() if k != "text"} for item in contents]
    identity = {"workflow_version": VERSION, "implementation_sha256": digest(Path(__file__).read_bytes()),
                "as_of": as_of, "context_lines": context_lines, "sources": sources}
    content_id = digest(encoded(identity))
    document = {**identity, "content_id": content_id, "method": "deterministic_extract_only",
                "limits": {"files": MAX_FILES, "combined_bytes": MAX_BYTES,
                           "checkbox_observations": MAX_OBSERVATIONS},
                **extract(contents, as_of, context_lines)}
    artifacts = {"observations.json": encoded(document), "brief.md": render(document)}
    manifest = {**identity, "content_id": content_id, "status": "completed",
                "artifacts": {name: {"sha256": digest(raw), "bytes": len(raw)}
                              for name, raw in artifacts.items()}}
    artifacts["manifest.json"] = encoded(manifest)
    verify_sources(source, root_info, entries, contents)
    destination = output_path(destination, source)
    target = destination / content_id
    if os.path.lexists(target):
        verify_existing(target, artifacts)
        return {"content_id": content_id, "output_directory": str(target), "reused": True}
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    output_path(destination, source)
    stage = Path(tempfile.mkdtemp(prefix=".n95-pending-", dir=destination))
    try:
        for name, raw in artifacts.items():
            descriptor = os.open(stage / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
        verify_sources(source, root_info, entries, contents)
        output_path(destination, source)
        if os.path.lexists(target):
            verify_existing(target, artifacts)
            reused = True
        else:
            try:
                os.rename(stage, target)
                reused = False
            except OSError:
                if not os.path.lexists(target):
                    raise
                verify_existing(target, artifacts)
                reused = True
        return {"content_id": content_id, "output_directory": str(target), "reused": reused}
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("run")
    command.add_argument("--input", required=True, type=Path)
    command.add_argument("--output", required=True, type=Path)
    command.add_argument("--as-of", required=True)
    command.add_argument("--context-lines", type=int, default=1)
    args = parser.parse_args(argv)
    try:
        result = run(args.input, args.output, args.as_of, context_lines=args.context_lines)
        print(json.dumps({"ok": True, **result}, ensure_ascii=True))
        return 0
    except KeyboardInterrupt:
        print(json.dumps({"ok": False, "error": "interrupted; rerun with the same inputs"}))
        return 130
    except (WorkflowError, OSError, UnicodeError) as exc:
        message = str(exc) if isinstance(exc, WorkflowError) else "filesystem operation failed"
        print(json.dumps({"ok": False, "error": message}))
        return 1
