def rubric() -> dict:
    return {
        "evidence": "Есть исполняемое доказательство: PoC, тест, крэш или ground truth",
        "coverage": "Покрыта ли ячейка матрицы поверхность атаки × класс уязвимости",
        "novelty": "Находка не дублирует уже подтверждённые",
        "mast_categories": [
            "system design",
            "inter-agent misalignment",
            "task verification",
        ],
    }
