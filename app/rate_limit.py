from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _api_key_or_ip(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_api_key_or_ip)
