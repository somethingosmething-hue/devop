from __future__ import annotations
from language.runtime import Runtime, Scope
from typing import Any, Optional


class ComponentHandler:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.active_components: dict[str, Any] = {}

    def register_component(self, component_id: str, data: Any) -> None:
        self.active_components[component_id] = data

    def get_component(self, component_id: str) -> Any:
        return self.active_components.get(component_id)

    def remove_component(self, component_id: str) -> None:
        self.active_components.pop(component_id, None)

    def handle_modal_values(self, interaction: Any, runtime: Runtime) -> dict[str, Any]:
        values = {}
        try:
            rows = interaction.data.get("components", []) if hasattr(interaction, 'data') else []
            for row in rows:
                for component in row.get("components", []):
                    cid = component.get("custom_id", "")
                    if component.get("type") == 4:
                        values[cid] = component.get("value", "")
            return values
        except (AttributeError, KeyError, TypeError):
            return {}
