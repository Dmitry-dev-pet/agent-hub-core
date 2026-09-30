from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".md", ".toml", ".json", ".yaml", ".yml"}
FORBIDDEN_LITERALS = {
    "coimbra",
    "jevspin",
    "ops-hub",
    "it-mentor",
    "rubik-physics-intern",
    "infra-access",
    "mac-access",
    "github-control",
    "repo_creator_token",
    "vercel_token",
    "typesafe_api_key",
    "cloudflare_api_token",
}
SECRET_PATTERNS = {
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"): "private-key marker",
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"): "GitHub PAT-like value",
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"): "GitHub token-like value",
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"): "API-key-like value",
}
FORBIDDEN_FILENAMES = {".env", "credentials.json", "secrets.json", "id_rsa", "id_ed25519"}


def audit(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path.name in FORBIDDEN_FILENAMES:
            errors.append(f"forbidden credential-like file: {path.relative_to(root)}")
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        folded = text.casefold()
        for literal in FORBIDDEN_LITERALS:
            if literal in folded:
                errors.append(
                    f"{path.relative_to(root)} contains instance-specific literal {literal!r}"
                )
        for pattern, label in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{path.relative_to(root)} contains {label}")
    return errors


def main() -> int:
    errors = audit()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK: public tree contains no known instance-specific or secret-like material")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
