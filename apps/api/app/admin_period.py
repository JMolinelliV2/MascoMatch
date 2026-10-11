from fastapi import HTTPException


def period_filters(column, from_at=None, to_at=None):
    """Timezone-aware half-open range shared by admin counters and lists."""
    if from_at is not None and to_at is not None and from_at >= to_at:
        raise HTTPException(status_code=422, detail="La fecha inicial debe ser anterior a la fecha final.")
    return [*([column >= from_at] if from_at is not None else []),
            *([column < to_at] if to_at is not None else [])]
