#!/usr/bin/env python3
"""Build and verify a content-addressed GitHub Pages deployment."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


ARTIFACTS = (
    "index.html",
    "ai-signals.js",
    "decision_matrix.json",
    "risk_score.json",
)


class VerificationError(RuntimeError):
    """Raised when the public Pages content does not match the deployment."""


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def build_manifest(public_dir: Path, commit: str) -> dict:
    artifacts = {}
    for name in ARTIFACTS:
        path = public_dir / name
        if not path.is_file():
            raise FileNotFoundError(path)
        artifacts[name] = sha256_bytes(path.read_bytes())

    manifest = {
        "schema_version": 1,
        "commit": commit,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": artifacts,
    }
    (public_dir / "deployment-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def fetch_bytes(url: str, timeout: float = 20) -> bytes:
    request = Request(
        url,
        headers={
            "Accept": "application/json,text/plain,*/*",
            "Cache-Control": "no-cache, no-store, max-age=0",
            "Pragma": "no-cache",
            "User-Agent": "investment-news-pages-verifier/1.0",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise VerificationError(f"HTTP {response.status}: {url}")
        return response.read()


def cache_busted_url(base_url: str, path: str, commit: str, attempt: int) -> str:
    root = base_url.rstrip("/") + "/"
    url = urljoin(root, path)
    token = f"{commit}-{attempt}-{time.time_ns()}"
    separator = "&" if urlparse(url).query else "?"
    return f"{url}{separator}verify={token}"


def verify_once(base_url: str, expected_commit: str, attempt: int = 1) -> dict:
    manifest_url = cache_busted_url(
        base_url, "deployment-manifest.json", expected_commit, attempt
    )
    try:
        manifest = json.loads(fetch_bytes(manifest_url).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"invalid deployment manifest: {exc}") from exc

    actual_commit = manifest.get("commit")
    if actual_commit != expected_commit:
        raise VerificationError(
            f"deployed commit {actual_commit!r} != expected {expected_commit!r}"
        )

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise VerificationError("deployment manifest has no artifact hashes")

    missing = sorted(set(ARTIFACTS) - set(artifacts))
    if missing:
        raise VerificationError(f"deployment manifest missing: {', '.join(missing)}")

    for name in ARTIFACTS:
        content = fetch_bytes(cache_busted_url(base_url, name, expected_commit, attempt))
        actual_hash = sha256_bytes(content)
        if actual_hash != artifacts[name]:
            raise VerificationError(
                f"deployed {name} hash {actual_hash} != manifest {artifacts[name]}"
            )

    return manifest


def verify_with_retry(
    base_url: str,
    expected_commit: str,
    attempts: int = 36,
    delay: float = 5,
) -> dict:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            manifest = verify_once(base_url, expected_commit, attempt)
            print(
                f"Pages verified: commit={expected_commit} "
                f"artifacts={len(manifest['artifacts'])} attempt={attempt}"
            )
            return manifest
        except Exception as exc:  # network and eventual-consistency failures are retryable
            last_error = exc
            print(f"Pages verification attempt {attempt}/{attempts} failed: {exc}")
            if attempt < attempts:
                time.sleep(delay)
    raise VerificationError(
        f"Pages did not converge to commit {expected_commit}: {last_error}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build")
    build.add_argument("--public-dir", type=Path, default=Path("public"))
    build.add_argument("--commit", required=True)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--page-url", required=True)
    verify.add_argument("--commit", required=True)
    verify.add_argument("--attempts", type=int, default=36)
    verify.add_argument("--delay", type=float, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "build":
        manifest = build_manifest(args.public_dir, args.commit)
        print(
            f"Deployment manifest built: commit={manifest['commit']} "
            f"artifacts={len(manifest['artifacts'])}"
        )
        return
    verify_with_retry(args.page_url, args.commit, args.attempts, args.delay)


if __name__ == "__main__":
    main()
