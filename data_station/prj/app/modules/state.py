from __future__ import annotations

from typing import Any

from ..config import AppConfig
from ..models import DocumentRecord


class StateRegistrationInterfaceModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.config = app_config.section("l2_state_registration")

    def register(self, document: DocumentRecord, version_start: int) -> tuple[str, int]:
        state = str(self.config.get("initial_state", "accepted"))
        return state, version_start


class StateTransitionControlModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.allowed_transitions = {
            key: [str(item) for item in value]
            for key, value in app_config.section("l2_state_transition_control").get("allowed_transitions", {}).items()
        }

    def validate(self, current_state: str, target_state: str) -> tuple[bool, str]:
        allowed = self.allowed_transitions.get(current_state, [])
        if target_state not in allowed:
            return False, f"Transition from {current_state} to {target_state} is not allowed."
        return True, "state transition allowed"


class VersionIdempotencyManagementModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.config = app_config.section("l2_version_idempotency")

    def is_duplicate(self, existing: DocumentRecord | None) -> bool:
        return bool(self.config.get("enable_idempotency", True) and existing is not None)

    def next_version(self, document: DocumentRecord) -> int:
        if not self.config.get("increment_on_transition", True):
            return document.version
        return document.version + 1


class StateManagementModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.config = app_config.section("l1_state_management")
        self.registration = StateRegistrationInterfaceModule(app_config)
        self.transition_control = StateTransitionControlModule(app_config)
        self.versioning = VersionIdempotencyManagementModule(app_config)

    def register_initial(self, document: DocumentRecord, existing: DocumentRecord | None) -> tuple[bool, DocumentRecord]:
        if self.versioning.is_duplicate(existing):
            return True, existing
        version_start = int(self.config.get("version_start", 1))
        state, version = self.registration.register(document, version_start)
        document.state = state
        document.version = version
        return False, document

    def transition(self, document: DocumentRecord, target_state: str) -> tuple[bool, str]:
        allowed, message = self.transition_control.validate(document.state, target_state)
        if not allowed:
            return False, message
        document.state = target_state
        document.version = self.versioning.next_version(document)
        return True, message
