def fit_to_daily_budget(items: list[dict], daily_minutes: int = 60) -> list[dict]:
    result, used, day = [], 0, 0
    for item in items:
        if used + item["minutes"] > daily_minutes:
            day, used = day + 1, 0
        result.append({**item, "day_offset": day})
        used += item["minutes"]
    return result
