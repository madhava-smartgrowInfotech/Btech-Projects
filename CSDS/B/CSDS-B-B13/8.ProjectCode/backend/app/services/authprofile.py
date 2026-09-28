"""Resolve auth profiles into concrete tokens/headers for two test users."""
import httpx


class AuthContext:
    def __init__(self, header_name: str, scheme: str,
                 token_a: str | None, token_b: str | None,
                 user_a_id=None, user_b_id=None):
        self.header_name = header_name or "Authorization"
        self.scheme = scheme or "Bearer"
        self.token_a = token_a
        self.token_b = token_b
        self.user_a_id = user_a_id
        self.user_b_id = user_b_id

    def headers(self, which: str = "a") -> dict:
        token = self.token_a if which == "a" else self.token_b
        if not token:
            return {}
        value = f"{self.scheme} {token}".strip() if self.scheme else token
        return {self.header_name: value}


async def _login(client: httpx.AsyncClient, base_url: str, auth: dict, user: dict):
    path = auth.get("login_path", "/login")
    payload = {
        auth.get("username_field", "username"): user.get("username"),
        auth.get("password_field", "password"): user.get("password"),
    }
    try:
        resp = await client.post(base_url.rstrip("/") + path, json=payload, timeout=15)
    except httpx.HTTPError:
        return None, None
    if resp.status_code >= 400:
        return None, None
    try:
        data = resp.json()
    except ValueError:
        return None, None
    token = data.get(auth.get("token_field", "token"))
    user_id = data.get("user_id")
    return token, user_id


async def resolve_auth(base_url: str, auth: dict) -> AuthContext:
    """auth can be a login flow or pre-supplied tokens."""
    header_name = auth.get("header_name", "Authorization")
    scheme = auth.get("scheme", "Bearer")

    if auth.get("type") == "tokens":
        return AuthContext(header_name, scheme,
                           auth.get("token_a"), auth.get("token_b"))

    if auth.get("type") == "login":
        async with httpx.AsyncClient() as client:
            ta, ua = await _login(client, base_url, auth, auth.get("user_a", {}))
            tb, ub = await _login(client, base_url, auth, auth.get("user_b", {}))
        return AuthContext(header_name, scheme, ta, tb, ua, ub)

    # No auth configured.
    return AuthContext(header_name, scheme, None, None)
