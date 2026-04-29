---
description: Продолжить workflow Delion с последнего checkpoint.
---

Продолжи workflow Delion с последнего сохраненного checkpoint реального GigaCode/MCP workflow.

Сначала выполни read-only runtime-команду:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:resume FEATURE_KEY
```

Runtime ничего не выполняет сам. Он возвращает структурированный вывод для агента:

```text
resume_mode=agent
feature=FEATURE_KEY
next_step=reviewed
agent_action=execute_prompt_stage
prompt_file=commands/deli/review.md
```

Если фича была разбита на work items, runtime также может вернуть:

```text
subtask_id=WT-001
subtask_status=in_progress
subtask_title=Краткое название подзадачи
```

Дальше продолжай по полям вывода:

- если `agent_action=execute_prompt_stage`, выполни инструкции из `prompt_file`;
- если `agent_action=implement_code` и указан `subtask_id`, продолжи именно эту подзадачу в текущей feature branch, затем зафиксируй ее через `/deli:subtask FEATURE_KEY SUBTASK_ID done`;
- если `agent_action=implement_code` без `subtask_id`, продолжи реализацию в текущей feature branch;
- если `agent_action=mcp_git_branch`, создай или переключись на feature branch через GigaCode git/SCM MCP/tools;
- если `agent_action=mcp_git_push`, выполни push через GigaCode git/SCM MCP/tools;
- если `agent_action=mcp_create_pr`, создай PR через GigaCode git/SCM MCP/tools;
- если `agent_action=none`, workflow уже завершен.

Не создавай новую ветку для той же фичи и не пропускай `tests_created` или `reviewed`. Внутренние work items не создают отдельных веток и не заменяют общий checkpoint фичи.
