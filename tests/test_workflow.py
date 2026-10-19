"""Real file I/O and adversarial regression tests for the local work brief."""
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from n95_workflow import workflow


class WorkBriefTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="n95-workflow-")
        self.root = Path(self.temporary.name)
        self.source = self.root / "notes"
        self.source.mkdir()
        self.output = self.root / "briefs"
        self.as_of = "2026-09-06"

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, name="ops.md", text="- [ ] Review draft [id:JOB1] [due:2026-09-06] [owner:Ben]\n"):
        path = self.source / name
        path.write_text(text, encoding="utf-8", newline="")
        return path

    def run_brief(self, **kwargs):
        return workflow.run(self.source, self.output, self.as_of, **kwargs)

    def artifact(self, result, name):
        return Path(result["output_directory"]) / name

    def assert_no_completed_artifact(self):
        if self.output.exists():
            self.assertEqual(list(self.output.iterdir()), [])

    def test_actual_run_links_exact_sources_preserves_originals_and_marks_due(self):
        first = self.write(text="Meeting notes\n- [ ] Review quote [id:JOB1] [due:2026-09-05] [owner:Ben]\n- [x] Call done [id:JOB2]\n")
        second = self.write("work.txt", "- [ ] Today [due:2026-09-06]\n- [ ] Later [due:2026-09-08]\n")
        originals = {path.name: path.read_bytes() for path in (first, second)}
        result = self.run_brief()
        document = json.loads(self.artifact(result, "observations.json").read_bytes())
        manifest = json.loads(self.artifact(result, "manifest.json").read_bytes())
        self.assertFalse(result["reused"])
        self.assertEqual(document["method"], "deterministic_extract_only")
        self.assertEqual(document["as_of"], self.as_of)
        self.assertEqual(len(document["observations"]), 4)
        record = document["observations"][0]
        self.assertEqual(record["quote"], originals["ops.md"].decode().splitlines()[1])
        self.assertEqual(record["source"]["filename"], "ops.md")
        self.assertEqual(record["source"]["line"], 2)
        self.assertEqual(record["source"]["sha256"], hashlib.sha256(originals["ops.md"]).hexdigest())
        self.assertEqual({task["due_status"] for task in document["tasks"]},
                         {"overdue", "completed", "due_today", "upcoming"})
        for path in (first, second):
            self.assertEqual(path.read_bytes(), originals[path.name])
        for name, metadata in manifest["artifacts"].items():
            raw = self.artifact(result, name).read_bytes()
            self.assertEqual(metadata["sha256"], hashlib.sha256(raw).hexdigest())
        brief = self.artifact(result, "brief.md").read_text()
        self.assertIn("[S001, line 2](#source-s001)", brief)
        self.assertIn("No AI model was used", brief)

    def test_conflicting_state_due_owner_is_surfaced_without_resolution(self):
        self.write(text="- [ ] Ship [id:JOB1] [due:2026-09-05] [owner:A]\n")
        self.write("second.md", "- [x] Ship [id:JOB1] [due:2026-09-08] [owner:B]\n")
        document = json.loads(self.artifact(self.run_brief(), "observations.json").read_bytes())
        self.assertEqual(len(document["tasks"]), 1)
        task = document["tasks"][0]
        self.assertEqual(task["state"], "conflict")
        self.assertEqual(task["due_values"], ["2026-09-05", "2026-09-08"])
        self.assertEqual(task["conflicts"], ["state", "due", "owner"])
        self.assertEqual(task["due_status"], "conflict")
        self.assertEqual(len(task["observation_ids"]), 2)

    def test_same_id_text_conflict_is_not_resolved_and_no_id_occurrences_stay_separate(self):
        self.write(text="- [ ] Send quote [id:ONE]\n- [ ] Delete quote [id:ONE]\n- [ ] Review\n- [ ] Review\n")
        self.write("other.md", "- [ ] Review\n")
        document = json.loads(self.artifact(self.run_brief(), "observations.json").read_bytes())
        self.assertEqual(len(document["tasks"]), 4)
        self.assertEqual([task["conflicts"] for task in document["tasks"] if task["id"] == "ONE"], [["text"]])
        self.assertEqual(len([task for task in document["tasks"] if task["id"] is None]), 3)

    def test_repeat_is_deterministic_and_changed_source_or_asof_creates_new_output(self):
        path = self.write(text="- [ ] Repeat [id:ONE]\n- [ ] Repeat [id:ONE]\n")
        first = self.run_brief()
        first_bytes = {name: self.artifact(first, name).read_bytes() for name in workflow.OUTPUT_NAMES}
        second = self.run_brief()
        self.assertTrue(second["reused"])
        self.assertEqual(first["content_id"], second["content_id"])
        self.assertEqual(json.loads(first_bytes["observations.json"])["tasks"][0]["repeated_occurrences"], 1)
        for name, raw in first_bytes.items():
            self.assertEqual(self.artifact(second, name).read_bytes(), raw)
        path.write_text("- [x] Repeat [id:ONE]\n", encoding="utf-8")
        changed = self.run_brief()
        self.assertNotEqual(changed["content_id"], first["content_id"])
        later = workflow.run(self.source, self.output, "2026-09-07")
        self.assertNotEqual(later["content_id"], changed["content_id"])
        self.assertTrue(self.artifact(first, "manifest.json").exists())

    def test_existing_modified_output_is_rejected_without_replacement(self):
        self.write()
        result = self.run_brief()
        brief = self.artifact(result, "brief.md")
        brief.write_text("corrupted fixture", encoding="utf-8")
        with self.assertRaises(workflow.WorkflowError):
            self.run_brief()
        self.assertEqual(brief.read_text(), "corrupted fixture")
        self.assertEqual(len(list(self.output.iterdir())), 1)

    def test_bad_metadata_remains_literal_and_warns_instead_of_inventing_date(self):
        self.write(text="- [ ] Review [id:A] [id:B] [due:tomorrow] [owner:]\n")
        document = json.loads(self.artifact(self.run_brief(), "observations.json").read_bytes())
        record = document["observations"][0]
        self.assertIsNone(record["id"])
        self.assertIsNone(record["due"])
        self.assertEqual(set(record["warnings"]), {"ambiguous_id_field", "invalid_due_field", "invalid_owner_field"})

    def test_fenced_and_indented_examples_are_not_open_tasks(self):
        self.write(text="```md\n- [ ] Fake one\n```\n    - [ ] Fake two\n- [ ] Real\n~~~\n- [ ] Fake three\n~~~\n")
        document = json.loads(self.artifact(self.run_brief(), "observations.json").read_bytes())
        self.assertEqual([record["text"] for record in document["observations"]], ["Real"])

    def test_untrusted_markdown_html_and_backticks_only_appear_in_literal_fences(self):
        quote = '- [ ] [pay](javascript:alert(1)) ![pixel](https://invalid.test/pixel) <img src=x> ``` ` ~~~'
        self.write(text=quote + "\n")
        result = self.run_brief()
        brief = self.artifact(result, "brief.md").read_text()
        self.assertIn("````text\n" + quote + "\n````", brief)
        document = json.loads(self.artifact(result, "observations.json").read_bytes())
        self.assertEqual(document["observations"][0]["quote"], quote)

    def test_context_is_bounded_and_not_presented_as_understood(self):
        self.write(text=("A" * 500) + "\nSecond non-task line\nThird line\n")
        document = json.loads(self.artifact(self.run_brief(context_lines=1), "observations.json").read_bytes())
        self.assertEqual(len(document["excerpts"]), 1)
        self.assertEqual(len(document["excerpts"][0]["quote"]), 240)
        self.assertTrue(document["excerpts"][0]["truncated"])
        self.assertEqual(document["warnings"], [{"code": "no_explicit_checkbox_tasks"}])

    def test_unsupported_nested_and_nonutf8_inputs_fail_without_output(self):
        for variant in ("unsupported", "nested", "invalid_utf8"):
            with self.subTest(variant=variant):
                if variant == "unsupported":
                    path = self.source / "data.pdf"
                    path.write_bytes(b"test")
                elif variant == "nested":
                    path = self.source / "nested"
                    path.mkdir()
                else:
                    path = self.source / "broken.md"
                    path.write_bytes(b"\xff\xfe")
                with self.assertRaises(workflow.WorkflowError):
                    self.run_brief()
                self.assert_no_completed_artifact()
                path.rmdir() if path.is_dir() else path.unlink()

    def test_empty_too_many_and_combined_byte_limits_are_enforced(self):
        with self.assertRaises(workflow.WorkflowError):
            self.run_brief()
        for number in range(51):
            self.write(f"{number:02d}.md", "")
        with self.assertRaises(workflow.WorkflowError):
            self.run_brief()
        for path in self.source.iterdir():
            path.unlink()
        self.write("one.md", "A" * (workflow.MAX_BYTES // 2))
        self.write("two.md", "B" * (workflow.MAX_BYTES // 2 + 1))
        with self.assertRaises(workflow.WorkflowError):
            self.run_brief()
        self.assert_no_completed_artifact()

    def test_checkbox_amplification_limit_rejects_whole_batch(self):
        self.write(text="- [ ]\n" * (workflow.MAX_OBSERVATIONS + 1))
        with self.assertRaises(workflow.WorkflowError):
            self.run_brief()
        self.assert_no_completed_artifact()

    def test_output_inside_input_or_git_worktree_is_rejected(self):
        self.write()
        with self.assertRaises(workflow.WorkflowError):
            workflow.run(self.source, self.source / "out", self.as_of)
        with self.assertRaises(workflow.WorkflowError):
            workflow.run(self.source, self.root, self.as_of)
        checkout = self.root / "checkout"
        checkout.mkdir()
        (checkout / ".git").write_text("gitdir: elsewhere", encoding="utf-8")
        with self.assertRaises(workflow.WorkflowError):
            workflow.run(self.source, checkout / "out", self.as_of)
        self.assertFalse((self.source / "out").exists())
        self.assertFalse((checkout / "out").exists())

    def test_unc_device_prefix_and_windows_remote_drive_types_fail_closed(self):
        for text in ("//server/share/notes", "\\\\server\\share\\notes", "\\\\?\\C:\\notes"):
            with self.assertRaises(workflow.WorkflowError):
                workflow.checked_path(text)
        with patch.object(workflow, "IS_WINDOWS", True):
            for drive_type in (0, 1, 4):
                with patch.object(workflow, "windows_drive_type", return_value=drive_type):
                    with self.assertRaises(workflow.WorkflowError):
                        workflow.checked_path(self.source)
            with patch.object(workflow, "windows_drive_type", return_value=3):
                self.assertEqual(workflow.checked_path(self.source), self.source)

    def test_source_and_output_symlinks_rejected_when_supported(self):
        self.write()
        alias = self.root / "alias"
        try:
            alias.symlink_to(self.source, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("creating symlinks requires unavailable OS privilege")
        with self.assertRaises(workflow.WorkflowError):
            workflow.run(alias, self.output, self.as_of)
        with self.assertRaises(workflow.WorkflowError):
            workflow.run(self.source, alias / "out", self.as_of)
        linked = self.source / "linked.md"
        linked.symlink_to(self.source / "ops.md")
        with self.assertRaises(workflow.WorkflowError):
            self.run_brief()
        self.assert_no_completed_artifact()

    @unittest.skipUnless(hasattr(os, "mkfifo"), "OS does not expose FIFO creation")
    def test_special_fifo_rejected_without_opening(self):
        os.mkfifo(self.source / "pipe.md")
        with self.assertRaises(workflow.WorkflowError):
            self.run_brief()
        self.assert_no_completed_artifact()

    @unittest.skipUnless(hasattr(os, "mkfifo"), "OS does not expose FIFO creation")
    def test_regular_source_swapped_for_fifo_is_rejected_before_open(self):
        path = self.write()
        expected = workflow.fingerprint(path.lstat())
        path.unlink()
        os.mkfifo(path)
        with patch.object(workflow.os, "open", side_effect=AssertionError("must not open FIFO")):
            with self.assertRaises(workflow.WorkflowError):
                workflow.read_checked(path, expected, workflow.MAX_BYTES)

    def test_source_modification_during_render_prevents_completed_artifact(self):
        path = self.write()
        original_render = workflow.render

        def change_source(document):
            result = original_render(document)
            path.write_text("- [x] Changed during extraction\n", encoding="utf-8")
            return result

        with patch.object(workflow, "render", side_effect=change_source):
            with self.assertRaises(workflow.WorkflowError):
                self.run_brief()
        self.assert_no_completed_artifact()

    def test_membership_change_is_detected_and_io_failure_removes_staging(self):
        self.write()
        original_render = workflow.render

        def add_source(document):
            result = original_render(document)
            self.write("added.md", "- [ ] Added later\n")
            return result

        with patch.object(workflow, "render", side_effect=add_source):
            with self.assertRaises(workflow.WorkflowError):
                self.run_brief()
        self.assert_no_completed_artifact()
        with patch.object(workflow.os, "fsync", side_effect=OSError("fixture disk failure")):
            with self.assertRaises(OSError):
                self.run_brief()
        self.assert_no_completed_artifact()
        self.assertFalse(self.run_brief()["reused"])

    def test_invalid_dates_cli_failure_and_success_exit_codes(self):
        self.write()
        for as_of in ("20260906", "2026-02-30", "today"):
            with self.assertRaises(workflow.WorkflowError):
                workflow.run(self.source, self.output, as_of)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = workflow.main(["run", "--input", str(self.source), "--output", str(self.output),
                                    "--as-of", self.as_of])
        self.assertEqual(result, 0)
        self.assertTrue(json.loads(stdout.getvalue())["ok"])
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = workflow.main(["run", "--input", str(self.source), "--output", str(self.output),
                                    "--as-of", "invalid"])
        self.assertEqual(result, 1)
        self.assertFalse(json.loads(stdout.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
