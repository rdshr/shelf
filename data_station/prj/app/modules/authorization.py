from __future__ import annotations

from typing import Any

from ..config import AppConfig
from ..models import AuthorizationDecision


class AuthorizationInputParsingModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.config = app_config.section("l2_authorization_input_parsing")

    def parse(self, actor_id: str | None, actor_role: str | None, action: str, resource: str, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "actor_id": actor_id or str(self.config.get("default_actor_id", "anonymous")),
            "actor_role": actor_role or str(self.config.get("default_actor_role", "viewer")),
            "action": action,
            "resource": resource,
            "context": context,
        }


class AuthorizationDecisionGenerationModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.policies = {
            key: [str(item) for item in value]
            for key, value in app_config.section("l2_authorization_decision_generation").get("policies", {}).items()
        }

    def decide(self, parsed: dict[str, Any]) -> AuthorizationDecision:
        allowed_roles = self.policies.get(parsed["action"], [])
        if parsed["actor_role"] not in allowed_roles:
            return AuthorizationDecision(False, "role_not_allowed", "Actor role is not allowed for this action.", "unknown")
        return AuthorizationDecision(True, "allowed", "Authorization passed.", "unknown")


class AuthorizationScopeGovernanceModule:
    def __init__(self, app_config: AppConfig) -> None:
        config = app_config.section("l2_authorization_scope_governance")
        self.resource_scopes = {key: [str(item) for item in value] for key, value in config.get("resource_scopes", {}).items()}
        self.role_scopes = {key: [str(item) for item in value] for key, value in config.get("role_scopes", {}).items()}
        self.default_scope = str(config.get("default_scope", "internal"))

    def apply(self, decision: AuthorizationDecision, parsed: dict[str, Any]) -> AuthorizationDecision:
        if not decision.allowed:
            return decision
        requested_scope = str(parsed["context"].get("scope", self.default_scope))
        resource_scopes = self.resource_scopes.get(parsed["resource"], [self.default_scope])
        role_scopes = self.role_scopes.get(parsed["actor_role"], [self.default_scope])
        if requested_scope not in resource_scopes or requested_scope not in role_scopes:
            return AuthorizationDecision(False, "scope_not_allowed", "Requested scope is not allowed.", requested_scope)
        return AuthorizationDecision(True, "allowed", "Authorization passed.", requested_scope)


class AuthorizationGovernanceModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.config = app_config.section("l1_authorization_governance")
        self.input_parsing = AuthorizationInputParsingModule(app_config)
        self.decision_generation = AuthorizationDecisionGenerationModule(app_config)
        self.scope_governance = AuthorizationScopeGovernanceModule(app_config)

    def authorize(self, actor_id: str | None, actor_role: str | None, action: str, resource: str, context: dict[str, Any]) -> AuthorizationDecision:
        if self.config.get("deny_if_actor_missing", True) and not actor_id:
            return AuthorizationDecision(False, "missing_actor", "Actor id is required.", "unknown")
        parsed = self.input_parsing.parse(actor_id, actor_role, action, resource, context)
        decision = self.decision_generation.decide(parsed)
        return self.scope_governance.apply(decision, parsed)
