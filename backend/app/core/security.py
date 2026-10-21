from datetime import datetime, timezone


def create_demo_token(user_id: str) -> str:
    """Create a deliberately simple demo token; replace with JWT in production."""
    return f"demo.{user_id}.{int(datetime.now(timezone.utc).timestamp())}"


def get_user_id_from_token(token: str | None) -> str:
    if not token or not token.startswith("demo."):
        return "demo-user"
    parts = token.split(".")
    return parts[1] if len(parts) > 1 else "demo-user"
