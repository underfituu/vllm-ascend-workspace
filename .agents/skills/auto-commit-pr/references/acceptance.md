# Acceptance Criteria

## probe

1. Returns valid JSON to stdout.
2. For each repo: `detached_head`, `current_branch`, `head_sha`, `dirty`, `dirty_files` are present and correct.
3. `has_upstream_remote` is `false` for `vllm/`, `true` for `vllm-ascend/`.
4. No git config is modified. No remote is added. No fetch is performed.
5. `upstream_head` is populated via `git ls-remote` (vllm/) or local ref (vllm-ascend/).

## commit

1. After commit, `git log --format='%an <%ae>' -1` shows `underfituu <hzhucong@163.com>`.
2. After commit, `git config --global user.name` is unchanged from before.
3. Detached HEAD → new branch is created, commit is on that branch.
4. On `main` → new branch is created, main is untouched.
5. Returns JSON with `repo`, `branch`, `commit_sha`, `message`, `author`.
6. If no staged changes, exits with error JSON — no empty commit created.

## rebase

1. After rebase, `git log --oneline` shows feature commits on top of upstream main.
2. On conflict: returns `status: "conflict"` with file list. Does NOT auto-abort.
3. On success: returns `status: "ok"` with new HEAD sha.
4. For vllm/: `_upstream_tmp` remote is added if missing, `main` is fetched.
5. For vllm-ascend/: `upstream/main` is fetched.

## push

1. Branch appears on `origin` (the fork) after push.
2. Uses `--force-with-lease` by default.
3. On rejection: returns `status: "rejected"` with hint.

## pr

1. PR is created on the upstream repo (e.g., `vllm-project/vllm-ascend`).
2. `head` is `underfituu:<branch>` — NOT the upstream org.
3. Title and body are auto-generated if not provided.
4. If an open PR already exists for the same head/base, returns `already_exists` — no duplicate.
5. Returns `pr_url` on success.
6. Requires `GITHUB_TOKEN` — exits cleanly with error if missing.
7. User-provided `--title` without a valid prefix → error exit, no PR created.
8. Auto-generated title (from commit subject) without a valid prefix → error exit, no PR created.
9. Valid prefixes: `[BugFix]`, `[Performance]`, `[Test]`, `[CI]`, `[Feature]`, `[Doc]`, `[Misc]`, `[Community]`, `[Refactor]`.

## Cross-cutting

1. Global git config is never modified (verify with `git config --global --list` before/after).
2. No Claude/AI co-author trailer in any commit.
3. All JSON output is valid and parseable.
4. Progress output goes to stderr, result to stdout.
