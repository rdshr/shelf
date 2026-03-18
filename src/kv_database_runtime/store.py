from __future__ import annotations

import ast
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WalRecord:
    operation: str
    key: str
    value: Any

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "key": self.key,
            "value": self.value,
        }


@dataclass(frozen=True)
class MemoryKvDatabaseConfig:
    allowed_operations: tuple[str, ...]
    read_operation: str
    write_operations: tuple[str, ...]
    missing_key_policy: str
    key_python_type: str
    value_python_type: str
    value_serialization: str
    wal_directory: Path
    wal_filename: str
    create_parent_on_boot: bool
    record_format: str
    field_order: tuple[str, ...]
    line_delimiter: str
    replay_strategy: str

    @property
    def wal_path(self) -> Path:
        return self.wal_directory / self.wal_filename


class WriteAheadLog:
    def __init__(self, config: MemoryKvDatabaseConfig) -> None:
        self._config = config
        if config.create_parent_on_boot:
            config.wal_directory.mkdir(parents=True, exist_ok=True)

    def append(self, record: WalRecord) -> None:
        payload = {
            "operation": record.operation,
            "key": record.key,
            "value_repr": self._encode_value(record.value),
        }
        line = json.dumps(payload, ensure_ascii=False, sort_keys=True) + self._config.line_delimiter
        with self._config.wal_path.open("a", encoding="utf-8") as handle:
            handle.write(line)

    def read_records(self) -> list[WalRecord]:
        if not self._config.wal_path.exists():
            return []
        records: list[WalRecord] = []
        with self._config.wal_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                text = raw_line.strip()
                if not text:
                    continue
                payload = json.loads(text)
                records.append(
                    WalRecord(
                        operation=str(payload["operation"]),
                        key=str(payload["key"]),
                        value=self._decode_value(str(payload.get("value_repr", "None"))),
                    )
                )
        return records

    def _encode_value(self, value: Any) -> str:
        if self._config.value_serialization == "repr":
            return repr(value)
        if self._config.value_serialization == "json":
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        raise ValueError(f"unsupported value serialization: {self._config.value_serialization}")

    def _decode_value(self, payload: str) -> Any:
        if self._config.value_serialization == "repr":
            try:
                return ast.literal_eval(payload)
            except (SyntaxError, ValueError):
                return payload
        if self._config.value_serialization == "json":
            return json.loads(payload)
        raise ValueError(f"unsupported value serialization: {self._config.value_serialization}")


class MemoryKvDatabase:
    def __init__(self, config: MemoryKvDatabaseConfig, wal: WriteAheadLog | None = None) -> None:
        self._config = config
        self._wal = wal or WriteAheadLog(config)
        self._store: dict[str, Any] = {}

    @classmethod
    def from_config(cls, config: MemoryKvDatabaseConfig) -> "MemoryKvDatabase":
        database = cls(config=config)
        database.recover()
        return database

    def put(self, key: str, value: Any) -> None:
        self._assert_operation_allowed("put")
        self._assert_key(key)
        self._wal.append(WalRecord(operation="put", key=key, value=value))
        self._store[key] = value

    def get(self, key: str) -> Any:
        self._assert_operation_allowed(self._config.read_operation)
        self._assert_key(key)
        if key not in self._store:
            self._raise_missing_key(key)
        return self._store[key]

    def delete(self, key: str) -> Any:
        self._assert_operation_allowed("delete")
        self._assert_key(key)
        if key not in self._store:
            self._raise_missing_key(key)
        value = self._store[key]
        self._wal.append(WalRecord(operation="delete", key=key, value=value))
        del self._store[key]
        return value

    def recover(self) -> dict[str, Any]:
        recovered: dict[str, Any] = {}
        for record in self._wal.read_records():
            if record.operation == "put":
                recovered[record.key] = record.value
            elif record.operation == "delete":
                recovered.pop(record.key, None)
            else:
                raise ValueError(f"unsupported WAL operation during recovery: {record.operation}")
        self._store = recovered
        return dict(self._store)

    def snapshot(self) -> dict[str, Any]:
        return dict(self._store)

    def _assert_operation_allowed(self, operation: str) -> None:
        if operation not in self._config.allowed_operations:
            raise ValueError(f"unsupported operation: {operation}")

    def _assert_key(self, key: str) -> None:
        if self._config.key_python_type != "str":
            raise ValueError(f"unsupported key type contract: {self._config.key_python_type}")
        if not isinstance(key, str):
            raise TypeError("KV database keys must be str")

    def _raise_missing_key(self, key: str) -> None:
        if self._config.missing_key_policy == "raise_key_error":
            raise KeyError(key)
        raise ValueError(f"unsupported missing key policy: {self._config.missing_key_policy}")
