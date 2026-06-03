#!/usr/bin/env python3
"""CLI test runner for vLLM serve API parameter compatibility (params_simple.yaml).

Usage:
    python3 cli.py --host <host> --nodes all
    python3 cli.py --host <host> --nodes single --section GlobalOptions
    python3 cli.py --host <host> --nodes single --section GlobalOptions --param --disable-log-stats --test-value true
"""

from __future__ import annotations

import argparse
import json as _json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _common
from _common import (
    ACCURACY_PROMPTS,
    build_extra_args_simple,
    compare_accuracy,
    emit_progress,
    extract_metrics,
    find_free_port,
    load_simple_params_yaml,
    now_utc,
    print_json,
    read_serve_logs,
    run_bench,
    send_accuracy_request,
    send_completion_request,
    start_vllm_serve,
    stop_vllm_serve,
    wait_for_ready,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Test vLLM serve CLI parameters for Ascend compatibility")
    p.add_argument("--host", default=None, help="Host to pass to vllm serve")
    p.add_argument("--port", type=int, default=None, help="Port override (default: auto)")
    p.add_argument("--nodes", required=True, choices=["all", "single"])
    p.add_argument("--section", default=None, help="Section name (required when --nodes single)")
    p.add_argument("--param", default=None, metavar="PARAM",
                   help="Single param name to test, e.g. --param=--disable-log-stats")
    p.add_argument("--test-value", default=None, help="Filter by test_value, e.g. true or false")
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--params-yaml", default=None, help="Override path to params_simple.yaml")
    p.add_argument("--log-path", default="./server-api-log",
                   help="Root log directory")
    p.add_argument("--bench", action="store_true", help="Run pressure test after each PASS")
    p.add_argument("--bench-num-prompts", type=int, default=10)
    p.add_argument("--bench-concurrency", type=int, default=4)
    p.add_argument("--accuracy", action="store_true",
                   help="Run accuracy check: compare outputs against baseline with temperature=0")
    return p


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _param_key(param_entry: dict) -> str:
    """Build a filesystem-safe key like `disable_log_stats_True`."""
    name = param_entry.get("name", "unknown")
    tv = param_entry.get("test_value")
    return f"{name.lstrip('-').replace('-', '_')}_{tv}"


def _baseline_to_args(baseline: list[str], host: str | None) -> tuple[str, list[str]]:
    model = baseline[0]
    args = []
    for item in baseline[1:]:
        args.extend(item.split())
    if host:
        args += ["--host", host]
    return model, args


def _get_served_model(baseline: list[str]) -> str:
    served_model = baseline[0].rstrip("/").split("/")[-1]
    for i, item in enumerate(baseline[1:], 1):
        if item == "--served-model-name" and i + 1 < len(baseline):
            return baseline[i + 1]
        if item.startswith("--served-model-name "):
            return item.split(" ", 1)[1]
    return served_model


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Baseline accuracy collection (once per section)
# ---------------------------------------------------------------------------

def _collect_baseline_outputs(
    section_name: str, baseline: list[str], host: str | None, timeout: int,
) -> list[str] | None:
    model, baseline_args = _baseline_to_args(baseline, host)
    port = find_free_port()
    emit_progress("accuracy_baseline", f"collecting baseline outputs for {section_name} on port {port}")
    proc = None
    try:
        proc = start_vllm_serve(model, baseline_args, port,
                                log_prefix=f"{section_name}/baseline", use_baseline_args=False)
        if not wait_for_ready(port, timeout, host=host or "localhost"):
            emit_progress("accuracy_baseline", "baseline service health timeout")
            return None
        served_model = _get_served_model(baseline)
        ok, outputs, err = send_accuracy_request(served_model, port, host=host or "localhost")
        log_data: dict
        if ok:
            log_data = {"status": "ok", "prompts": list(ACCURACY_PROMPTS),
                        "outputs": outputs, "timestamp": now_utc()}
        else:
            log_data = {"status": "failed", "error": err, "timestamp": now_utc()}
        _write_json(_common.LOG_DIR / "accuracy" / section_name / "baseline.json", log_data)
        if ok:
            emit_progress("accuracy_baseline", f"baseline outputs collected: {len(outputs)} prompts")
            return outputs
        emit_progress("accuracy_baseline", f"baseline request failed: {err}")
        return None
    except Exception as e:
        emit_progress("accuracy_baseline", f"baseline exception: {e}")
        return None
    finally:
        if proc is not None:
            stop_vllm_serve(proc)


# ---------------------------------------------------------------------------
# Single param test
# ---------------------------------------------------------------------------

def test_param(
    section_name: str,
    param_entry: dict,
    baseline: list[str],
    host: str | None,
    port: int,
    timeout: int,
    bench: bool = False,
    bench_num_prompts: int = 10,
    bench_concurrency: int = 4,
    accuracy: bool = False,
    baseline_outputs: list[str] | None = None,
) -> dict:
    name = param_entry.get("name", "")
    pkey = _param_key(param_entry)
    extra = build_extra_args_simple(param_entry)
    model, baseline_args = _baseline_to_args(baseline, host)

    emit_progress("test", f"testing {section_name} {name}={param_entry.get('test_value')}", param=name, port=port)

    proc = None
    try:
        proc = start_vllm_serve(
            model, baseline_args + extra, port,
            log_prefix=f"{section_name}/{pkey}", use_baseline_args=False,
        )
        if not wait_for_ready(port, timeout, host=host or "localhost"):
            _, stderr = read_serve_logs(proc)
            return {"section": section_name, "param": name, "test_value": param_entry.get("test_value"),
                    "status": "FAIL", "notes": f"health timeout: {stderr[-300:]}"}

        served_model = _get_served_model(baseline)
        ok, err = send_completion_request(served_model, port, host=host or "localhost")
        result = {"section": section_name, "param": name, "test_value": param_entry.get("test_value"),
                  "status": "PASS" if ok else "FAIL", "notes": "" if ok else err}

        if ok and bench:
            try:
                bench_log_dir = _common.LOG_DIR / "bench" / section_name
                bench_log_dir.mkdir(parents=True, exist_ok=True)
                raw = run_bench(model, port, bench_num_prompts, bench_concurrency,
                                _common.LOG_DIR, log_name=f"{section_name}/{pkey}")
                result["bench"] = extract_metrics(raw)
            except Exception as be:
                result["bench_error"] = str(be)

        if ok and accuracy and baseline_outputs is not None:
            try:
                a_ok, test_outputs, a_err = send_accuracy_request(served_model, port, host=host or "localhost")
                acc_path = _common.LOG_DIR / "accuracy" / section_name / f"{pkey}.json"
                if a_ok:
                    cmp = compare_accuracy(baseline_outputs, test_outputs)
                    result["accuracy"] = cmp
                    _write_json(acc_path, {"status": "ok", "comparison": cmp,
                                           "prompts": list(ACCURACY_PROMPTS),
                                           "test_outputs": test_outputs, "timestamp": now_utc()})
                else:
                    result["accuracy_error"] = a_err
                    _write_json(acc_path, {"status": "failed", "error": a_err, "timestamp": now_utc()})
            except Exception as ae:
                result["accuracy_error"] = str(ae)

        # Write per-param result
        _write_json(_common.LOG_DIR / "results" / section_name / f"{pkey}.json", result)

        return result
    except Exception as e:
        return {"section": section_name, "param": name, "test_value": param_entry.get("test_value"),
                "status": "FAIL", "notes": f"exception: {e}"}
    finally:
        if proc is not None:
            stop_vllm_serve(proc)


# ---------------------------------------------------------------------------
# Iteration
# ---------------------------------------------------------------------------

def _iter_params(section_data: list[dict], filter_param: str | None, filter_test_value=None):
    for p in section_data:
        if "subfields" in p:
            parent_cli = p["name"]
            for sf in p["subfields"]:
                entry = {"name": parent_cli, "test_value": None, "subfields": [sf]}
                if filter_param is None or parent_cli == filter_param:
                    yield entry
        else:
            if filter_param is None or p["name"] == filter_param:
                if filter_test_value is None or str(p.get("test_value")).lower() == str(filter_test_value).lower():
                    yield p


def _fix_argv(argv: list[str]) -> list[str]:
    out, i = [], 0
    while i < len(argv):
        if argv[i] in ("--param", "--test-value") and i + 1 < len(argv) and argv[i + 1].startswith("-"):
            out.append(f"{argv[i]}={argv[i + 1]}")
            i += 2
        else:
            out.append(argv[i])
            i += 1
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args(_fix_argv(sys.argv[1:]))

    if args.nodes == "single" and not args.section:
        parser.error("--section is required when --nodes is single")

    _common.LOG_DIR = Path(args.log_path).resolve()

    yaml_path = Path(args.params_yaml) if args.params_yaml else None
    data = load_simple_params_yaml(yaml_path)
    sections = {k: v for k, v in data.items() if k != "meta"}

    if args.nodes == "single":
        if args.section not in sections:
            sys.stderr.write(f"Error: section '{args.section}' not found. Available: {', '.join(sections)}\n")
            sys.exit(1)
        sections_to_test = {args.section: sections[args.section]}
    else:
        sections_to_test = sections

    emit_progress("start", f"sections={list(sections_to_test)}")

    results = []
    for sname, sec in sections_to_test.items():
        baseline = sec["baseline"]
        params = list(_iter_params(sec["params"], args.param, args.test_value))
        emit_progress("section", f"testing {sname} ({len(params)} entries)")

        baseline_outputs = None
        if args.accuracy:
            baseline_outputs = _collect_baseline_outputs(sname, baseline, args.host, args.timeout)
            if baseline_outputs is None:
                emit_progress("accuracy", f"failed to collect baseline outputs for {sname}, skipping accuracy")

        for entry in params:
            port = args.port or find_free_port()
            result = test_param(sname, entry, baseline, args.host, port, args.timeout,
                                bench=args.bench, bench_num_prompts=args.bench_num_prompts,
                                bench_concurrency=args.bench_concurrency,
                                accuracy=args.accuracy, baseline_outputs=baseline_outputs)
            results.append(result)
            emit_progress("result", f"{sname} {result['param']}={result['test_value']}: {result['status']}")

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    summary = {"status": "ok", "tested": len(results), "passed": passed,
               "failed": failed, "skipped": skipped, "results": results,
               "timestamp": now_utc()}

    results_dir = _common.LOG_DIR / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    _write_json(results_dir / "summary_latest.json", summary)
    print_json(summary)


if __name__ == "__main__":
    main()
