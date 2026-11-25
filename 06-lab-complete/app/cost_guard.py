from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from .config import settings
from .redis_client import r


PRICE_INPUT_PER_1K = 0.00015
PRICE_OUTPUT_PER_1K = 0.0006


def check_budget() -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    key = f"lab14:cost:{today}"
    if float(r.get(key) or 0) >= settings.daily_budget_usd:
        raise HTTPException(status_code=402, detail="Daily budget exhausted")
    return key


def record_cost(key: str, input_tokens: int, output_tokens: int) -> float:
    cost = (input_tokens * PRICE_INPUT_PER_1K + output_tokens * PRICE_OUTPUT_PER_1K) / 1000
    expire_at = datetime.fromisoformat(key.rsplit(":", 1)[1]).replace(
        tzinfo=timezone.utc
    ) + timedelta(days=2)
    with r.pipeline() as transaction:
        transaction.incrbyfloat(key, cost)
        transaction.expireat(key, expire_at)
        transaction.execute()
    return cost
