from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import yaml


LEVELS = {"L0", "L1", "L2", "L3", "L4", "L5"}
OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
REPO_RE = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9_.-]{1,100}$"
)
SENSITIVE_VALUE_KEYS = {
    "value",
    "token",
    "password",
    "secret",
    "private_key",
    "api_key",
}
OPTIONAL_CREDENTIAL_STATUSES = {"optional", "optional_dormant", "disabled"}
CANONICAL_INSTANCE_CONFIG = "truthrail.yaml"
LEGACY_INSTANCE_CONFIG = "agent-hub.yaml"


class InstanceValidationError(ValueError):
    """Raised when an Agent Hub instance configuration is invalid."""


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise InstanceValidationError(f"{path}: cannot read YAML: {exc}") from exc
    if not isinstance(payload, dict):
        raise InstanceValidationError(f"{path}: top level must be a mapping")
    return payload


def _load_instance_config(root: Path) -> tuple[Path, dict[str, Any]]:
    canonical_path = root / CANONICAL_INSTANCE_CONFIG
    legacy_path = root / LEGACY_INSTANCE_CONFIG

    if canonical_path.is_file():
        canonical = _load_yaml(canonical_path)
        if legacy_path.is_file():
            legacy = _load_yaml(legacy_path)
            if legacy != canonical:
                raise InstanceValidationError(
                    f"{canonical_path} and {legacy_path} differ; refusing split-brain instance config"
                )
        return canonical_path, canonical

    if legacy_path.is_file():
        return legacy_path, _load_yaml(legacy_path)

    raise InstanceValidationError(
        f"{canonical_path}: missing (legacy {LEGACY_INSTANCE_CONFIG} is also absent)"
    )


def _relative_path(root: Path, raw: Any, label: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise InstanceValidationError(f"{label} must be a non-empty relative path")
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise InstanceValidationError(f"{label} must stay inside the instance directory")
    resolved_root = root.resolve()
    resolved = (root / path).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise InstanceValidationError(f"{label} escapes the instance directory")
    return resolved


def _validate_repo(repo: Any, label: str) -> str:
    if not isinstance(repo, str) or not REPO_RE.fullmatch(repo):
        raise InstanceValidationError(f"{label} must be owner/repository")
    return repo


def _scan_sensitive_values(value: Any, label: str = "credentials") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).casefold()
            if normalized in SENSITIVE_VALUE_KEYS:
                raise InstanceValidationError(
                    f"{label}: secret-value field {key!r} is not allowed"
                )
            _scan_sensitive_values(nested, f"{label}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _scan_sensitive_values(nested, f"{label}[{index}]")


def _dump_yaml(payload: dict[str, Any]) -> str:
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def _project_id(repo: str, used: set[str]) -> str:
    candidate = repo.split("/", 1)[1].lower()
    candidate = re.sub(r"[^a-z0-9._-]+", "-", candidate).strip("-")
    candidate = candidate or "project"
    base = candidate
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def init_instance(
    target: str | Path,
    *,
    owner: str,
    projects: list[str] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    if not OWNER_RE.fullmatch(owner):
        raise InstanceValidationError(
            "owner must look like a GitHub user or organization handle"
        )

    project_names = projects or []
    for index, repo in enumerate(project_names):
        _validate_repo(repo, f"projects[{index}]")

    root = Path(target)
    if root.exists() and any(root.iterdir()) and not force:
        raise InstanceValidationError(
            f"{root}: directory is not empty; pass --force to overwrite managed files"
        )
    root.mkdir(parents=True, exist_ok=True)
    (root / "context").mkdir(parents=True, exist_ok=True)

    used_ids: set[str] = set()
    routes = []
    for repo in project_names:
        project_id = _project_id(repo, used_ids)
        routes.append(
            {
                "id": project_id,
                "repo": repo,
                "aliases": [project_id, repo],
            }
        )

    hub = {
        "version": 1,
        "inventory": {"provider": "github", "owner": owner},
        "projects": "projects.yaml",
        "capabilities": "capabilities.yaml",
        "credentials": "credentials.yaml",
        "context_dir": "context",
    }
    project_config = {"version": 1, "routing": routes}
    capabilities = {
        "version": 1,
        "capabilities": {
            "github-public": {
                "kind": "public_api",
                "provider": "github",
                "execution_levels": ["L0"],
                "authentication": "none",
            },
            "github": {
                "kind": "connected_runtime",
                "provider": "github",
                "execution_levels": ["L0", "L1"],
                "authentication": "ambient_optional",
            },
            "github-actions": {
                "kind": "ephemeral_runtime",
                "provider": "github",
                "execution_levels": ["L3"],
                "authentication": "provider_managed",
            },
        },
    }
    credentials = {
        "version": 1,
        "policy": {"store_values_here": False},
        "credential_routes": {},
    }

    managed = {
        CANONICAL_INSTANCE_CONFIG: hub,
        LEGACY_INSTANCE_CONFIG: hub,
        "projects.yaml": project_config,
        "capabilities.yaml": capabilities,
        "credentials.yaml": credentials,
    }
    for filename, payload in managed.items():
        (root / filename).write_text(_dump_yaml(payload), encoding="utf-8")

    (root / "context" / "README.md").write_text(
        "# Durable context\n\n"
        "Store durable goals, decisions, constraints, and authoritative pointers here.\n"
        "Do not store secret values or live branch/deployment/runtime state.\n",
        encoding="utf-8",
    )
    return validate_instance(root)


def validate_instance(target: str | Path) -> dict[str, Any]:
    root = Path(target)
    hub_path, hub = _load_instance_config(root)
    hub_label = hub_path.name

    if hub.get("version") != 1:
        raise InstanceValidationError(f"{hub_label}: version must be 1")

    inventory = hub.get("inventory")
    if not isinstance(inventory, dict) or inventory.get("provider") != "github":
        raise InstanceValidationError(
            f"{hub_label}: inventory.provider must be github"
        )
    owner = inventory.get("owner")
    if not isinstance(owner, str) or not OWNER_RE.fullmatch(owner):
        raise InstanceValidationError(
            f"{hub_label}: inventory.owner must look like a GitHub handle"
        )

    projects_path = _relative_path(root, hub.get("projects"), "projects")
    capabilities_path = _relative_path(
        root, hub.get("capabilities"), "capabilities"
    )
    credentials_path = _relative_path(
        root, hub.get("credentials"), "credentials"
    )
    context_dir = _relative_path(root, hub.get("context_dir"), "context_dir")

    for path in (projects_path, capabilities_path, credentials_path):
        if not path.is_file():
            raise InstanceValidationError(f"{path}: missing")
    if not context_dir.is_dir():
        raise InstanceValidationError(f"{context_dir}: missing directory")

    projects = _load_yaml(projects_path)
    if projects.get("version") != 1:
        raise InstanceValidationError("projects.yaml: version must be 1")
    routing = projects.get("routing")
    if not isinstance(routing, list):
        raise InstanceValidationError("projects.yaml: routing must be a list")

    ids: set[str] = set()
    aliases: dict[str, str] = {}
    repositories: list[str] = []
    for index, route in enumerate(routing):
        if not isinstance(route, dict):
            raise InstanceValidationError(
                f"projects.yaml: routing[{index}] must be a mapping"
            )
        project_id = route.get("id")
        if not isinstance(project_id, str) or not project_id.strip():
            raise InstanceValidationError(
                f"projects.yaml: routing[{index}].id must be non-empty"
            )
        if project_id in ids:
            raise InstanceValidationError(
                f"projects.yaml: duplicate project id {project_id!r}"
            )
        ids.add(project_id)

        repo = _validate_repo(
            route.get("repo"), f"projects.yaml: routing[{index}].repo"
        )
        repositories.append(repo)

        route_aliases = route.get("aliases", [])
        if not isinstance(route_aliases, list) or any(
            not isinstance(alias, str) or not alias.strip()
            for alias in route_aliases
        ):
            raise InstanceValidationError(
                f"projects.yaml: routing[{index}].aliases must be strings"
            )
        for alias in [project_id, *route_aliases]:
            key = alias.casefold()
            previous = aliases.get(key)
            if previous is not None and previous != project_id:
                raise InstanceValidationError(
                    f"projects.yaml: alias {alias!r} maps to both "
                    f"{previous!r} and {project_id!r}"
                )
            aliases[key] = project_id

    credentials = _load_yaml(credentials_path)
    if credentials.get("version") != 1:
        raise InstanceValidationError("credentials.yaml: version must be 1")
    policy = credentials.get("policy")
    if not isinstance(policy, dict) or policy.get("store_values_here") is not False:
        raise InstanceValidationError(
            "credentials.yaml: policy.store_values_here must be false"
        )
    credential_routes = credentials.get("credential_routes")
    if not isinstance(credential_routes, dict):
        raise InstanceValidationError(
            "credentials.yaml: credential_routes must be a mapping"
        )
    _scan_sensitive_values(credential_routes)
    for name, route in credential_routes.items():
        if not isinstance(name, str) or not name.strip():
            raise InstanceValidationError(
                "credentials.yaml: credential route names must be non-empty"
            )
        if not isinstance(route, dict):
            raise InstanceValidationError(
                f"credentials.yaml: {name} route must be a mapping"
            )
        if route.get("value_access") != "forbidden":
            raise InstanceValidationError(
                f"credentials.yaml: {name}.value_access must be forbidden"
            )

    capabilities = _load_yaml(capabilities_path)
    if capabilities.get("version") != 1:
        raise InstanceValidationError("capabilities.yaml: version must be 1")
    capability_map = capabilities.get("capabilities")
    if not isinstance(capability_map, dict) or not capability_map:
        raise InstanceValidationError(
            "capabilities.yaml: capabilities must be a non-empty mapping"
        )

    for name, capability in capability_map.items():
        if not isinstance(capability, dict):
            raise InstanceValidationError(
                f"capabilities.yaml: {name} must be a mapping"
            )
        levels = capability.get("execution_levels")
        if (
            not isinstance(levels, list)
            or not levels
            or any(level not in LEVELS for level in levels)
        ):
            raise InstanceValidationError(
                f"capabilities.yaml: {name}.execution_levels are invalid"
            )
        if capability.get("kind") == "reviewed_control_plane":
            contract = capability.get("operations_contract")
            if not isinstance(contract, dict):
                raise InstanceValidationError(
                    f"capabilities.yaml: {name} requires operations_contract"
                )
            if contract.get("provider") != "github":
                raise InstanceValidationError(
                    f"capabilities.yaml: {name} contract provider must be github"
                )
            _validate_repo(
                contract.get("repo"),
                f"capabilities.yaml: {name}.operations_contract.repo",
            )
            contract_path = contract.get("path")
            if (
                not isinstance(contract_path, str)
                or not contract_path.strip()
                or Path(contract_path).is_absolute()
                or ".." in Path(contract_path).parts
            ):
                raise InstanceValidationError(
                    f"capabilities.yaml: {name} contract path must be relative"
                )

        credential_ref = capability.get("credential_ref")
        if credential_ref is not None and credential_ref not in credential_routes:
            raise InstanceValidationError(
                f"capabilities.yaml: {name}.credential_ref has no credential route"
            )

    required_credentials = sorted(
        name
        for name, route in credential_routes.items()
        if route.get("status") not in OPTIONAL_CREDENTIAL_STATUSES
    )
    return {
        "ok": True,
        "root": str(root),
        "instance_config": hub_path.name,
        "legacy_config_present": (root / LEGACY_INSTANCE_CONFIG).is_file(),
        "owner": owner,
        "projects": len(routing),
        "repositories": repositories,
        "capabilities": len(capability_map),
        "credential_routes": len(credential_routes),
        "custom_credentials_required": len(required_credentials),
        "required_credentials": required_credentials,
        "credential_mode": (
            "zero-custom-secret"
            if not required_credentials
            else "capability-credentials-declared"
        ),
    }


def _github_public_get(url: str, timeout: float) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "agent-hub-core-doctor/0.1",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("GitHub returned a non-object response")
    return data


def doctor_instance(
    target: str | Path,
    *,
    network: bool = True,
    timeout: float = 5.0,
) -> dict[str, Any]:
    summary = validate_instance(target)
    result: dict[str, Any] = {
        **summary,
        "network_mode": "public-unauthenticated" if network else "offline",
        "github_public_api": "skipped" if not network else "unknown",
        "project_checks": [],
    }
    if not network:
        return result

    try:
        _github_public_get("https://api.github.com/rate_limit", timeout)
        result["github_public_api"] = "reachable"
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        result["github_public_api"] = f"unreachable: {exc}"
        result["ok"] = False
        return result

    checks = []
    for repo in summary["repositories"]:
        encoded = quote(repo, safe="/")
        try:
            payload = _github_public_get(
                f"https://api.github.com/repos/{encoded}", timeout
            )
            checks.append(
                {
                    "repo": repo,
                    "publicly_reachable": True,
                    "default_branch": payload.get("default_branch"),
                }
            )
        except HTTPError as exc:
            checks.append(
                {
                    "repo": repo,
                    "publicly_reachable": False,
                    "error": f"HTTP {exc.code}",
                }
            )
            result["ok"] = False
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            checks.append(
                {
                    "repo": repo,
                    "publicly_reachable": False,
                    "error": str(exc),
                }
            )
            result["ok"] = False
    result["project_checks"] = checks
    return result


def bootstrap_acceptance() -> dict[str, Any]:
    from .conformance import run_scenario

    projects = [f"example-org/public-project-{index}" for index in range(1, 6)]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / ".agent-hub"
        init_summary = init_instance(
            root,
            owner="example-org",
            projects=projects,
        )
        doctor = doctor_instance(root, network=False)
        conformance = run_scenario()

    result = {
        "instance_initialized": init_summary["ok"],
        "configured_repositories": init_summary["projects"],
        "custom_credentials_required": doctor["custom_credentials_required"],
        "credential_mode": doctor["credential_mode"],
        "doctor_ok": doctor["ok"],
        "doctor_network_mode": doctor["network_mode"],
        "protocol_conformance_verified": (
            conformance["verification_status"] == "verified"
            and conformance["fresh_recovery_matches"] is True
        ),
    }
    expected = {
        "instance_initialized": True,
        "configured_repositories": 5,
        "custom_credentials_required": 0,
        "credential_mode": "zero-custom-secret",
        "doctor_ok": True,
        "doctor_network_mode": "offline",
        "protocol_conformance_verified": True,
    }
    if result != expected:
        raise AssertionError(f"bootstrap acceptance mismatch: {result!r}")
    return result
