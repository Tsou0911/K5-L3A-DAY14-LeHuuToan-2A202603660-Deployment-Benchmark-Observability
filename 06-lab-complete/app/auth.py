from hmac import compare_digest

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from .config import settings


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(key: str | None = Security(api_key_header)) -> str:
    expected = settings.agent_api_key
    if not key or not expected or not compare_digest(key.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key
