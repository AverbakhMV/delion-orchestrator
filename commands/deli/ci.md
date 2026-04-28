---
description: Запустить Jenkins CI loop Delion для фичи через GigaCode MCP/tools.
---

# /deli:ci — Jenkins CI loop

Запусти post-merge CI loop для `FEATURE_KEY` через доступные Jenkins MCP/tools GigaCode.

## Использование

```text
/deli:ci BR-001
```

## Алгоритм

1. Проверь, что PR по `FEATURE_KEY` уже merge-нут в основную ветку.

2. Убедись, что перед CI пройдены:
   - `/deli:validate system`;
   - `/deli:validate feature FEATURE_KEY`;
   - `/deli:test FEATURE_KEY`, то есть тесты созданы или обновлены, но не запускались;
   - `/deli:review FEATURE_KEY`, то есть code review принят;
   - feature branch запушена в удаленный репозиторий;
   - PR создан;
   - PR merge-нут в основную ветку.

   Не запускай Jenkins до merge PR. Jenkins собирает удаленный репозиторий после merge в основную ветку.

3. Через Jenkins MCP/tools GigaCode запусти релевантный job/build для основной ветки после merge.

4. Дождись результата или получи ссылку на build, если job асинхронный.

5. Если CI упал:
   - покажи краткий статус;
   - выдели ошибки из лога;
   - верни задачу основному агенту для исправления в новой follow-up feature branch или по процессу проекта;
   - после исправления повтори полный цикл: тестовые файлы, review, push, PR, merge и только потом `/deli:ci FEATURE_KEY`.

6. Если CI прошел, выведи:

```text
═══════════════════════════════════════════
CI PASSED
═══════════════════════════════════════════

Feature: FEATURE_KEY
Branch: [branch]
Jenkins: [build url]

Next:
  → workflow complete
═══════════════════════════════════════════
```

7. Зафиксируй прохождение CI в state:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:mark FEATURE_KEY ci_passed --build-url "[Jenkins build url]" --test-result "[CI summary]"
```

## Важно

- Не используй Python runtime как реальный CI.
- Реальный Jenkins должен запускаться через MCP/tools GigaCode после merge PR.
- Не запускай Jenkins CI до push, PR и merge в основную ветку.
- Не используй Jenkins как pre-push или pre-PR gate.
