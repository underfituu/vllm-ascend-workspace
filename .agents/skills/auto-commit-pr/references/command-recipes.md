# Command Recipes

All commands run from the workspace root (`vllm-ascend-workspace/`).

## Full workflow — vllm-ascend (typical case)

```bash
# 1. Probe
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py probe --repos vllm-ascend

# 2. Commit
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py commit \
  --repo vllm-ascend \
  --branch fix/mamba-config \
  --message "fix: patch mamba config for Ascend platform"

# 3. Rebase onto upstream main
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py rebase --repo vllm-ascend

# 4. Push to fork
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py push --repo vllm-ascend

# 5. Create PR
GITHUB_TOKEN=$GITHUB_TOKEN python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py pr \
  --repo vllm-ascend \
  --branch fix/mamba-config
```

## Full workflow — vllm (detached HEAD case)

```bash
# 1. Probe
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py probe --repos vllm

# 2. Commit (--branch required because HEAD is detached)
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py commit \
  --repo vllm \
  --branch fix/kv-cache-coordinator \
  --message "fix: improve KV cache coordinator and scheduler logic"

# 3. Rebase (adds _upstream_tmp remote automatically)
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py rebase --repo vllm

# 4. Push
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py push --repo vllm

# 5. Create PR
GITHUB_TOKEN=$GITHUB_TOKEN python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py pr \
  --repo vllm \
  --branch fix/kv-cache-coordinator
```

## Selective file commit

```bash
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py commit \
  --repo vllm \
  --branch fix/scheduler-only \
  --message "fix: scheduler edge case" \
  --files vllm/v1/core/sched/scheduler.py
```

## Draft PR

```bash
GITHUB_TOKEN=$GITHUB_TOKEN python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py pr \
  --repo vllm-ascend \
  --branch feat/new-feature \
  --title "feat: add new feature for Ascend" \
  --draft
```

## Custom PR title and body

```bash
GITHUB_TOKEN=$GITHUB_TOKEN python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py pr \
  --repo vllm-ascend \
  --branch fix/mamba-config \
  --title "fix: patch mamba config" \
  --body "$(cat <<'EOF'
## Summary
- Fix mamba config compatibility for Ascend platform

## Test Plan
- [ ] CI passes
- [ ] Tested on Ascend 910B
EOF
)"
```

## Push without force

```bash
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py push \
  --repo vllm-ascend \
  --no-force
```

## Both repos in one session

```bash
# Probe both
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py probe

# Commit vllm
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py commit \
  --repo vllm --branch fix/kv-cache -m "fix: KV cache issue"

# Commit vllm-ascend
python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py commit \
  --repo vllm-ascend --branch fix/ascend-patch -m "fix: Ascend patch"

# Rebase + push + PR for each
for repo in vllm vllm-ascend; do
  python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py rebase --repo $repo
  python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py push --repo $repo
  GITHUB_TOKEN=$GITHUB_TOKEN python3 .agents/skills/auto-commit-pr/scripts/auto_commit_pr.py pr --repo $repo
done
```

## Verify identity after commit

```bash
# Should show: underfituu <hzhucong@163.com>
git -C vllm log --format='%an <%ae>' -1
git -C vllm-ascend log --format='%an <%ae>' -1

# Global config should be unchanged
git config --global user.name
git config --global user.email
```
