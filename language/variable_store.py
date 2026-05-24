from __future__ import annotations
import json
import os
import aiofiles
from typing import Any


class VariableStore:
    def __init__(self, path: str = "data/variables.json"):
        self.path = path
        self.data: dict[str, Any] = {}
        self._ensure_path()

    def _ensure_path(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def load(self) -> dict[str, Any]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {}
        return self.data

    async def load_async(self) -> dict[str, Any]:
        try:
            async with aiofiles.open(self.path, "r", encoding="utf-8") as f:
                content = await f.read()
                self.data = json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {}
        return self.data

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, default=str)

    async def save_async(self) -> None:
        async with aiofiles.open(self.path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(self.data, indent=2, default=str))

    def get(self, key: str, default: Any = None) -> Any:
        encoded = self._encode_key(key)
        return self.data.get(encoded, default)

    def set(self, key: str, value: Any) -> None:
        encoded = self._encode_key(key)
        self.data[encoded] = value

    def delete(self, key: str) -> bool:
        encoded = self._encode_key(key)
        if encoded in self.data:
            del self.data[encoded]
            return True
        return False

    def has(self, key: str) -> bool:
        encoded = self._encode_key(key)
        return encoded in self.data

    def clear(self) -> None:
        self.data.clear()

    def get_all(self) -> dict[str, Any]:
        return dict(self.data)

    def get_namespace(self, namespace: str) -> dict[str, Any]:
        prefix = self._encode_key(namespace)
        return {k: v for k, v in self.data.items() if k.startswith(prefix)}

    def _encode_key(self, key: str) -> str:
        return key.replace(".", "\\.").replace("$", "\\$").replace("{", "\\{").replace("}", "\\}")
