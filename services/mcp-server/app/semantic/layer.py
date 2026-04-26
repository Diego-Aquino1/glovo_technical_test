import json
from pathlib import Path
from typing import Any


class SemanticLayer:
    def __init__(self) -> None:
        schema_path = Path(__file__).parent / "schema_semantic.json"
        with schema_path.open(encoding="utf-8") as f:
            raw = json.load(f)

        layer = raw.get("semantic_layer", {})
        self._version: str = layer.get("version", "unknown")
        self._policies: dict[str, Any] = layer.get("policies", {})

        self._tech_to_semantic: dict[str, dict] = {
            m["technical_name"]: m for m in layer.get("mappings", [])
        }
        self._semantic_to_tech: dict[str, dict] = {
            m["semantic_name"]: m for m in layer.get("mappings", [])
        }
        self._pii_fields: frozenset[str] = frozenset(
            m["technical_name"]
            for m in layer.get("mappings", [])
            if m.get("is_pii", False)
        )

    @property
    def version(self) -> str:
        return self._version

    @property
    def read_only_default(self) -> bool:
        return self._policies.get("read_only_default", True)

    @property
    def mask_pii(self) -> bool:
        return self._policies.get("mask_pii", False)

    def get_field_description(self, field_name: str) -> str | None:
        mapping = self._tech_to_semantic.get(field_name) or self._semantic_to_tech.get(field_name)
        return mapping.get("description") if mapping else None

    def get_semantic_name(self, technical_name: str) -> str:
        mapping = self._tech_to_semantic.get(technical_name)
        return mapping["semantic_name"] if mapping else technical_name

    def apply_pii_mask(self, value: str, field: str) -> str:
        if self.mask_pii and field in self._pii_fields:
            return "***MASKED***"
        return value

    def enrich_response(self, data: dict[str, Any]) -> dict[str, Any]:
        field_context: dict[str, dict] = {}

        for field_name in data:
            if field_name.startswith("_"):
                continue
            mapping = self._tech_to_semantic.get(field_name)
            if mapping:
                field_context[field_name] = {
                    "nombre_negocio": mapping["semantic_name"],
                    "descripcion": mapping["description"],
                }

        enriched = {**data, "_schema_version": self._version}
        if field_context:
            enriched["_field_context"] = field_context

        return enriched

    def assert_read_only(self, operation: str) -> None:
        if not self.read_only_default:
            return
        forbidden_keywords = {"INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER", "CREATE"}
        op_upper = operation.upper()
        for kw in forbidden_keywords:
            if kw in op_upper:
                raise PermissionError(
                    f"Operación '{kw}' bloqueada por política read_only_default del schema semántico v{self._version}."
                )


semantic_layer = SemanticLayer()
