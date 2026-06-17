# Behavior Rules

## Identity

- Every `git commit`, `git rebase`, `git merge` call MUST include:
  ```
  -c user.name=underfituu -c user.email=hzhucong@163.com
  ```
- Never run `git config --global user.name` or `git config --local user.name`.
- Never add `Co-authored-by: Claude` or any AI/bot co-author trailer.
- The only valid author line is `underfituu <hzhucong@163.com>`.

## Detached HEAD handling

- `vllm/` is frequently in detached HEAD state (checked out to a specific upstream commit).
- Before committing, the `commit` sub-command creates a new branch from the current HEAD.
- If the branch name already exists locally, it checks out that branch (dirty working tree changes follow the checkout).
- The user must provide `--branch` when HEAD is detached or when on `main`.

## Branch policy

- Never commit directly to `main`. Always create a feature branch.
- Branch naming convention: `fix/<topic>`, `feat/<topic>`, `refactor/<topic>`.
- If the user is on `main`, `commit --branch <name>` forks a new branch from `main` before committing.

## vllm/ — no upstream remote

- `vllm/` has only `origin` → `underfituu/vllm`. There is no `upstream` remote.
- For rebase, the script adds a temporary remote `_upstream_tmp` → `vllm-project/vllm` and fetches `main`.
- This remote persists across sub-command calls within a session. It is not cleaned up automatically.
- `probe` uses `git ls-remote` (read-only, no remote added) to check the upstream HEAD.

## vllm-ascend/ — has upstream remote

- `vllm-ascend/` has `origin` → `underfituu/vllm-ascend` and `upstream` → `vllm-project/vllm-ascend`.
- Rebase uses `upstream/main` directly.

## Rebase conflict policy

- If `git rebase` exits non-zero, the script outputs a `status: "conflict"` JSON with the list of conflicting files.
- It does **not** run `git rebase --abort`. The user must resolve conflicts manually.
- After resolution: `git add <files> && git rebase --continue`, then re-run `push` and `pr`.

## Push behavior

- Default: `git push origin <branch> --force-with-lease -u`
- `--force-with-lease` is safe after rebase (it only force-pushes if the remote ref matches local expectations).
- Use `--no-force` only when the branch has never been pushed before and rebase was skipped.

## PR creation

- PRs are created via GitHub REST API (`POST /repos/{upstream}/pulls`).
- The `head` field must be `underfituu:<branch>` (cross-fork format).
- `GITHUB_TOKEN` must be set in the environment with `repo` scope.
- Before creating, the script checks for an existing open PR with the same head/base — if found, it reports `already_exists` instead of creating a duplicate.
- Auto-generated title: first commit subject.
- Auto-generated body: commit list + diff stat + test plan checklist.
- PR title must start with one of: `[BugFix]`, `[Performance]`, `[Test]`, `[CI]`, `[Feature]`, `[Doc]`, `[Misc]`, `[Community]`, `[Refactor]`.
- If the title (user-provided or auto-generated) lacks a valid prefix, the script exits with an error — it never auto-prepends a prefix.

## GITHUB_TOKEN

- Must be a GitHub Personal Access Token (classic or fine-grained) with `repo` scope.
- Passed via environment variable: `export GITHUB_TOKEN=ghp_...`
- Never accept tokens as CLI arguments (shell history risk).
- If missing, the script exits with a clear error message.

## Progress output

- Progress lines go to stderr: `__VAWS_AUTO_COMMIT_PR_PROGRESS__={"phase":"...","message":"..."}`
- Final JSON result goes to stdout.
- This separation allows the agent to stream progress while collecting the final result.
