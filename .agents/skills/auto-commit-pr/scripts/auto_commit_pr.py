#!/usr/bin/env python3
"""auto-commit-pr: commit, rebase, push and open PRs for vllm / vllm-ascend.

Sub-commands
------------
probe   – read-only snapshot of both repos
commit  – stage + commit (handles detached HEAD)
rebase  – rebase current branch onto upstream main
push    – push branch to origin fork
pr      – open a cross-fork pull request via GitHub API

All git operations use the fixed identity ``underfituu <hzhucong@163.com>``
without touching global git config.
"""
from __future__ import annotations

import argparse
import sys
import textwrap

# local helper module ---------------------------------------------------
from _common import (
    REPOS,
    GIT_USER_NAME,
    GIT_USER_EMAIL,
    TMP_UPSTREAM_REMOTE,
    branch_exists,
    check_github_token,
    current_branch,
    die,
    emit_progress,
    ensure_upstream_fetched,
    get_commits_since,
    get_diff_stat,
    get_dirty_files,
    get_repo_status,
    get_upstream_ref,
    git,
    github_api,
    head_sha,
    is_detached_head,
    print_json,
    remote_exists,
    resolve_repo,
)

VALID_PR_TITLE_PREFIXES = (
    "[BugFix]", "[Performance]", "[Test]", "[CI]",
    "[Feature]", "[Doc]", "[Misc]", "[Community]", "[Refactor]",
)

# ═══════════════════════════════════════════════════════════════════════════
# probe
# ═══════════════════════════════════════════════════════════════════════════

def cmd_probe(args: argparse.Namespace) -> None:
    """Read-only probe of repository state."""
    targets = list(REPOS) if args.repos == "both" else [args.repos]
    result: dict = {"repos": {}}

    for name in targets:
        _, repo_path, meta = resolve_repo(name)
        emit_progress("probe", f"checking {name}")
        status = get_repo_status(repo_path)

        # upstream head (read-only, no fetch for vllm/)
        upstream_head = None
        has_upstream_remote = meta["upstream_remote"] is not None
        if has_upstream_remote:
            ref = f"{meta['upstream_remote']}/{meta['upstream_branch']}"
            r = git(["rev-parse", "--short", ref], cwd=repo_path, check=False, identity=False)
            if r.returncode == 0:
                upstream_head = r.stdout.strip()
        else:
            # vllm/ — use ls-remote (no fetch, no side-effect)
            r = git(
                ["ls-remote", meta["upstream_url"], meta["upstream_branch"]],
                cwd=repo_path, check=False, identity=False,
            )
            if r.returncode == 0 and r.stdout.strip():
                upstream_head = r.stdout.strip().split()[0][:12]

        status["has_upstream_remote"] = has_upstream_remote
        status["upstream_head"] = upstream_head
        status["github_upstream"] = meta["github_upstream"]
        status["github_fork_owner"] = meta["github_fork_owner"]
        result["repos"][name] = status

    print_json(result)


# ═══════════════════════════════════════════════════════════════════════════
# commit
# ═══════════════════════════════════════════════════════════════════════════

def cmd_commit(args: argparse.Namespace) -> None:
    """Stage and commit changes on a (possibly new) branch."""
    name, repo_path, _ = resolve_repo(args.repo)

    detached = is_detached_head(repo_path)
    on_main = (not detached) and current_branch(repo_path) == "main"

    # Determine branch
    branch = args.branch
    if branch is None:
        if detached:
            die(f"{name} is in detached HEAD state — --branch is required")
        if on_main:
            die(f"{name} is on 'main' — --branch is required to create a feature branch")
        branch = current_branch(repo_path)

    # Create or checkout branch if needed
    if detached or on_main:
        if branch_exists(repo_path, branch):
            emit_progress("commit", f"checking out existing branch {branch}")
            git(["checkout", branch], cwd=repo_path)
            # Cherry-pick or merge the detached changes — actually the uncommitted
            # working-tree changes follow checkout automatically if there is no conflict.
        else:
            emit_progress("commit", f"creating branch {branch}")
            git(["checkout", "-b", branch], cwd=repo_path)
    elif current_branch(repo_path) != branch:
        # On a different branch — switch
        if branch_exists(repo_path, branch):
            git(["checkout", branch], cwd=repo_path)
        else:
            git(["checkout", "-b", branch], cwd=repo_path)

    # Run lint/format for vllm-ascend before staging
    if name == "vllm-ascend":
        format_sh = repo_path / "format.sh"
        emit_progress("commit", "running format.sh")
        r = subprocess.run(["bash", str(format_sh)], cwd=repo_path)
        if r.returncode != 0:
            die("format.sh failed — fix lint errors before committing")

    # Stage files
    if args.files:
        emit_progress("commit", f"staging {len(args.files)} file(s)")
        git(["add", "--"] + args.files, cwd=repo_path)
    else:
        emit_progress("commit", "staging all changes")
        git(["add", "-A"], cwd=repo_path)

    # Check if there is anything to commit
    r = git(["diff", "--cached", "--quiet"], cwd=repo_path, check=False)
    if r.returncode == 0:
        die(f"No staged changes to commit in {name}")

    # Commit
    emit_progress("commit", "committing")
    git(["commit", "-m", args.message], cwd=repo_path)

    sha = head_sha(repo_path)
    print_json({
        "repo": name,
        "branch": branch,
        "commit_sha": sha,
        "message": args.message,
        "author": f"{GIT_USER_NAME} <{GIT_USER_EMAIL}>",
    })


# ═══════════════════════════════════════════════════════════════════════════
# rebase
# ═══════════════════════════════════════════════════════════════════════════

def cmd_rebase(args: argparse.Namespace) -> None:
    """Rebase current branch onto upstream main."""
    name, repo_path, meta = resolve_repo(args.repo)

    branch = current_branch(repo_path)
    if branch is None:
        die(f"{name} is in detached HEAD — commit to a branch first")

    # Determine rebase target
    if args.onto:
        onto_ref = args.onto
    else:
        onto_ref = ensure_upstream_fetched(name, repo_path)

    emit_progress("rebase", f"rebasing {branch} onto {onto_ref}")
    r = git(["rebase", onto_ref], cwd=repo_path, check=False)

    if r.returncode != 0:
        # Check for conflict markers
        status_r = git(["status", "--porcelain"], cwd=repo_path, identity=False)
        conflicts = [
            line[3:].strip()
            for line in status_r.stdout.splitlines()
            if line.startswith("UU") or line.startswith("AA")
        ]
        print_json({
            "repo": name,
            "branch": branch,
            "status": "conflict",
            "rebased_onto": onto_ref,
            "conflicts": conflicts,
            "stderr": r.stderr.strip(),
            "instruction": "Resolve conflicts, then: git add <files> && git rebase --continue",
        })
        return

    sha = head_sha(repo_path)
    print_json({
        "repo": name,
        "branch": branch,
        "status": "ok",
        "rebased_onto": onto_ref,
        "head_sha": sha,
    })


# ═══════════════════════════════════════════════════════════════════════════
# push
# ═══════════════════════════════════════════════════════════════════════════

def cmd_push(args: argparse.Namespace) -> None:
    """Push branch to origin fork."""
    name, repo_path, _ = resolve_repo(args.repo)

    branch = args.branch or current_branch(repo_path)
    if branch is None:
        die(f"{name} is in detached HEAD — cannot push")

    push_args = ["push", "origin", branch]
    if args.force_with_lease:
        push_args.insert(1, "--force-with-lease")
    if args.set_upstream:
        push_args.insert(1, "-u")

    emit_progress("push", f"pushing {branch} to origin")
    r = git(push_args, cwd=repo_path, check=False)

    if r.returncode != 0:
        stderr = r.stderr.strip()
        if "rejected" in stderr.lower() or "non-fast-forward" in stderr.lower():
            print_json({
                "repo": name,
                "branch": branch,
                "status": "rejected",
                "hint": "Try with --force-with-lease (default on) after rebase",
                "stderr": stderr,
            })
        else:
            print_json({
                "repo": name,
                "branch": branch,
                "status": "error",
                "stderr": stderr,
            })
        return

    print_json({
        "repo": name,
        "branch": branch,
        "remote": "origin",
        "status": "ok",
    })


# ═══════════════════════════════════════════════════════════════════════════
# pr
# ═══════════════════════════════════════════════════════════════════════════

def _validate_pr_title_prefix(title: str) -> None:
    """Die if title does not start with a recognised category prefix."""
    for prefix in VALID_PR_TITLE_PREFIXES:
        if title.startswith(prefix):
            return
    allowed = ", ".join(VALID_PR_TITLE_PREFIXES)
    die(
        f"PR title must start with a category prefix.\n"
        f"  Got:     {title!r}\n"
        f"  Allowed: {allowed}\n"
        f"Provide a --title that begins with one of the allowed prefixes."
    )


def _generate_pr_body(repo_path, upstream_ref: str, commits: list[dict]) -> str:
    """Generate a markdown PR body from commits and diff stat."""
    diff_stat = get_diff_stat(repo_path, upstream_ref)

    lines = ["## Summary\n"]
    for c in commits:
        lines.append(f"- `{c['sha']}` {c['subject']}")
    lines.append("")

    if diff_stat:
        lines.append("## Changes\n")
        lines.append(f"```\n{diff_stat}\n```\n")

    lines.append("## Test Plan\n")
    lines.append("- [ ] Existing CI passes")
    lines.append("- [ ] Manual verification")
    lines.append("")

    return "\n".join(lines)


def cmd_pr(args: argparse.Namespace) -> None:
    """Create a pull request via GitHub API."""
    name, repo_path, meta = resolve_repo(args.repo)
    token = check_github_token()

    branch = args.branch or current_branch(repo_path)
    if branch is None:
        die(f"{name} is in detached HEAD — commit and push to a branch first")

    base = args.base
    upstream_repo = meta["github_upstream"]
    fork_owner = meta["github_fork_owner"]
    head = f"{fork_owner}:{branch}"

    # Generate title/body if not provided
    upstream_ref = get_upstream_ref(name, repo_path)
    if upstream_ref is None:
        # Need to fetch upstream to generate description
        upstream_ref = ensure_upstream_fetched(name, repo_path)

    commits = get_commits_since(repo_path, upstream_ref)

    title = args.title
    if not title:
        if commits:
            title = commits[0]["subject"]
        else:
            title = f"[{name}] Changes on branch {branch}"

    _validate_pr_title_prefix(title)

    body = args.body
    if not body:
        body = _generate_pr_body(repo_path, upstream_ref, commits)

    # Check for existing PR
    emit_progress("pr", "checking for existing PR")
    try:
        existing = github_api(
            "GET",
            f"repos/{upstream_repo}/pulls?head={fork_owner}:{branch}&base={base}&state=open",
            token,
        )
        # github_api returns dict, but list endpoint returns a list. Handle both.
        if isinstance(existing, list) and len(existing) > 0:
            pr = existing[0]
            print_json({
                "repo": name,
                "pr_number": pr["number"],
                "pr_url": pr["html_url"],
                "title": pr["title"],
                "head": head,
                "base": base,
                "status": "already_exists",
            })
            return
    except RuntimeError:
        pass  # If check fails, proceed to create

    # Create PR
    emit_progress("pr", f"creating PR: {head} → {upstream_repo}:{base}")
    payload = {
        "title": title,
        "body": body,
        "head": head,
        "base": base,
        "draft": args.draft,
    }

    try:
        result = github_api("POST", f"repos/{upstream_repo}/pulls", token, payload)
        print_json({
            "repo": name,
            "pr_number": result.get("number"),
            "pr_url": result.get("html_url"),
            "title": title,
            "head": head,
            "base": base,
            "status": "created",
        })
    except RuntimeError as exc:
        error_msg = str(exc)
        # If PR already exists (422), report it
        if "422" in error_msg or "already exists" in error_msg.lower():
            print_json({
                "repo": name,
                "head": head,
                "base": base,
                "status": "already_exists",
                "error": error_msg,
            })
        else:
            die(f"Failed to create PR: {error_msg}")


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="auto_commit_pr",
        description="Commit, rebase, push and PR for vllm / vllm-ascend repos.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # --- probe ---
    sp = sub.add_parser("probe", help="Read-only snapshot of repos")
    sp.add_argument(
        "--repos",
        choices=["vllm", "vllm-ascend", "both"],
        default="both",
        help="Which repos to probe (default: both)",
    )

    # --- commit ---
    sp = sub.add_parser("commit", help="Stage and commit changes")
    sp.add_argument("--repo", required=True, choices=["vllm", "vllm-ascend"])
    sp.add_argument("--message", "-m", required=True, help="Commit message")
    sp.add_argument("--branch", "-b", help="Branch name (required for detached HEAD or main)")
    sp.add_argument("--files", nargs="*", help="Specific files to stage (default: all)")

    # --- rebase ---
    sp = sub.add_parser("rebase", help="Rebase onto upstream main")
    sp.add_argument("--repo", required=True, choices=["vllm", "vllm-ascend"])
    sp.add_argument("--onto", help="Override rebase target ref (default: auto-detect upstream/main)")

    # --- push ---
    sp = sub.add_parser("push", help="Push branch to origin fork")
    sp.add_argument("--repo", required=True, choices=["vllm", "vllm-ascend"])
    sp.add_argument("--branch", "-b", help="Branch to push (default: current)")
    sp.add_argument(
        "--force-with-lease",
        action="store_true",
        default=True,
        help="Use --force-with-lease (default: on)",
    )
    sp.add_argument("--no-force", action="store_false", dest="force_with_lease")
    sp.add_argument("-u", "--set-upstream", action="store_true", default=True)

    # --- pr ---
    sp = sub.add_parser("pr", help="Create a pull request on upstream")
    sp.add_argument("--repo", required=True, choices=["vllm", "vllm-ascend"])
    sp.add_argument("--branch", "-b", help="Head branch (default: current)")
    sp.add_argument("--base", default="main", help="Base branch on upstream (default: main)")
    sp.add_argument(
        "--title",
        help="PR title — must start with a category prefix: "
             "[BugFix], [Performance], [Test], [CI], [Feature], "
             "[Doc], [Misc], [Community], [Refactor]",
    )
    sp.add_argument("--body", help="PR body (auto-generated if omitted)")
    sp.add_argument("--draft", action="store_true", help="Open as draft PR")

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "probe": cmd_probe,
        "commit": cmd_commit,
        "rebase": cmd_rebase,
        "push": cmd_push,
        "pr": cmd_pr,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
