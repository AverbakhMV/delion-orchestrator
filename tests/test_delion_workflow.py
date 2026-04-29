from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from orchestrator import cli
from orchestrator.artifacts import ProjectAnalyzer
from orchestrator.validation import BUSINESS_REQUIRED_SECTIONS, SYSTEM_REQUIRED_SECTIONS


def valid_document(required_sections: list[str]) -> str:
    return "\n\n".join([*required_sections, "Jenkins review"])


class DelionWorkflowTests(unittest.TestCase):
    def test_feature_writes_business_requirements_to_docs_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                output = io.StringIO()
                with redirect_stdout(output):
                    exit_code = cli.main(["\\deli:feature", "BR-001", "Add export"])

                self.assertEqual(exit_code, 0)
                self.assertTrue(Path("docs/business-requirements/BR-001.md").exists())
                self.assertFalse(Path("docs/delion/business-requirements/BR-001.md").exists())
                text = Path("docs/business-requirements/BR-001.md").read_text(encoding="utf-8")
                self.assertIn("id: BR-001", text)
                self.assertIn('title: "Add export"', text)
                self.assertIn("status: draft", text)
                self.assertIn("## Что и зачем", text)
                self.assertIn("## Требования", text)
                self.assertIn("## Критерии готовности", text)
                self.assertIn("## Следующий шаг", text)
                self.assertIn("AGENTS.md", text)
                self.assertIn("Target_columns", text)

    def test_project_root_arg_writes_init_output_to_project_not_extension_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as extension_dir, tempfile.TemporaryDirectory() as project_dir:
            with working_directory(extension_dir):
                output = io.StringIO()
                with redirect_stdout(output):
                    exit_code = cli.main(["--project-root", project_dir, "\\deli:init"])

                self.assertEqual(exit_code, 0)
                self.assertTrue(Path(project_dir, "docs/system-requirements.md").exists())
                self.assertFalse(Path(extension_dir, "docs/system-requirements.md").exists())

    def test_init_creates_minimal_delion_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                output = io.StringIO()
                with redirect_stdout(output):
                    exit_code = cli.main(["\\deli:init"])

                self.assertEqual(exit_code, 0)
                self.assertTrue(Path(".deli/state.json").exists())
                self.assertTrue(Path("docs/system-requirements.md").exists())
                self.assertTrue(Path("docs/business-requirements").is_dir())
                self.assertTrue(Path("docs/specs").is_dir())
                self.assertFalse(Path("backlog").exists())
                self.assertFalse(Path("tasks").exists())
                self.assertFalse(Path("docs/templates").exists())

    def test_project_analyzer_skips_target_build_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Path(root, "src").mkdir()
            Path(root, "src", "Main.scala").write_text("object Main", encoding="utf-8")
            target_file = Path(root, "target", "streams", "global", "assembly", "deep", "Generated.scala")
            target_file.parent.mkdir(parents=True)
            target_file.write_text("object Generated", encoding="utf-8")

            snapshot = ProjectAnalyzer().analyze(root)

            self.assertEqual(snapshot.files_count, 1)
            self.assertNotIn("target", " ".join(snapshot.entrypoints + snapshot.test_paths))

    def test_runtime_run_is_prompt_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                output = io.StringIO()
                with redirect_stdout(output):
                    exit_code = cli.main(["\\deli:run", "BR-001"])

                self.assertEqual(exit_code, 2)
                self.assertIn("prompt command", output.getvalue())

    def test_runtime_run_dry_run_is_not_executable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                output = io.StringIO()
                with redirect_stdout(output):
                    exit_code = cli.main(["\\deli:run", "BR-001", "--dry-run"])

                self.assertEqual(exit_code, 2)
                self.assertIn("prompt command", output.getvalue())

    def test_business_requirements_require_test_section(self) -> None:
        text_without_test_section = "\n\n".join(
            section for section in BUSINESS_REQUIRED_SECTIONS if section != "## Требования к тестам"
        )

        errors = cli.validate_requirements_ready(text_without_test_section)

        self.assertTrue(any("## Требования к тестам" in error for error in errors))

    def test_draft_business_requirements_are_invalid(self) -> None:
        text = "\n\n".join(["---\nstatus: draft\n---", *BUSINESS_REQUIRED_SECTIONS, "Jenkins review"])

        errors = cli.validate_requirements_ready(text)

        self.assertTrue(any("draft" in error for error in errors))

    def test_validate_file_auto_rejects_unknown_document_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                path = Path("random.md")
                path.write_text("# Random\n\nJenkins review", encoding="utf-8")

                result = cli.RequirementsValidator().validate_file(path, document_type="auto")

                self.assertFalse(result.is_valid)
                self.assertEqual(result.document_type, "unknown")

    def test_feature_key_must_use_br_number_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                with self.assertRaises(SystemExit):
                    cli.main(["\\deli:feature", "../BAD", "Add export"])

    def test_prompt_only_commands_are_not_runtime_commands(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = cli.main(["\\deli:test", "BR-001"])

        self.assertEqual(exit_code, 2)
        self.assertIn("GigaCode", output.getvalue())

    def test_runtime_ci_is_prompt_only(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = cli.main(["\\deli:ci", "BR-001", "Add export"])

        self.assertEqual(exit_code, 2)
        self.assertIn("prompt command", output.getvalue())

    def test_mark_records_prompt_workflow_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                Path("docs/business-requirements").mkdir(parents=True)
                Path("docs/business-requirements/BR-001.md").write_text("Requirement", encoding="utf-8")

                output = io.StringIO()
                with redirect_stdout(output):
                    branch_exit_code = cli.main([
                        "\\deli:mark",
                        "BR-001",
                        "branch_created",
                        "--branch",
                        "ai/br-001-export",
                        "--base",
                        "main",
                    ])
                    implemented_exit_code = cli.main([
                        "\\deli:mark",
                        "BR-001",
                        "implemented",
                        "--branch",
                        "ai/br-001-export",
                    ])
                    exit_code = cli.main([
                        "\\deli:mark",
                        "BR-001",
                        "tests_created",
                        "--branch",
                        "ai/br-001-export",
                        "--base",
                        "main",
                        "--note",
                        "tests updated",
                        "--test-result",
                        "tests updated",
                    ])

                self.assertEqual(branch_exit_code, 0)
                self.assertEqual(implemented_exit_code, 0)
                self.assertEqual(exit_code, 0)
                state = json.loads(Path(".deli/state.json").read_text(encoding="utf-8"))
                checkpoint = state["checkpoints"]["BR-001"]
                self.assertEqual(checkpoint["completed_steps"], ["branch_created", "implemented", "tests_created"])
                self.assertEqual(checkpoint["branch_name"], "ai/br-001-export")
                self.assertEqual(checkpoint["base_branch"], "main")
                self.assertEqual(checkpoint["notes"], ["tests updated"])
                self.assertEqual(checkpoint["test_result"], "tests updated")
                self.assertIn("completed_at", checkpoint["steps"]["tests_created"])

                status_output = io.StringIO()
                with redirect_stdout(status_output):
                    status_code = cli.main(["\\deli:status", "BR-001"])

                self.assertEqual(status_code, 0)
                self.assertIn("checkpoint=BR-001", status_output.getvalue())
                self.assertIn("completed=branch_created,implemented,tests_created", status_output.getvalue())
                self.assertIn("next=reviewed", status_output.getvalue())

    def test_mark_rejects_out_of_order_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                with self.assertRaises(SystemExit):
                    cli.main(["\\deli:mark", "BR-001", "tests_created"])

    def test_resume_is_read_only_and_reports_next_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                with redirect_stdout(io.StringIO()):
                    cli.main(["\\deli:mark", "BR-001", "branch_created", "--branch", "ai/br-001-export"])

                output = io.StringIO()
                with redirect_stdout(output):
                    exit_code = cli.main(["\\deli:resume", "BR-001"])

                self.assertEqual(exit_code, 0)
                self.assertIn("checkpoint=BR-001", output.getvalue())
                self.assertIn("resume_mode=agent", output.getvalue())
                self.assertIn("next_step=implemented", output.getvalue())
                self.assertIn("agent_action=implement_code", output.getvalue())

    def test_subtask_state_is_recorded_and_reported_on_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                output = io.StringIO()
                with redirect_stdout(output):
                    cli.main(["\\deli:mark", "BR-001", "branch_created", "--branch", "ai/br-001-export"])
                    exit_code = cli.main([
                        "\\deli:subtask",
                        "BR-001",
                        "WT-001",
                        "in_progress",
                        "--title",
                        "Prepare mapping",
                        "--branch",
                        "ai/br-001-export",
                    ])

                self.assertEqual(exit_code, 0)
                state = json.loads(Path(".deli/state.json").read_text(encoding="utf-8"))
                checkpoint = state["checkpoints"]["BR-001"]
                self.assertEqual(checkpoint["subtask_order"], ["WT-001"])
                self.assertEqual(checkpoint["subtasks"]["WT-001"]["status"], "in_progress")
                self.assertEqual(checkpoint["subtasks"]["WT-001"]["title"], "Prepare mapping")
                self.assertEqual(checkpoint["branch_name"], "ai/br-001-export")

                status_output = io.StringIO()
                with redirect_stdout(status_output):
                    status_code = cli.main(["\\deli:status", "BR-001"])

                self.assertEqual(status_code, 0)
                self.assertIn("subtasks=0/1", status_output.getvalue())
                self.assertIn("next_subtask=WT-001", status_output.getvalue())

                resume_output = io.StringIO()
                with redirect_stdout(resume_output):
                    resume_code = cli.main(["\\deli:resume", "BR-001"])

                self.assertEqual(resume_code, 0)
                self.assertIn("next_step=implemented", resume_output.getvalue())
                self.assertIn("subtask_id=WT-001", resume_output.getvalue())
                self.assertIn("subtask_status=in_progress", resume_output.getvalue())

    def test_done_subtask_counts_as_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                with redirect_stdout(io.StringIO()):
                    cli.main(["\\deli:subtask", "BR-001", "WT-001", "planned", "--title", "Prepare mapping"])
                    exit_code = cli.main(["\\deli:subtask", "BR-001", "WT-001", "done", "--note", "implemented"])

                self.assertEqual(exit_code, 0)
                state = json.loads(Path(".deli/state.json").read_text(encoding="utf-8"))
                subtask = state["checkpoints"]["BR-001"]["subtasks"]["WT-001"]
                self.assertEqual(subtask["status"], "done")
                self.assertEqual(subtask["notes"], ["implemented"])
                self.assertIn("completed_at", subtask)

    def test_implemented_requires_all_subtasks_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                with redirect_stdout(io.StringIO()):
                    cli.main(["\\deli:mark", "BR-001", "branch_created", "--branch", "ai/br-001-export"])
                    cli.main(["\\deli:subtask", "BR-001", "WT-001", "planned", "--title", "Prepare mapping"])

                with self.assertRaises(SystemExit):
                    cli.main(["\\deli:mark", "BR-001", "implemented", "--branch", "ai/br-001-export"])

                with redirect_stdout(io.StringIO()):
                    cli.main(["\\deli:subtask", "BR-001", "WT-001", "done"])
                    exit_code = cli.main(["\\deli:mark", "BR-001", "implemented", "--branch", "ai/br-001-export"])

                self.assertEqual(exit_code, 0)
                state = json.loads(Path(".deli/state.json").read_text(encoding="utf-8"))
                self.assertIn("implemented", state["checkpoints"]["BR-001"]["completed_steps"])

    def test_mark_rejects_unknown_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                with self.assertRaises(SystemExit):
                    cli.main(["\\deli:mark", "BR-001", "unknown_step"])

    def test_mark_requires_real_urls_and_post_merge_ci_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                mark_steps_until_pr_ready()

                with self.assertRaises(SystemExit):
                    cli.main(["\\deli:mark", "BR-001", "ci_passed", "--build-url", "https://jenkins/build/1"])

                with redirect_stdout(io.StringIO()):
                    cli.main(["\\deli:mark", "BR-001", "branch_pushed"])

                with self.assertRaises(SystemExit):
                    cli.main(["\\deli:mark", "BR-001", "pr_created"])

                with redirect_stdout(io.StringIO()):
                    cli.main(["\\deli:mark", "BR-001", "pr_created", "--pr-url", "https://git/pr/1"])

                with self.assertRaises(SystemExit):
                    cli.main(["\\deli:mark", "BR-001", "pr_merged"])

                with redirect_stdout(io.StringIO()):
                    cli.main(["\\deli:mark", "BR-001", "pr_merged", "--pr-url", "https://git/pr/1"])

                with self.assertRaises(SystemExit):
                    cli.main(["\\deli:mark", "BR-001", "ci_passed"])

    def test_repeated_implementation_invalidates_later_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with working_directory(tmp):
                mark_full_workflow()

                with redirect_stdout(io.StringIO()):
                    cli.main(["\\deli:mark", "BR-001", "implemented", "--branch", "ai/br-001-export"])

                state = json.loads(Path(".deli/state.json").read_text(encoding="utf-8"))
                checkpoint = state["checkpoints"]["BR-001"]
                self.assertEqual(checkpoint["completed_steps"], ["branch_created", "implemented"])
                self.assertNotIn("test_result", checkpoint)
                self.assertNotIn("review_summary", checkpoint)
                self.assertNotIn("build_url", checkpoint)
                self.assertNotIn("pr_url", checkpoint)
                self.assertNotIn("tests_created", checkpoint["steps"])


def mark_steps_until_pr_ready() -> None:
    with redirect_stdout(io.StringIO()):
        cli.main(["\\deli:mark", "BR-001", "branch_created", "--branch", "ai/br-001-export", "--base", "main"])
        cli.main(["\\deli:mark", "BR-001", "implemented", "--branch", "ai/br-001-export"])
        cli.main(["\\deli:mark", "BR-001", "tests_created", "--test-result", "tests updated"])
        cli.main(["\\deli:mark", "BR-001", "reviewed", "--review-summary", "review accepted"])


def mark_full_workflow() -> None:
    mark_steps_until_pr_ready()
    with redirect_stdout(io.StringIO()):
        cli.main(["\\deli:mark", "BR-001", "branch_pushed"])
        cli.main(["\\deli:mark", "BR-001", "pr_created", "--pr-url", "https://git/pr/1"])
        cli.main(["\\deli:mark", "BR-001", "pr_merged", "--pr-url", "https://git/pr/1"])
        cli.main(["\\deli:mark", "BR-001", "ci_passed", "--build-url", "https://jenkins/build/1"])


class working_directory:
    def __init__(self, path: str) -> None:
        self.path = path
        self.previous = os.getcwd()

    def __enter__(self) -> None:
        os.chdir(self.path)

    def __exit__(self, *args) -> None:
        os.chdir(self.previous)
