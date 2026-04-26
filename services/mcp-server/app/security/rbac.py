from typing import Final

ROLE_PERMISSIONS: Final[dict[str, set[str]]] = {
    "viewer": {
        "get_article_info",
        "get_stock_availability",
        "get_pending_replenishments",
    },
    "manager": {
        "get_article_info",
        "get_stock_availability",
        "get_pending_replenishments",
    },
    "admin": {
        "get_article_info",
        "get_stock_availability",
        "get_pending_replenishments",
    },
}

DEFAULT_ROLE: Final[str] = "viewer"


def check_permission(role: str, tool_name: str) -> None:
    allowed = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS[DEFAULT_ROLE])
    if tool_name not in allowed:
        raise PermissionError(
            f"El rol '{role}' no tiene permiso para ejecutar la tool '{tool_name}'."
        )
