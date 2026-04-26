import re

_SKU_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9\-]{1,18}[A-Z0-9]$")

_DANGEROUS_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|EXEC|EXECUTE|UNION|SELECT\s+\*|--)\b",
    re.IGNORECASE,
)


def validate_sku(sku: str) -> str:
    if not isinstance(sku, str):
        raise ValueError(f"SKU debe ser una cadena de texto, recibido: {type(sku).__name__}.")

    normalized = sku.strip().upper()

    if not normalized:
        raise ValueError("SKU no puede estar vacío.")

    if len(normalized) > 20:
        raise ValueError(f"SKU demasiado largo ({len(normalized)} chars). Máximo 20.")

    _check_injection(normalized, field_name="sku")

    if not _SKU_PATTERN.match(normalized):
        raise ValueError(
            f"Formato de SKU inválido: '{normalized}'. "
            "Sólo se permiten letras mayúsculas, dígitos y guiones (longitud 3-20)."
        )

    return normalized


def validate_role(role: str) -> str:
    if not isinstance(role, str):
        raise ValueError("El rol debe ser una cadena de texto.")
    normalized = role.strip().lower()
    if not normalized:
        raise ValueError("El rol no puede estar vacío.")
    _check_injection(normalized, field_name="user_role")
    return normalized


def _check_injection(value: str, field_name: str) -> None:
    if _DANGEROUS_KEYWORDS.search(value):
        raise ValueError(
            f"Input sospechoso detectado en el campo '{field_name}'. "
            "El parámetro contiene palabras clave no permitidas."
        )
