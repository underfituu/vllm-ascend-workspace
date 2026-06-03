---
name: vllm-api-compat
description: Monitor vLLM serve API parameter compatibility on Ascend and auto-fix regressions. Use for "check API compat", "test serve params", "run daily compat check", "API参数适配检测", "每日例行检测", "参数兼容性". Do not use for performance benchmarks, machine management, or code sync.
---

# vLLM API Compat

Test every `vllm serve` CLI parameter for Ascend compatibility, detect newly added parameters from upstream PRs, and auto-fix regressions.

Parameter test cases are defined in `references/params_simple.yaml` — each section has an independent `baseline` command and a list of bool-only params with `test_value`.

Each parameter is tested by launching a local `vllm serve` process with that parameter enabled, sending a minimal inference request, and optionally running a pressure test (`--bench`).

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

### Test a single param with specific test_value

```bash
export PYTHONPATH="/path/to/vllm-ascend-workspace/vllm:$PYTHONPATH"
export ASCEND_RT_VISIBLE_DEVICES=4,5,6,7

python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --host <serve-host> \
  --nodes single \
  --section GlobalOptions \
  --param=--disable-log-stats \
  --test-value true \
  --timeout 400 \
  --log-path ./server-api-log
```

### Test a single param (all test_values)

```bash
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --host <serve-host> \
  --nodes single \
  --section GlobalOptions \
  --param=--disable-log-stats \
  --timeout 400
```

### Test all params in a section

```bash
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --host <serve-host> \
  --nodes single \
  --section GlobalOptions \
  --timeout 400
```

### Test all sections

```bash
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --host <serve-host> \
  --nodes all \
  --timeout 400
```

### Test with pressure test (bench)

Add `--bench` to any command above. The pressure test runs `vllm bench serve` on the live service after each PASS.

```bash
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --host <serve-host> \
  --nodes single \
  --section GlobalOptions \
  --param=--disable-log-stats \
  --test-value true \
  --bench \
  --bench-num-prompts 10 \
  --bench-concurrency 4 \
  --timeout 400
```

### Standalone pressure test

```bash
python3 .agents/skills/vllm-api-compat/scripts/bench_test.py \
  --model <model-path> [--num-prompts 10] [--concurrency 4]
```

### Daily check (requires GITHUB_TOKEN)

```bash
GITHUB_TOKEN=ghp_... python3 .agents/skills/vllm-api-compat/scripts/daily_check.py \
  --model <model-path>
```

## cli.py argument reference

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | — | Host passed to `vllm serve` |
| `--port` | auto | Override port; otherwise a free port is chosen per test |
| `--nodes` | required | `all` or `single` |
| `--section` | — | Section name (required when `--nodes single`) |
| `--param` | — | Single param CLI name, e.g. `--param=--disable-log-stats` |
| `--test-value` | — | Filter by test_value, e.g. `true` or `false` |
| `--timeout` | 180 | Health-check timeout in seconds (use 400+ for DP2xTP2) |
| `--log-path` | `./server-api-log` | Root log dir |
| `--params-yaml` | — | Override path to params_simple.yaml |
| `--bench` | off | Run pressure test after each PASS |
| `--bench-num-prompts` | 10 | Number of prompts for bench |
| `--bench-concurrency` | 4 | Max concurrency for bench |

## Log layout

```
<log-path>/           (default: ./server-api-log)
├── bench/            # pressure test output
│   └── bench_latest.log
├── results/          # test summary
│   └── summary_latest.json
└── serve/            # vllm process stdout per test case
    └── <section>_<param>_<test_value>_stdout.log
```

Logs are overwritten on each run (no timestamps in filenames).

## Local state

```
.vaws-local/vllm-api-compat/
└── daily/
    ├── state.json    # {last_pr_number, last_run}
    └── fixes/        # per-param fix stubs
```

## Workflow

### cli.py

1. Load `references/params_simple.yaml`.
2. For each section: read `baseline` (the root `vllm serve` command template).
3. Per param entry: append the flag to baseline, start `vllm serve`, poll `/health`, send `/v1/completions`.
4. If `--bench`: run `vllm bench serve` on the live service, attach metrics to result.
5. Stop service, wait for NPU HBM and HCCL ports to release.
6. Write `results/summary_latest.json` and print final JSON to stdout.

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
