#!/usr/bin/env python3
"""Shared helpers for the auto-commit-pr skill.

All git calls inject ``-c user.name=underfituu -c user.email=hzhucong@163.com``
so that the global git config is **never** mutated.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS_DIR.parent
ROOT = SKILL_DIR.parents[2]  # vllm-ascend-workspace/

PROGRESS_SENTINEL = "__VAWS_AUTO_COMMIT_PR_PROGRESS__="

# ---------------------------------------------------------------------------
# Fixed identity — never touch global git config
# ---------------------------------------------------------------------------
GIT_USER_NAME = "underfituu"
GIT_USER_EMAIL = "hzhucong@163.com"

# ---------------------------------------------------------------------------
# Repository metadata
# ---------------------------------------------------------------------------
REPOS: dict[str, dict[str, Any]] = {
    "vllm": {
        "path": ROOT / "vllm",
        "origin_url": "https://github.com/underfituu/vllm.git",
        "upstream_url": "https://github.com/vllm-project/vllm.git",
        "upstream_remote": None,  # vllm/ has no upstream remote by default
        "upstream_branch": "main",
        "github_upstream": "vllm-project/vllm",
        "github_fork_owner": "underfituu",
    },
    "vllm-ascend": {
        "path": ROOT / "vllm-ascend",
        "origin_url": "https://github.com/underfituu/vllm-ascend.git",
        "upstream_url": "https://github.com/vllm-project/vllm-ascend.git",
        "upstream_remote": "upstream",
        "upstream_branch": "main",
        "github_upstream": "vllm-project/vllm-ascend",
        "github_fork_owner": "underfituu",
    },
}

# Temporary remote name added to vllm/ for rebase (no permanent upstream)
TMP_UPSTREAM_REMOTE = "_upstream_tmp"


# ───────────────────────────────────────────────────────────────────────────
# I/O helpers
# ───────────────────────────────────────────────────────────────────────────
def emit_progress(phase: str, message: str, **extra: Any) -> None:
    """Write a progress line to *stderr* so the agent can stream status."""
    payload = {"phase": phase, "message": message, **extra}
    print(f"{PROGRESS_SENTINEL}{json.dumps(payload)}", file=sys.stderr, flush=True)


def print_json(data: Any) -> None:
    """Write final JSON result to *stdout*."""
    print(json.dumps(data, indent=2, default=str), flush=True)


def die(message: str, code: int = 1) -> None:
    print(json.dumps({"error": message}), file=sys.stderr, flush=True)
    sys.exit(code)


# ───────────────────────────────────────────────────────────────────────────
# Git wrapper
# ───────────────────────────────────────────────────────────────────────────
def git(
    args: list[str],
    *,
    cwd: pathlib.Path,
    check: bool = True,
    capture: bool = True,
    identity: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a git command with the fixed identity injected.

    Parameters
    ----------
    args:
        Git sub-command and arguments, e.g. ``["status", "--porcelain"]``.
    cwd:
        Working directory (the repo root).
    check:
        If *True*, raise on non-zero exit.
    capture:
        If *True*, capture stdout/stderr.
    identity:
        If *True* (default), prepend ``-c user.name=… -c user.email=…``.
    """
    cmd = ["git"]
    if identity:
        cmd += [
            "-c", f"user.name={GIT_USER_NAME}",
            "-c", f"user.email={GIT_USER_EMAIL}",
        ]
    cmd += args
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        check=check,
        text=True,
        capture_output=capture,
    )


# ───────────────────────────────────────────────────────────────────────────
# Repo status helpers
# ───────────────────────────────────────────────────────────────────────────
def is_detached_head(repo: pathlib.Path) -> bool:
    r = git(["symbolic-ref", "-q", "HEAD"], cwd=repo, check=False)
    return r.returncode != 0


def current_branch(repo: pathlib.Path) -> Optional[str]:
    """Return the current branch name, or *None* if HEAD is detached."""
    r = git(["symbolic-ref", "--short", "HEAD"], cwd=repo, check=False, identity=False)
    if r.returncode != 0:
        return None
    return r.stdout.strip()


def head_sha(repo: pathlib.Path, short: bool = True) -> str:
    flag = ["--short"] if short else []
    r = git(["rev-parse", *flag, "HEAD"], cwd=repo, identity=False)
    return r.stdout.strip()


def get_dirty_files(repo: pathlib.Path) -> list[str]:
    """Return list of modified/untracked file paths from ``git status --porcelain``."""
    r = git(["status", "--porcelain"], cwd=repo, identity=False)
    files: list[str] = []
    for line in r.stdout.splitlines():
        if len(line) > 3:
            files.append(line[3:].strip())
    return files


def branch_exists(repo: pathlib.Path, branch: str) -> bool:
    r = git(["rev-parse", "--verify", f"refs/heads/{branch}"], cwd=repo, check=False, identity=False)
    return r.returncode == 0


def remote_exists(repo: pathlib.Path, remote: str) -> bool:
    r = git(["remote"], cwd=repo, identity=False)
    return remote in r.stdout.split()


def get_repo_status(repo: pathlib.Path) -> dict[str, Any]:
    """Collect a snapshot of the repository state."""
    detached = is_detached_head(repo)
    branch = current_branch(repo)
    sha = head_sha(repo)
    dirty = get_dirty_files(repo)
    return {
        "path": str(repo),
        "detached_head": detached,
        "current_branch": branch,
        "head_sha": sha,
        "dirty": len(dirty) > 0,
        "dirty_count": len(dirty),
        "dirty_files": dirty,
    }


def get_upstream_ref(repo_name: str, repo_path: pathlib.Path) -> Optional[str]:
    """Return the local ref string that points to upstream main.

    For vllm-ascend/ this is ``upstream/main``.
    For vllm/ (no upstream remote) we check for the temp remote; if absent
    we return *None* — the caller must fetch first.
    """
    meta = REPOS[repo_name]
    upstream_remote = meta["upstream_remote"]
    if upstream_remote is None:
        # vllm/ — check if temp remote exists
        if remote_exists(repo_path, TMP_UPSTREAM_REMOTE):
            return f"{TMP_UPSTREAM_REMOTE}/{meta['upstream_branch']}"
        return None
    return f"{upstream_remote}/{meta['upstream_branch']}"


def ensure_upstream_fetched(repo_name: str, repo_path: pathlib.Path) -> str:
    """Ensure that the upstream main is fetchable and return the ref.

    For vllm/ (no upstream remote), adds ``_upstream_tmp`` remote if needed.
    """
    meta = REPOS[repo_name]
    upstream_remote = meta["upstream_remote"]
    branch = meta["upstream_branch"]

    if upstream_remote is None:
        # vllm/ — add temporary remote if missing
        if not remote_exists(repo_path, TMP_UPSTREAM_REMOTE):
            emit_progress("rebase", f"adding temporary remote {TMP_UPSTREAM_REMOTE}")
            git(["remote", "add", TMP_UPSTREAM_REMOTE, meta["upstream_url"]], cwd=repo_path, identity=False)
        emit_progress("rebase", f"fetching {TMP_UPSTREAM_REMOTE}/{branch}")
        git(["fetch", TMP_UPSTREAM_REMOTE, branch], cwd=repo_path, identity=False)
        return f"{TMP_UPSTREAM_REMOTE}/{branch}"
    else:
        emit_progress("rebase", f"fetching {upstream_remote}/{branch}")
        git(["fetch", upstream_remote, branch], cwd=repo_path, identity=False)
        return f"{upstream_remote}/{branch}"


def get_commits_since(repo: pathlib.Path, base_ref: str) -> list[dict[str, str]]:
    """Return list of {sha, subject} for commits since *base_ref*."""
    r = git(
        ["log", f"{base_ref}..HEAD", "--oneline", "--no-decorate"],
        cwd=repo,
        check=False,
        identity=False,
    )
    commits = []
    for line in r.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split(" ", 1)
        commits.append({"sha": parts[0], "subject": parts[1] if len(parts) > 1 else ""})
    return commits


def get_diff_stat(repo: pathlib.Path, base_ref: str) -> str:
    """Return the ``--stat`` output of diff against *base_ref*."""
    r = git(
        ["diff", f"{base_ref}..HEAD", "--stat"],
        cwd=repo,
        check=False,
        identity=False,
    )
    return r.stdout.strip()


# ───────────────────────────────────────────────────────────────────────────
# GitHub API (curl)
# ───────────────────────────────────────────────────────────────────────────
def check_github_token() -> str:
    """Return GITHUB_TOKEN from env, or die with instructions."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        die(
            "GITHUB_TOKEN environment variable is not set. "
            "Export a PAT with 'repo' scope: export GITHUB_TOKEN=ghp_..."
        )
    return token


def github_api(
    method: str,
    endpoint: str,
    token: str,
    payload: Optional[dict] = None,
) -> dict:
    """Call the GitHub REST API via curl. Returns the parsed JSON response.

    Raises RuntimeError on non-2xx status.
    """
    url = f"https://api.github.com/{endpoint.lstrip('/')}"
    cmd = [
        "curl", "-s", "-w", "\n__HTTP_STATUS__%{http_code}",
        "-X", method.upper(),
        url,
        "-H", f"Authorization: Bearer {token}",
        "-H", "Accept: application/vnd.github+json",
        "-H", "X-GitHub-Api-Version: 2022-11-28",
    ]
    if payload is not None:
        cmd += ["-d", json.dumps(payload)]

    r = subprocess.run(cmd, capture_output=True, text=True)
    raw = r.stdout
    # Split status code from body
    parts = raw.rsplit("__HTTP_STATUS__", 1)
    body = parts[0].strip() if len(parts) > 0 else ""
    status_code = int(parts[1].strip()) if len(parts) > 1 else 0

    try:
        data = json.loads(body) if body else {}
    except json.JSONDecodeError:
        data = {"raw_body": body}

    if status_code < 200 or status_code >= 300:
        msg = data.get("message", body[:500]) if isinstance(data, dict) else body[:500]
        raise RuntimeError(
            f"GitHub API {method} {url} returned {status_code}: {msg}"
        )
    if isinstance(data, dict):
        data["_http_status"] = status_code
    return data


def resolve_repo(name: str) -> tuple[str, pathlib.Path, dict]:
    """Resolve a repo name to (canonical_name, path, metadata). Dies on invalid."""
    name = name.lower().strip()
    if name in REPOS:
        meta = REPOS[name]
        return name, meta["path"], meta
    die(f"Unknown repo: {name!r}. Must be one of: {', '.join(REPOS)}")
    # unreachable
    raise SystemExit(1)
