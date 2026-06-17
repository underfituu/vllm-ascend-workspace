---
name: auto-commit-pr
description: Commit, rebase, push, and open pull requests for vllm / vllm-ascend repos. Use for requests like "提交代码", "帮我 commit", "推送到 fork", "提 PR", "rebase 到上游", "commit 并提 PR", "把修改提交到上游". Do not use for ordinary coding, benchmark, serving, or machine management tasks.
---

# Auto Commit PR

Automate the full git workflow: commit → rebase → push → PR for `vllm/` and `vllm-ascend/`.

All operations must use a fixed identity (`underfituu <hzhucong@163.com>`) injected via `-c user.name=… -c user.email=…`. **The global git config is never modified.**

For example，git commit -sm "test"

## Use this skill when

- the user asks to commit changes in `vllm/` or `vllm-ascend/`
- the user asks to rebase onto upstream main
- the user asks to push to their fork
- the user asks to open a PR against the upstream repo
- the user asks for a combined commit-push-PR flow
- the user says "提交代码", "帮我提 PR", "push 上去", "rebase 一下"

## Do not use this skill when

- the task is coding, debugging, or code review (no git mutation needed)
- the task is benchmark, serving, profiling, or machine management
- the user wants to work on a completely different repository

## Critical rules

1. **Identity lock**: Every `git commit`, `git rebase`, `git merge` must use `-c user.name=underfituu -c user.email=hzhucong@163.com`. Never run `git config --global` or `git config --local` to change user identity.
2. **No Claude as co-author**: Never add Claude as a co-author, collaborator, or committer. The only author is `underfituu <hzhucong@163.com>`.
3. **Detached HEAD**: `vllm/` is often in detached HEAD state. The `commit` command requires `--branch` to create a feature branch before committing.
4. **Never commit on main directly**: Always create a feature branch. If the user is on `main`, `commit` requires `--branch` to fork off.
5. **vllm/ has no upstream remote**: The `rebase` command automatically adds a temporary remote `_upstream_tmp` pointing to `vllm-project/vllm` and fetches from it. This is transparent to the user.
6. **GITHUB_TOKEN required for PR**: The `pr` command needs `GITHUB_TOKEN` env var with `repo` scope. Prompt the user if missing.
7. **Rebase conflicts**: If rebase produces conflicts, output the conflict list and stop. Do not auto-abort. Let the user resolve, then re-run push + pr.
8. **Probe first**: Always run `probe` before any mutation to understand the current state.
9. **PR title prefix**: Every PR title must start with one of: `[BugFix]`, `[Performance]`, `[Test]`, `[CI]`, `[Feature]`, `[Doc]`, `[Misc]`, `[Community]`, `[Refactor]`. The script validates this and exits with an error if the prefix is missing — it will not auto-add a prefix.

## Script-first entry points

All commands below run from the workspace root.

### Probe (read-only)
```bash
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py probe
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py probe --repos vllm
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py probe --repos vllm-ascend
```

### Commit
```bash
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py commit \
  --repo vllm \
  --branch fix/kv-cache-coordinator \
  --message "fix: improve KV cache coordinator logic"

python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py commit \
  --repo vllm-ascend \
  --branch fix/mamba-config \
  --message "fix: patch mamba config for Ascend" \
  --files vllm_ascend/patch/platform/patch_mamba_config.py
```

### Rebase
```bash
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py rebase --repo vllm
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py rebase --repo vllm-ascend
```

### Push
```bash
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py push --repo vllm
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py push --repo vllm-ascend --no-force
```

### Create PR
```bash
GITHUB_TOKEN=ghp_... python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py pr \
  --repo vllm \
  --branch fix/kv-cache-coordinator

GITHUB_TOKEN=ghp_... python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py pr \
  --repo vllm-ascend \
  --branch fix/mamba-config \
  --title "[BugFix] patch mamba config for Ascend platform" \
  --draft
```

## Workflow

### 1. Probe

Run the probe and summarize the state of each repo to the user:
- detached HEAD or not
- current branch
- dirty files
- upstream HEAD comparison

### 2. Confirm with user

Before any mutation, confirm:
- **Which repo(s)** to commit (vllm, vllm-ascend, or both)
- **Branch name** for the feature branch
- **Commit message** — draft one based on the dirty files and ask for approval
- **Whether to rebase** onto upstream main

### 3. Commit

Run `commit` for each target repo. Handle detached HEAD automatically.

### 4. Rebase (optional but recommended)

Run `rebase` to put the commit(s) on top of upstream main.

If conflicts occur:
- Report the conflicting files
- Stop and let the user resolve
- After resolution, the user re-triggers push + pr

### 5. Push

Run `push` to send the branch to the origin fork. Uses `--force-with-lease` by default (safe after rebase).

### 6. Create PR

Run `pr` to open a pull request on the upstream repo. The script:
- Auto-generates title from the first commit subject (or user can override)
- **Title must start with a category prefix**: `[BugFix]`, `[Performance]`, `[Test]`, `[CI]`, `[Feature]`, `[Doc]`, `[Misc]`, `[Community]`, `[Refactor]`. If the title (whether user-provided or auto-generated) lacks a valid prefix, the script exits with an error.
- Auto-generates body from commit log + diff stat
- Sets `head` to `underfituu:<branch>` for cross-fork PR
- Checks for existing open PR to avoid duplicates
- Description Template:
<!--  Thanks for sending a pull request!

BEFORE SUBMITTING, PLEASE READ https://docs.vllm.ai/en/latest/contributing/overview.html

-->
### What this PR does / why we need it?
<!--
- Please clarify what changes you are proposing. The purpose of this section is to outline the changes and how this PR fixes the issue.
If possible, please consider writing useful notes for better and faster reviews in your PR.

- Please clarify why the changes are needed. For instance, the use case and bug description.

- Fixes #
-->

### Does this PR introduce _any_ user-facing change?
<!--
Note that it means *any* user-facing change including all aspects such as API, interface or other behavior changes.
Documentation-only updates are not considered user-facing changes.
-->

### How was this patch tested?
<!--
CI passed with new added/existing test.
If it was tested in a way different from regular unit tests, please clarify how you tested step by step, ideally copy and paste-able, so that other reviewers can test and check, and descendants can verify in the future.
If tests were not added, please describe why they were not added and/or why it was difficult to add.
-->



### 7. Report

Output the PR URL and status to the user.

## Reference files

- `.agents/skills/auto-commit-pr/references/behavior.md` — detailed behavior rules
- `.agents/skills/auto-commit-pr/references/acceptance.md` — acceptance criteria
- `.agents/skills/auto-commit-pr/references/command-recipes.md` — copy-paste recipes
