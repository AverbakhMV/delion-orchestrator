from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from orchestrator.artifacts import ProjectAnalyzer, write_business_requirements, write_system_requirements
from orchestrator.models import WorkflowStep
from orchestrator.validation import RequirementsValidator


COMMAND_PREFIXES = {"\\deli", "/deli", "deli"}
STATE_DIR = Path(".deli")
STATE_FILE = STATE_DIR / "state.json"
FEATURE_KEY_PATTERN = re.compile(r"^BR-\d{3,}$")
WORKFLOW_STEP_ORDER = [
    WorkflowStep.BRANCH_CREATED.value,
    WorkflowStep.IMPLEMENTED.value,
    WorkflowStep.TESTS_CREATED.value,
    WorkflowStep.REVIEWED.value,
    WorkflowStep.CI_PASSED.value,
    WorkflowStep.BRANCH_PUSHED.value,
    WorkflowStep.PR_CREATED.value,
]
INVALIDATING_STEPS = {
    WorkflowStep.IMPLEMENTED.value,
    WorkflowStep.TESTS_CREATED.value,
}
REQUIRED_MARK_OPTIONS = {
    WorkflowStep.CI_PASSED.value: ["build-url"],
    WorkflowStep.PR_CREATED.value: ["pr-url"],
}
STEP_FIELDS = {
    WorkflowStep.TESTS_CREATED.value: ["test_result"],
    WorkflowStep.REVIEWED.value: ["review_summary"],
    WorkflowStep.CI_PASSED.value: ["build_url"],
    WorkflowStep.PR_CREATED.value: ["pr_url"],
}
NEXT_STEP_AGENT_ACTIONS = {
    WorkflowStep.BRANCH_CREATED.value: {
        "agent_action": "mcp_git_branch",
        "mcp_action": "create_or_switch_feature_branch",
    },
    WorkflowStep.IMPLEMENTED.value: {
        "agent_action": "implement_code",
    },
    WorkflowStep.TESTS_CREATED.value: {
        "agent_action": "execute_prompt_stage",
        "prompt_file": "commands/deli/test.md",
    },
    WorkflowStep.REVIEWED.value: {
        "agent_action": "execute_prompt_stage",
        "prompt_file": "commands/deli/review.md",
    },
    WorkflowStep.CI_PASSED.value: {
        "agent_action": "execute_prompt_stage",
        "prompt_file": "commands/deli/ci.md",
    },
    WorkflowStep.BRANCH_PUSHED.value: {
        "agent_action": "mcp_git_push",
        "mcp_action": "push_feature_branch",
    },
    WorkflowStep.PR_CREATED.value: {
        "agent_action": "mcp_create_pr",
        "mcp_action": "create_pull_request",
    },
}


def main(argv: list[str] | None = None) -> int:
    configure_output_encoding()
    args = list(sys.argv[1:] if argv is None else argv)
    args = apply_project_root_arg(args)
    if not args:
        print_help()
        return 0

    args = normalize_command_args(args)

    if not args:
        print_help()
        return 0

    command = args[0]
    command_args = args[1:]

    if command in {"help", "-h", "--help"}:
        print_help()
        return 0
    if command == "init":
        return init_command(command_args)
    if command == "feature":
        return feature_command(command_args)
    if command in {"plan", "run", "run-file", "ci", "test", "review"}:
        return prompt_only_command(command)
    if command == "validate":
        return validate_command(command_args)
    if command == "mark":
        return mark_command(command_args)
    if command == "resume":
        return resume_command(command_args)
    if command == "status":
        return status_command(command_args)
    if command in {"test", "review"}:
        print(f"Команда \\deli:{command} выполняется агентом GigaCode через prompt, а не Python runtime.")
        return 2

    print(f"Неизвестная команда Delion: {command}")
    print_help()
    return 2


def prompt_only_command(command: str) -> int:
    print(
        f"\\deli:{command} is a GigaCode prompt command, not a Python runtime command. "
        "Python runtime is limited to local document/state operations: init, feature, validate, mark, resume, status."
    )
    return 2


def apply_project_root_arg(args: list[str]) -> list[str]:
    if "--project-root" not in args:
        return args

    root_index = args.index("--project-root")
    try:
        project_root = Path(args[root_index + 1]).expanduser().resolve()
    except IndexError as exc:
        raise SystemExit("--project-root требует путь к проекту") from exc

    if not project_root.exists() or not project_root.is_dir():
        raise SystemExit(f"Директория проекта не найдена: {project_root}")

    os.chdir(project_root)
    return args[:root_index] + args[root_index + 2 :]


def normalize_command_args(args: list[str]) -> list[str]:
    first = args[0]
    for prefix in COMMAND_PREFIXES:
        if first == prefix:
            return args[1:]
        command_prefix = f"{prefix}:"
        if first.startswith(command_prefix):
            return [first[len(command_prefix) :], *args[1:]]
    return args


def init_command(args: list[str]) -> int:
    if args:
        raise SystemExit("Usage: \\deli:init")

    initialize_project_structure()
    snapshot = ProjectAnalyzer().analyze(Path.cwd())
    output_path = write_system_requirements(snapshot)
    print(f"Создан файл системных требований: {output_path}")
    print("Статус: требуется валидация и дополнение человеком.")
    return 0


def feature_command(args: list[str]) -> int:
    feature_key, task_text, _base_branch = parse_feature_args(args)
    source_file = None
    if task_text.startswith("@"):
        source_file = Path(task_text[1:])
        if not source_file.exists():
            raise SystemExit(f"Файл требований не найден: {source_file}")
        task_text = source_file.read_text(encoding="utf-8")

    output_path = write_business_requirements(feature_key, task_text, source_file=source_file)
    print(f"Создан файл бизнес-требований: {output_path}")
    print("Статус: draft. Требуется проверка и дополнение человеком.")
    return 0


def validate_command(args: list[str]) -> int:
    if not args:
        raise SystemExit("Usage: \\deli:validate <system|feature|file> [FEATURE_KEY|PATH]")

    target = args[0]
    validator = RequirementsValidator()

    if target == "system":
        path = Path(args[1]) if len(args) > 1 else system_requirements_path()
        result = validator.validate_file(path, document_type="system")
        print_validation_result(result)
        return 0 if result.is_valid else 1

    if target == "feature":
        if len(args) != 2:
            raise SystemExit("Usage: \\deli:validate feature FEATURE_KEY")
        path = business_requirements_path(args[1])
        result = validator.validate_file(path, document_type="business")
        print_validation_result(result)
        return 0 if result.is_valid else 1

    if target == "file":
        if len(args) < 2:
            raise SystemExit("Usage: \\deli:validate file PATH [--type system|business|auto]")
        path = Path(args[1])
        document_type = parse_document_type(args[2:])
        result = validator.validate_file(path, document_type=document_type)
        print_validation_result(result)
        return 0 if result.is_valid else 1

    raise SystemExit("Usage: \\deli:validate <system|feature|file> [FEATURE_KEY|PATH]")


def resume_command(args: list[str]) -> int:
    if len(args) != 1:
        raise SystemExit("Usage: \\deli:resume FEATURE_KEY")

    feature_key = args[0]
    validate_feature_key(feature_key)
    checkpoint = load_state().get("checkpoints", {}).get(feature_key)
    if not checkpoint:
        print(f"Checkpoint не найден для фичи: {feature_key}")
        return 1

    print_checkpoint_status(checkpoint)
    next_step = next_workflow_step(checkpoint.get("completed_steps", []))
    print("resume_mode=agent")
    print(f"feature={feature_key}")
    if next_step:
        print(f"next_step={next_step}")
        for key, value in NEXT_STEP_AGENT_ACTIONS[next_step].items():
            print(f"{key}={value}")
    else:
        print("next_step=done")
        print("agent_action=none")
    return 0


def status_command(args: list[str]) -> int:
    feature_key = args[0] if args else None
    state = load_state()
    runs = state.get("runs", {})
    checkpoints = state.get("checkpoints", {})

    if feature_key:
        run = runs.get(feature_key)
        checkpoint = checkpoints.get(feature_key)
        if not run and not checkpoint:
            print(f"Запуск Delion не найден для фичи: {feature_key}")
            return 1
        if run:
            print_run_status(run)
        if checkpoint:
            print_checkpoint_status(checkpoint)
        return 0

    if not runs and not checkpoints:
        print("Запуски Delion не найдены.")
        return 0

    for run in runs.values():
        print_run_status(run)
    for checkpoint in checkpoints.values():
        print_checkpoint_status(checkpoint)
    return 0


def mark_command(args: list[str]) -> int:
    if len(args) < 2:
        raise SystemExit(mark_usage())

    feature_key = args[0]
    validate_feature_key(feature_key)
    step = args[1]
    allowed_steps = {workflow_step.value for workflow_step in WorkflowStep}
    if step not in allowed_steps:
        raise SystemExit(f"STEP должен быть одним из: {', '.join(sorted(allowed_steps))}")

    options = parse_mark_options(args[2:])
    validate_required_mark_options(step, options)
    state = load_state()
    checkpoints = state.setdefault("checkpoints", {})
    checkpoint = checkpoints.setdefault(
        feature_key,
        {
            "feature_key": feature_key,
            "requirement_text": read_requirement_text(feature_key),
            "base_branch": options.get("base") or "unknown",
            "branch_name": options.get("branch") or "",
            "completed_steps": [],
            "requirements_file": str(business_requirements_path(feature_key)),
            "status": "planned",
        },
    )

    completed_steps = checkpoint.setdefault("completed_steps", [])
    validate_checkpoint_order(step, completed_steps)
    if step in INVALIDATING_STEPS:
        invalidate_following_steps(checkpoint, step)
        completed_steps = checkpoint.setdefault("completed_steps", [])
    if step not in completed_steps:
        completed_steps.append(step)
    if options.get("branch"):
        checkpoint["branch_name"] = options["branch"]
    if options.get("base"):
        checkpoint["base_branch"] = options["base"]
    checkpoint["status"] = options.get("status") or step
    checkpoint["updated_at"] = now_utc()
    if options.get("note"):
        notes = checkpoint.setdefault("notes", [])
        notes.append(options["note"])
    if options.get("build-url"):
        checkpoint["build_url"] = options["build-url"]
    if options.get("pr-url"):
        checkpoint["pr_url"] = options["pr-url"]
    if options.get("review-summary"):
        checkpoint["review_summary"] = options["review-summary"]
    if options.get("test-result"):
        checkpoint["test_result"] = options["test-result"]
    if options.get("last-error"):
        checkpoint["last_error"] = options["last-error"]

    steps = checkpoint.setdefault("steps", {})
    step_record = steps.setdefault(step, {})
    step_record["completed_at"] = now_utc()
    for option_name in ["branch", "base", "note", "build-url", "pr-url", "review-summary", "test-result", "last-error"]:
        if options.get(option_name):
            step_record[option_name.replace("-", "_")] = options[option_name]

    STATE_DIR.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"checkpoint={feature_key} | completed={','.join(completed_steps)} | status={checkpoint['status']}")
    return 0


def parse_mark_options(args: list[str]) -> dict[str, str]:
    options: dict[str, str] = {}
    allowed_options = {
        "--branch",
        "--base",
        "--status",
        "--note",
        "--build-url",
        "--pr-url",
        "--review-summary",
        "--test-result",
        "--last-error",
    }
    index = 0
    while index < len(args):
        option = args[index]
        if option not in allowed_options:
            raise SystemExit(mark_usage())
        try:
            value = args[index + 1]
        except IndexError as exc:
            raise SystemExit(f"{option} требует значение") from exc
        options[option.removeprefix("--")] = value
        index += 2
    return options


def mark_usage() -> str:
    return (
        "Usage: \\deli:mark FEATURE_KEY STEP [--branch BRANCH] [--base BASE] "
        "[--status STATUS] [--note TEXT] [--build-url URL] [--pr-url URL] "
        "[--review-summary TEXT] [--test-result TEXT] [--last-error TEXT]"
    )


def validate_checkpoint_order(step: str, completed_steps: list[str]) -> None:
    expected_index = WORKFLOW_STEP_ORDER.index(step)
    missing_steps = [
        required_step
        for required_step in WORKFLOW_STEP_ORDER[:expected_index]
        if required_step not in completed_steps
    ]
    if missing_steps:
        raise SystemExit(
            f"Cannot mark {step}: missing previous checkpoint(s): {', '.join(missing_steps)}"
        )


def validate_required_mark_options(step: str, options: dict[str, str]) -> None:
    missing_options = [
        option_name for option_name in REQUIRED_MARK_OPTIONS.get(step, []) if not options.get(option_name)
    ]
    if missing_options:
        formatted = ", ".join(f"--{option_name}" for option_name in missing_options)
        raise SystemExit(f"Cannot mark {step}: missing required option(s): {formatted}")


def invalidate_following_steps(checkpoint: dict, step: str) -> None:
    completed_steps = checkpoint.setdefault("completed_steps", [])
    if step not in completed_steps:
        return

    step_index = WORKFLOW_STEP_ORDER.index(step)
    removed_steps = [
        completed_step
        for completed_step in completed_steps
        if WORKFLOW_STEP_ORDER.index(completed_step) > step_index
    ]
    if not removed_steps:
        return

    checkpoint["completed_steps"] = [
        completed_step
        for completed_step in completed_steps
        if WORKFLOW_STEP_ORDER.index(completed_step) <= step_index
    ]

    step_records = checkpoint.get("steps", {})
    for removed_step in removed_steps:
        step_records.pop(removed_step, None)
        for field_name in STEP_FIELDS.get(removed_step, []):
            checkpoint.pop(field_name, None)


def next_workflow_step(completed_steps: list[str]) -> str | None:
    completed = set(completed_steps)
    for step in WORKFLOW_STEP_ORDER:
        if step not in completed:
            return step
    return None


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_requirement_text(feature_key: str) -> str:
    path = business_requirements_path(feature_key)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def parse_feature_args(args: list[str]) -> tuple[str, str, str]:
    if len(args) < 2:
        raise SystemExit("Usage: \\deli:feature FEATURE_KEY REQUIREMENT_TEXT")

    base_branch = "master"
    if "--base" in args:
        base_index = args.index("--base")
        try:
            base_branch = args[base_index + 1]
        except IndexError as exc:
            raise SystemExit("--base требует имя ветки") from exc
        args = args[:base_index] + args[base_index + 2 :]

    feature_key = args[0]
    validate_feature_key(feature_key)
    requirement_text = " ".join(args[1:]).strip()
    if not requirement_text:
        raise SystemExit("Текст требования не может быть пустым")
    return feature_key, requirement_text, base_branch


def validate_requirements_ready(requirement_text: str) -> list[str]:
    return RequirementsValidator().validate_text(requirement_text, document_type="business")


def validate_ready_for_run(requirements_file: Path) -> list[str]:
    validator = RequirementsValidator()
    errors = []

    system_result = validator.validate_file(system_requirements_path(), document_type="system")
    errors.extend([f"Системные требования: {error}" for error in system_result.errors])

    business_result = validator.validate_file(requirements_file, document_type="business")
    errors.extend([f"Бизнес-требования: {error}" for error in business_result.errors])
    return errors


def system_requirements_path() -> Path:
    return Path("docs") / "system-requirements.md"


def business_requirements_path(feature_key: str) -> Path:
    validate_feature_key(feature_key)
    return Path("docs") / "business-requirements" / f"{feature_key}.md"


def validate_feature_key(feature_key: str) -> None:
    if not FEATURE_KEY_PATTERN.fullmatch(feature_key):
        raise SystemExit("FEATURE_KEY должен иметь формат BR-001.")


def parse_document_type(args: list[str]) -> str:
    if not args:
        return "auto"
    if len(args) == 2 and args[0] == "--type" and args[1] in {"system", "business", "auto"}:
        return args[1]
    raise SystemExit("Usage: \\deli:validate file PATH [--type system|business|auto]")


def initialize_project_structure() -> None:
    STATE_DIR.mkdir(exist_ok=True)
    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"runs": {}, "checkpoints": {}}, indent=2), encoding="utf-8")
    Path("docs", "business-requirements").mkdir(parents=True, exist_ok=True)
    Path("docs", "specs").mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"runs": {}, "checkpoints": {}}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def print_run_status(run: dict) -> None:
    parts = [
        f"feature={run['feature_key']}",
        f"branch={run['branch_name']}",
        f"status={run['status']}",
    ]
    pull_request = run.get("pull_request")
    if pull_request:
        parts.append(f"pr={pull_request['url']}")
    ci_result = run.get("ci_result")
    if ci_result:
        parts.append(f"ci={ci_result['status']}")
    print(" | ".join(parts))


def print_checkpoint_status(checkpoint: dict) -> None:
    parts = [
        f"checkpoint={checkpoint['feature_key']}",
        f"branch={checkpoint['branch_name']}",
        f"completed={','.join(checkpoint.get('completed_steps', [])) or 'none'}",
    ]
    if checkpoint.get("requirements_file"):
        parts.append(f"requirements={checkpoint['requirements_file']}")
    if checkpoint.get("build_url"):
        parts.append(f"build={checkpoint['build_url']}")
    if checkpoint.get("pr_url"):
        parts.append(f"pr={checkpoint['pr_url']}")
    parts.append(f"next={next_workflow_step(checkpoint.get('completed_steps', [])) or 'done'}")
    print(" | ".join(parts))


def print_validation_result(result) -> None:
    status = "VALID" if result.is_valid else "INVALID"
    print(f"{status}: {result.path} ({result.document_type})")
    for error in result.errors:
        print(f"- ERROR: {error}")
    for warning in result.warnings:
        print(f"- WARN: {warning}")


def print_help() -> None:
    print(
        "\n".join(
            [
                "Delion CLI",
                "",
                "Команды:",
                "  \\deli:help",
                "  \\deli:init",
                "  \\deli:feature FEATURE_KEY REQUIREMENT_TEXT",
                "  \\deli:feature FEATURE_KEY @path/to/requirements.md",
                "  \\deli:validate <system|feature|file> [FEATURE_KEY|PATH]",
                "  \\deli:mark FEATURE_KEY STEP [--branch BRANCH] [--base BASE] [--status STATUS]",
                "  \\deli:resume FEATURE_KEY",
                "  \\deli:status [FEATURE_KEY]",
                "",
                "Политика:",
                "  одна фича = одна ветка = один PR",
                "  один execution agent выполняет реализацию",
                "  тесты создаются или обновляются для всех бизнес-требований до review и CI",
                "  CI loop ограничен количеством retry",
                "  системные и бизнес-требования требуют валидации человеком",
            ]
        )
    )

def configure_output_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
