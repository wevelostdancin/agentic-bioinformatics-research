# SDD ledger — plan: docs/superpowers/plans/2026-11-25-reproducibility-must-fixes.md

## Pre-flight: shared interfaces

- Task 1 -> Task 3: aggregate_runs читает metrics.json с полем findings; Task 3 добавляет confirmed_count рядом — совместимо.
- Task 2 -> Task 6: валидатор требует поля, которые шаблон начинает записывать в Task 2; финальная проверка их проверяет.
- Task 4 -> Task 5: unit _EVIDENCE импортируется в run.py; trace использует event_id, не пересекается.
- Task 5 -> rubric: новый ключ mast_categories не ломает старый тест на подмножество ключей.

## Rulings

- Execution method: Native перенесён с предыдущего плана по выбору пользователя.
- Начальная точка: HEAD 84e008b (после предыдущего fix pass и пуша).
