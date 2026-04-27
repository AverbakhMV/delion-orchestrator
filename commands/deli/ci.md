---
description: Запустить Jenkins CI loop Delion для фичи через GigaCode MCP/tools.
---

# /deli:ci — Jenkins CI loop

Запусти CI loop для `FEATURE_KEY` через доступные Jenkins MCP/tools GigaCode.

## Использование

```text
/deli:ci BR-001
```

## Алгоритм

1. Проверь, что текущая ветка соответствует фиче `FEATURE_KEY`.

2. Убедись, что перед CI пройдены:
   - `/deli:validate system`;
   - `/deli:validate feature FEATURE_KEY`;
   - `/deli:test FEATURE_KEY`;
   - `/deli:review FEATURE_KEY`.

3. Через Jenkins MCP/tools GigaCode запусти релевантный job/build для текущей feature branch.

4. Дождись результата или получи ссылку на build, если job асинхронный.

5. Если CI упал:
   - покажи краткий статус;
   - выдели ошибки из лога;
   - верни задачу основному агенту для исправления в той же feature branch;
   - после исправления повтори `/deli:test FEATURE_KEY`, `/deli:review FEATURE_KEY` и `/deli:ci FEATURE_KEY`.

6. Если CI прошел, выведи:

```text
═══════════════════════════════════════════
CI PASSED
═══════════════════════════════════════════

Feature: FEATURE_KEY
Branch: [branch]
Jenkins: [build url]

Next:
  → push branch
  → create PR
═══════════════════════════════════════════
```

7. Зафиксируй прохождение CI в state:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" \deli:mark FEATURE_KEY ci_passed --build-url "[Jenkins build url]" --test-result "[CI summary]"
```

## Важно

- Не используй Python runtime как реальный CI.
- Реальный Jenkins должен запускаться через MCP/tools GigaCode.
- Не переходи к PR, если Jenkins build не прошел.
