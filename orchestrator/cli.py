from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

from orchestrator.agents import DeveloperAgent, PlannerAgent, ReviewerAgent, TestAgent
from orchestrator.artifacts import ProjectAnalyzer, write_business_requirements, write_system_requirements
from orchestrator.ci import InMemoryCIRunner
from orchestrator.models import FeatureRequest, WorkflowCheckpoint, WorkflowResult
from orchestrator.scm import InMemoryScmClient
from orchestrator.validation import RequirementsValidator
from orchestrator.workflow import WorkflowEngine


COMMAND_PREFIXES = {"\\deli", "/deli", "deli"}
STATE_DIR = Path(".deli")
STATE_FILE = STATE_DIR / "state.json"


def main(argv: list[str] | None = None) -> int:
    configure_output_encoding()
    args = list(sys.argv[1:] if argv is None else argv)
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
    if command == "plan":
        return plan_command(command_args)
    if command == "run":
        return run_command(command_args)
    if command == "run-file":
        return run_file_command(command_args)
    if command == "validate":
        return validate_command(command_args)
    if command == "resume":
        return resume_command(command_args)
    if command == "status":
        return status_command(command_args)
    if command == "ci":
        return ci_command(command_args)

    print(f"Неизвестная команда Delion: {command}")
    print_help()
    return 2


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
    print("Статус: требуется валидация и дополнение человеком.")
    return 0


def plan_command(args: list[str]) -> int:
    feature_key, requirement_text, base_branch = parse_feature_args(args)
    planner = PlannerAgent()
    plan = planner.build_plan(
        FeatureRequest(
            key=feature_key,
            requirement_text=requirement_text,
            base_branch=base_branch,
        )
    )

    print(f"feature: {plan.feature.key}")
    print(f"base_branch: {plan.feature.base_branch}")
    print(f"branch: {plan.branch_name}")
    print(f"summary: {plan.summary}")
    print("work_items:")
    for index, item in enumerate(plan.work_items, start=1):
        print(f"  {index}. {item.title}: {item.description}")
    return 0


def run_command(args: list[str]) -> int:
    allow_draft = "--allow-draft" in args
    if allow_draft:
        args = [arg for arg in args if arg != "--allow-draft"]

    base_branch = "master"
    if "--base" in args:
        base_index = args.index("--base")
        try:
            base_branch = args[base_index + 1]
        except IndexError as exc:
            raise SystemExit("--base требует имя ветки") from exc
        args = args[:base_index] + args[base_index + 2 :]

    if len(args) != 1:
        raise SystemExit("Usage: \\deli:run FEATURE_KEY [--base master] [--allow-draft]")

    feature_key = args[0]
    requirements_file = business_requirements_path(feature_key)
    if not requirements_file.exists():
        raise SystemExit(
            f"Файл бизнес-требований не найден: {requirements_file}. "
            f"Сначала выполните \\deli:feature {feature_key} \"Описание задачи\""
        )

    requirement_text = requirements_file.read_text(encoding="utf-8")
    if not allow_draft:
        validation_errors = validate_ready_for_run(requirements_file)
        if validation_errors:
            print("Workflow остановлен: файл требований еще не готов.")
            for error in validation_errors:
                print(f"- {error}")
            print("Дополните файл и повторите запуск или используйте --allow-draft только для отладки.")
            return 1

    result = build_engine().run_feature(
        feature_key=feature_key,
        requirement_text=requirement_text,
        base_branch=base_branch,
        requirements_file=str(requirements_file),
        checkpoint_callback=save_checkpoint,
    )
    save_result(result)
    print(result.summary())
    return 0 if not result.errors else 1


def run_file_command(args: list[str]) -> int:
    if not args:
        raise SystemExit("Usage: \\deli:run FEATURE_KEY [--base master] [--allow-draft]")
    print("Команда \\deli:run-file устарела. Используйте \\deli:run FEATURE_KEY.")
    return run_command(args[:1] + args[2:] if len(args) > 1 else args)


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
    checkpoint = load_state().get("checkpoints", {}).get(feature_key)
    if not checkpoint:
        print(f"Checkpoint не найден для фичи: {feature_key}")
        return 1

    requirements_file = checkpoint.get("requirements_file")
    requirement_text = checkpoint["requirement_text"]
    if requirements_file:
        path = Path(requirements_file)
        if path.exists():
            requirement_text = path.read_text(encoding="utf-8")

    result = build_engine().run_feature(
        feature_key=feature_key,
        requirement_text=requirement_text,
        base_branch=checkpoint.get("base_branch", "master"),
        completed_steps=set(checkpoint.get("completed_steps", [])),
        requirements_file=requirements_file,
        checkpoint_callback=save_checkpoint,
    )
    save_result(result)
    print(result.summary())
    return 0 if not result.errors else 1


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


def ci_command(args: list[str]) -> int:
    feature_key, requirement_text, base_branch = parse_feature_args(args)
    planner = PlannerAgent()
    ci = InMemoryCIRunner()
    plan = planner.build_plan(
        FeatureRequest(
            key=feature_key,
            requirement_text=requirement_text,
            base_branch=base_branch,
        )
    )
    result = ci.run_validation_loop(plan=plan, branch_name=plan.branch_name, max_attempts=3)
    print(f"feature={feature_key} | branch={plan.branch_name} | ci={result.status.value} | build={result.build_url}")
    return 0 if result.status.value == "success" else 1


def parse_feature_args(args: list[str]) -> tuple[str, str, str]:
    if len(args) < 2:
        raise SystemExit("Usage: \\deli:<plan|run|feature|ci> FEATURE_KEY REQUIREMENT_TEXT [--base master]")

    base_branch = "master"
    if "--base" in args:
        base_index = args.index("--base")
        try:
            base_branch = args[base_index + 1]
        except IndexError as exc:
            raise SystemExit("--base требует имя ветки") from exc
        args = args[:base_index] + args[base_index + 2 :]

    feature_key = args[0]
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
    return Path("docs") / "business-requirements" / f"{feature_key}.md"


def parse_document_type(args: list[str]) -> str:
    if not args:
        return "auto"
    if len(args) == 2 and args[0] == "--type" and args[1] in {"system", "business", "auto"}:
        return args[1]
    raise SystemExit("Usage: \\deli:validate file PATH [--type system|business|auto]")


def build_engine() -> WorkflowEngine:
    return WorkflowEngine(
        planner=PlannerAgent(),
        developer=DeveloperAgent(),
        tester=TestAgent(),
        reviewer=ReviewerAgent(),
        scm=InMemoryScmClient(default_base_branch="master"),
        ci=InMemoryCIRunner(),
    )


def save_result(result: WorkflowResult) -> None:
    STATE_DIR.mkdir(exist_ok=True)
    state = load_state()
    runs = state.setdefault("runs", {})
    runs[result.feature_key] = asdict(result)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def save_checkpoint(checkpoint: WorkflowCheckpoint) -> None:
    STATE_DIR.mkdir(exist_ok=True)
    state = load_state()
    checkpoints = state.setdefault("checkpoints", {})
    checkpoints[checkpoint.feature_key] = asdict(checkpoint)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"runs": {}}
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
                "  \\deli:plan FEATURE_KEY REQUIREMENT_TEXT [--base master]",
                "  \\deli:run FEATURE_KEY [--base master] [--allow-draft]",
                "  \\deli:validate <system|feature|file> [FEATURE_KEY|PATH]",
                "  \\deli:resume FEATURE_KEY",
                "  \\deli:status [FEATURE_KEY]",
                "  \\deli:ci FEATURE_KEY REQUIREMENT_TEXT [--base master]",
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
