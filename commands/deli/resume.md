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

Дальше продолжай по полям вывода:

- если `agent_action=execute_prompt_stage`, выполни инструкции из `prompt_file`;
- если `agent_action=implement_code`, продолжи реализацию в текущей feature branch;
- если `agent_action=mcp_git_branch`, создай или переключись на feature branch через GigaCode git/SCM MCP/tools;
- если `agent_action=mcp_git_push`, выполни push через GigaCode git/SCM MCP/tools;
- если `agent_action=mcp_create_pr`, создай PR через GigaCode git/SCM MCP/tools;
- если `agent_action=none`, workflow уже завершен.

Не создавай новую ветку для той же фичи и не пропускай `tests_created` или `reviewed`.
