---
name: vllm-api-compat
description: Monitor vLLM serve API parameter compatibility on Ascend and auto-fix regressions. Use for "check API compat", "test serve params", "run daily compat check", "API参数适配检测", "每日例行检测", "参数兼容性". Do not use for performance benchmarks, machine management, or code sync.
---

# vLLM API Compat

Test every `vllm serve` CLI parameter for Ascend compatibility, detect newly added parameters from upstream PRs, and auto-fix regressions.

This skill manages a **parameter test tree** with two YAML sources:
- `references/params_full.yaml` — full 419-node tree (all sections, all types, nested subfields with dependency annotations)
- `references/params_simple.yaml` — bool-only subset (238 test cases), each section has an independent `baseline` command

Each parameter is tested by launching a local `vllm serve` process with that parameter enabled and sending a minimal inference request.

## Use this skill when

- the user asks to check API parameter compatibility on Ascend
- the user asks to test serve parameters
- the user asks to run a daily compat check or routine inspection
- the user asks whether new upstream vllm parameters work on Ascend

## Do not use this skill when

- the task is running performance benchmarks (use `vllm-ascend-benchmark`)
- the task is managing machines (use `machine-management`)
- the task is syncing code (use `remote-code-parity`)
- the task is starting/stopping a production service (use `vllm-ascend-serving`)

## Critical rules

- All execution is **local** — never SSH to remote machines.
- Each parameter test starts a **fresh** `vllm serve` process and stops it after.
- PASS = the service starts, `/health` returns 200, and `/v1/completions` returns a valid JSON response.
- FAIL = startup crash, health timeout, or request error.
- Progress on `stderr` as `__VAWS_VLLM_API_COMPAT_PROGRESS__=<json>`, final result on `stdout` as JSON.
- `daily_check.py` requires `GITHUB_TOKEN` env var.
- NPU: set `ASCEND_RT_VISIBLE_DEVICES` before running; set `PYTHONPATH` to include the local `vllm/` submodule.

## Cross-platform launcher rule

- macOS / Linux / WSL: `python3 ...`
- Windows: `py -3 ...`

## Public entry points

### Simple format — test a single param (recommended)

```bash
export PYTHONPATH="/path/to/vllm-ascend-workspace/vllm:$PYTHONPATH"
export ASCEND_RT_VISIBLE_DEVICES=4,5,6,7

python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --format simple \
  --host <serve-host> \
  --nodes single \
  --section GlobalOptions \
  --param="--aggregate-engine-logging" \
  --timeout 400 \
  --log-path ./server-api-log
```

### Simple format — test all params in a section

```bash
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --format simple \
  --host <serve-host> \
  --nodes single --section ModelConfig \
  --timeout 400
```

### Simple format — test all sections

```bash
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --format simple \
  --host <serve-host> \
  --nodes all \
  --timeout 400
```

### Legacy format — test all parameter nodes

```bash
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --model <model-path> --nodes all [--timeout 120]
```

### Pressure test

```bash
python3 .agents/skills/vllm-api-compat/scripts/bench_test.py \
  --model <model-path> [--num-prompts 100] [--concurrency 4]
```

### Daily check (requires GITHUB_TOKEN)

```bash
GITHUB_TOKEN=ghp_... python3 .agents/skills/vllm-api-compat/scripts/daily_check.py \
  --model <model-path>
```

## cli.py argument reference

| Flag | Default | Description |
|------|---------|-------------|
| `--format` | `legacy` | `simple` uses `params_simple.yaml`; `legacy` uses `params.yaml` |
| `--host` | — | Host passed to `vllm serve` (simple format) |
| `--port` | auto | Override port; otherwise a free port is chosen per test |
| `--nodes` | required | `all` or `single` |
| `--section` | — | Section name (required when `--nodes single`) |
| `--param` | — | Single param CLI name to test, e.g. `--aggregate-engine-logging` |
| `--timeout` | 180 | Health-check timeout in seconds (use 400+ for DP2×TP2) |
| `--log-path` | `./server-api-log` | Root log dir; `results/` and `serve/` subdirs created inside |
| `--params-yaml` | — | Override path to params YAML |
| `--model` | — | Model path (legacy format only) |

## Log layout

```
<log-path>/           (default: ./server-api-log)
├── results/          # per-run summary JSON files
│   └── summary_<timestamp>.json
└── serve/            # vllm process stdout/stderr per test case
    ├── <section>_<param>_True_<timestamp>_stdout.log
    └── <section>_<param>_True_<timestamp>_stderr.log
```

## Local state

```
.vaws-local/vllm-api-compat/
├── params.yaml       # legacy parameter registry (runtime state)
└── daily/
    ├── state.json    # {last_pr_number, last_run}
    └── fixes/        # per-param fix stubs
```

## Workflow

### cli.py (simple format)

1. Load `references/params_simple.yaml`.
2. For each section: read `baseline` (the root `vllm serve` command template).
3. Per param entry: append the flag to baseline, start `vllm serve`, poll `/health` on `--host`, send `/v1/completions`, stop.
4. Wait for NPU HBM and HCCL ports to release before the next test.
5. Write `results/summary_<ts>.json` and print final JSON to stdout.

### cli.py (legacy format)

1. Load `params.yaml` parameter registry.
2. Per parameter: build baseline command + test parameter, start `vllm serve`, wait for health, send request, stop.
3. Update `params.yaml` with PASS/FAIL status and timestamp.
4. Output summary JSON.

### daily_check.py

1. Poll `vllm-project/vllm` GitHub PRs for changes to serve CLI or config files.
2. Auto-detect new parameters from PR diffs.
3. Add new params to `params.yaml`.
4. Run `cli.py --nodes all`.
5. For FAILs: attempt auto-fix, re-test, invoke `auto-commit-pr` if fixes applied.

## Reference files

- `.agents/skills/vllm-api-compat/references/params_full.yaml` — full 419-node parameter tree
- `.agents/skills/vllm-api-compat/references/params_simple.yaml` — bool-only test cases with per-section baselines
- `.agents/skills/vllm-api-compat/references/serve_cli.md` — verbatim transcription of `vllm serve --help=all`
- `.agents/skills/vllm-api-compat/references/behavior.md` — test lifecycle and PASS/FAIL definitions
- `.agents/skills/vllm-api-compat/references/acceptance.md` — acceptance criteria
- `.agents/skills/vllm-api-compat/references/command-recipes.md` — quick-reference commands


## Use this skill when

- the user asks to check API parameter compatibility on Ascend
- the user asks to test serve parameters
- the user asks to run a daily compat check or routine inspection
- the user asks whether new upstream vllm parameters work on Ascend

## Do not use this skill when

- the task is running performance benchmarks (use `vllm-ascend-benchmark`)
- the task is managing machines (use `machine-management`)
- the task is syncing code (use `remote-code-parity`)
- the task is starting/stopping a production service (use `vllm-ascend-serving`)

## Critical rules

- All execution is **local** — never SSH to remote machines.
- Each parameter test starts a **fresh** `vllm serve` process and stops it after.
- PASS = the service starts, `/health` returns 200, and `/v1/completions` returns a valid JSON response.
- FAIL = startup crash, health timeout, or request error.
- Keep local runtime state only under `.vaws-local/vllm-api-compat/`.
- Progress on `stderr` as `__VAWS_VLLM_API_COMPAT_PROGRESS__=<json>`, final result on `stdout` as JSON.
- `daily_check.py` requires `GITHUB_TOKEN` env var.

## Cross-platform launcher rule

- macOS / Linux / WSL: `python3 ...`
- Windows: `py -3 ...`

## Public entry points

### Test all parameter nodes

```bash
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --model <model-path> --nodes all [--timeout 120]
```

### Test a single config section

```bash
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --model <model-path> --nodes single --section ModelConfig
```

### Pressure test

```bash
python3 .agents/skills/vllm-api-compat/scripts/bench_test.py \
  --model <model-path> [--num-prompts 100] [--concurrency 4]
```

### Daily check (requires GITHUB_TOKEN)

```bash
GITHUB_TOKEN=ghp_... python3 .agents/skills/vllm-api-compat/scripts/daily_check.py \
  --model <model-path>
```

## Local state

Per-run state is stored under `.vaws-local/vllm-api-compat/`:

```
.vaws-local/vllm-api-compat/
├── params.yaml           # parameter registry
├── results/              # per-run log files
└── daily/
    ├── state.json        # {last_pr_number, last_run}
    └── fixes/            # per-param fix notes
```

## Workflow

### cli.py

1. Load `params.yaml` parameter registry.
2. For `--nodes all`: iterate every section; for `--nodes single`: iterate only the named section.
3. Per parameter: build baseline command + test parameter, start `vllm serve`, wait for health, send request, stop.
4. Update `params.yaml` with PASS/FAIL status and timestamp.
5. Output summary JSON.

### daily_check.py

1. Poll `vllm-project/vllm` GitHub PRs for changes to serve CLI or config files.
2. Auto-detect new parameters from PR diffs.
3. Add new params to `params.yaml`.
4. Run `cli.py --nodes all`.
5. For FAILs: attempt auto-fix, re-test, invoke `auto-commit-pr` if fixes applied.

## Reference files

- `.agents/skills/vllm-api-compat/references/serve_cli.md`
- `.agents/skills/vllm-api-compat/references/behavior.md`
- `.agents/skills/vllm-api-compat/references/acceptance.md`
- `.agents/skills/vllm-api-compat/references/command-recipes.md`
