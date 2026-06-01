# Behavior: vllm-api-compat

## Test lifecycle

For each parameter under test:

1. **Build command**: `vllm serve <model> --port <port> --max-model-len 512 --enforce-eager <param-under-test>`
2. **Start**: Launch as a local subprocess, stdout/stderr logged to `STATE_DIR/results/`.
3. **Wait**: Poll `GET http://localhost:<port>/health` every 2 seconds up to `--timeout` (default 120s).
4. **Request**: `POST http://localhost:<port>/v1/completions` with `{"model":"<served_model>","prompt":"Hello","max_tokens":1}`.
5. **Stop**: SIGTERM → 10s grace → SIGKILL.

## PASS / FAIL definitions

- **PASS**: Health returns 200 AND completion request returns HTTP 200 with a JSON body containing `"choices"`.
- **FAIL**: Any of: startup crash, health timeout, non-200 response, invalid JSON, or exception during the test.
- **SKIP**: Parameter cannot be tested in isolation (e.g. `--ssl-certfile` requires a real cert), or no safe `test_value` is defined.

## Baseline command rationale

`--enforce-eager` avoids CUDA graph compilation overhead (fast per-test cycle).
`--max-model-len 512` keeps HBM usage minimal so tests run on a single NPU card.

## Parameter types

- `bool_flag`: Append `--flag` or `--no-flag` as-is.
- `Enum`: Append `--flag <first-choice>`.
- `int`, `float`, `str`: Append `--flag <test_value>`.
- `positional`: Part of the baseline command (e.g. `model_tag`), not independently tested.
- `List`: Append `--flag <test_value>` with a single representative item.

## GitHub PR detection heuristic

`daily_check.py` scans PR diffs for lines matching `add_argument("--param-name", ...)` in:
- `vllm/entrypoints/cli/serve.py`
- `vllm/config.py`

New parameters are auto-classified by inspecting the `add_argument` call for `action=`, `choices=`, `type=`, and `default=`.

## Progress format

All progress lines go to stderr as:
```
__VAWS_VLLM_API_COMPAT_PROGRESS__={"phase":"...","message":"..."}
```

Final JSON result goes to stdout only.
