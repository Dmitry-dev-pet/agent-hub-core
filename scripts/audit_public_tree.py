from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".md", ".toml", ".json", ".yaml", ".yml"}
TOKEN_RE = re.compile(r"[A-Za-z0-9_.@+-]+")

# SHA-256 fingerprints of known instance-specific identifiers. Keeping only
# fingerprints lets CI reject accidental private-instance leakage without
# publishing the identifiers themselves in this public repository.
FORBIDDEN_TOKEN_HASHES = {
    "56fae122778684acbc850a10748e6871f099ff42b4bb36bf06cf80e3a3140985",
    "6263c07981770a319ee4c8772819c666a4b5bbcf92db10ab430d38fc6eb41191",
    "63b126e73ea9cb830f9c88e46f136df9ee1412a7a4c938325be12575af2d0a4b",
    "b7a815a5959aa1dcbf601cf56c7b7716201666ff74e6e3a0a59ef44bf4fc7609",
    "b8560104e2fd59feb5aac77d8b2b8fccc94ac2434a8ef63c0aef92a84c8d174c",
    "bd68ec0f2a605cfd874633be90b05445bef0bbab02a8626f36d4679a998f5f4c",
    "6605c844f0381f5b431a72b5eacd8458c7c14199003438fa5be1bb9ccae66567",
    "201950669774c86a35fd505156ab3e9658bbfd7c229c42fcf52eda3a19a9f04e",
    "13f367b6b44430e21d5a39ab293606bf077fe11f025c8e0de848204eefa58501",
    "06307eb298b7316587e727de1be5a190c92fede4546daf28531b3d10db2452bd",
    "1b7afbe53f5e49af91b06e15ab2bc1dc907d834cf2e3c745e63b3c5e2c664113",
    "d18d9b3e0ea16e07d4a2eb5ff881c37418da1b737c86d273797508989c3a9ce6",
    "cb090c27316c10cd68f15a4a98fef80e976be8cc299c6b674da662320251106b",
    "53ace7b91a7158ea65bd521277bb7a01aa7b6ac7632908579c9e27f40263f155",
    "12a4efd55aae3ef6d67ad3740ca1fc42ff6dac454f6a6a95cd99948f069b006c",
    "ad768546baab9f72668808da2ac695b435cc47c80ed37716fd7c425c2d09596e",
}

SECRET_PATTERNS = {
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"): "private-key marker",
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"): "GitHub PAT-like value",
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"): "GitHub token-like value",
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"): "API-key-like value",
}
FORBIDDEN_FILENAMES = {
    ".env",
    "credentials.json",
    "secrets.json",
    "id_rsa",
    "id_ed25519",
}


def fingerprint(token: str) -> str:
    return hashlib.sha256(token.casefold().encode("utf-8")).hexdigest()


def audit(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue

        relative = path.relative_to(root)
        if path.name in FORBIDDEN_FILENAMES:
            errors.append(f"forbidden credential-like file: {relative}")

        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != "LICENSE":
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        if any(
            fingerprint(token) in FORBIDDEN_TOKEN_HASHES
            for token in TOKEN_RE.findall(text)
        ):
            errors.append(
                f"{relative} contains an instance-specific identifier fingerprint"
            )

        for pattern, label in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{relative} contains {label}")

    return errors


def main() -> int:
    errors = audit()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        "OK: public tree contains no known instance-specific or secret-like material"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
