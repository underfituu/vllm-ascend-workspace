# Acceptance Criteria: vllm-api-compat

## cli.py — single section

- [ ] `cli.py --model <model> --nodes single --section ModelConfig` produces stdout JSON with `status: "ok"`.
- [ ] At least one param entry has `status: "PASS"`.
- [ ] `params.yaml` is updated with new `status` and `last_tested` timestamps.
- [ ] Each param test starts a fresh `vllm serve` process and stops it after.
- [ ] No orphan `vllm serve` processes after run (`pgrep -f "vllm serve"` empty).
- [ ] Params with `status: SKIP` are not tested.

## cli.py — all nodes

- [ ] `cli.py --model <model> --nodes all` completes without hanging.
- [ ] `STATE_DIR/results/` has log files.
- [ ] Summary JSON includes `tested`, `passed`, `failed`, `skipped` counts.
- [ ] `params.yaml` is updated for all tested params.

## bench_test.py

- [ ] Starts service, runs `vllm bench serve`, stops service.
- [ ] Output JSON has `status: "ok"` with `metrics` containing at least `output_throughput`.
- [ ] On service start failure: output has `status: "failed"` with `phase: "serve_start"`.
- [ ] Service is stopped after benchmark (no residual processes).

## daily_check.py

- [ ] Requires `GITHUB_TOKEN` env var; exits with error if missing.
- [ ] Detects new params from PRs newer than `state.json`'s `last_pr_number`.
- [ ] New params are appended to `params.yaml` with `status: UNKNOWN`.
- [ ] `state.json` is updated with new `last_pr_number` and `last_run`.
- [ ] `--dry-run` mode reports detected params without running tests.
- [ ] On FAIL with Ascend-specific errors: fix stub written to `daily/fixes/`.

## Progress reporting

- [ ] Progress lines go to stderr as `__VAWS_VLLM_API_COMPAT_PROGRESS__=<json>`.
- [ ] Final JSON goes to stdout only.
- [ ] Each progress line parses as valid JSON.

## params.yaml integrity

- [ ] Daily check does not duplicate existing params.
- [ ] Param entries preserve all fields (name, cli, type, test_value, status, last_tested, notes).
- [ ] `meta.last_updated` reflects the last run timestamp.
