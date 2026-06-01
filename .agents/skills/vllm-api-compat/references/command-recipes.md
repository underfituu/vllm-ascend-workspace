# Command Recipes: vllm-api-compat

## Test all parameters

```bash
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --model Qwen/Qwen3-0.6B --nodes all --timeout 120
```

## Test a single config section

```bash
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --model Qwen/Qwen3-0.6B --nodes single --section ModelConfig
```

## Pressure test

```bash
python3 .agents/skills/vllm-api-compat/scripts/bench_test.py \
  --model Qwen/Qwen3-0.6B --num-prompts 50 --concurrency 4
```

## Daily check (dry run)

```bash
GITHUB_TOKEN=ghp_... python3 .agents/skills/vllm-api-compat/scripts/daily_check.py \
  --model Qwen/Qwen3-0.6B --dry-run
```

## Daily check (full run)

```bash
GITHUB_TOKEN=ghp_... python3 .agents/skills/vllm-api-compat/scripts/daily_check.py \
  --model Qwen/Qwen3-0.6B
```

## Inspect test results

```bash
# View latest test output
ls -lt .vaws-local/vllm-api-compat/results/ | head -10

# View params registry
cat .vaws-local/vllm-api-compat/params.yaml

# View daily state
cat .vaws-local/vllm-api-compat/daily/state.json

# Check for fix stubs
ls .vaws-local/vllm-api-compat/daily/fixes/
```

## Check for orphan processes after test

```bash
pgrep -f "vllm serve"
```

## Custom params.yaml path

```bash
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --model Qwen/Qwen3-0.6B --nodes all \
  --params-yaml /path/to/custom/params.yaml
```
