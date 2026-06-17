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
import signal
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
    p.add_argument("--host", default="localhost", help="Host to pass to vllm serve")
    p.add_argument("--port", type=int, default=None, help="Port override (default: auto)")
    p.add_argument("--nodes", default=None, choices=["all", "single"])
    p.add_argument("--section", default=None, help="Section name (required when --nodes single)")
    p.add_argument("--param", default=None, metavar="PARAM",
                   help="Single param to test, e.g. --param=--disable-log-stats or "
                        "--param=--structured-outputs-config.disable_any_whitespace")
    p.add_argument("--test-value", default=None, help="Filter by test_value, e.g. true or false")
    p.add_argument("--timeout", type=int, default=400)
    p.add_argument("--params-yaml", default=None, help="Override path to params_simple.yaml")
    p.add_argument("--log-path", default="./server-api-log", help="Root log directory")
    p.add_argument("--bench", action="store_true", help="Run pressure test after each PASS")
    p.add_argument("--bench-num-prompts", type=int, default=10)
    p.add_argument("--bench-concurrency", type=int, default=4)
    p.add_argument("--accuracy", action="store_true",
                   help="Run accuracy check: compare outputs against baseline with temperature=0")
    p.add_argument("--rerun-failed", default=None, metavar="SUMMARY_JSON",
                   help="Re-run all FAIL entries from a summary.json (overrides --nodes/--section/--param)")
    return p


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_param_filter(raw: str | None) -> tuple[str | None, str | None]:
    """Split --param value into (parent_filter, subfield_filter).

    Examples:
        "--disable-log-stats"                                → ("--disable-log-stats", None)
        "--structured-outputs-config.disable_any_whitespace" → ("--structured-outputs-config", "disable_any_whitespace")
        "--compilation-config.pass_config.fuse_norm_quant"   → ("--compilation-config", "pass_config.fuse_norm_quant")
        None                                                 → (None, None)
    """
    if raw is None:
        return None, None
    dot_idx = raw.find(".")
    if dot_idx == -1:
        return raw, None
    return raw[:dot_idx], raw[dot_idx + 1:]


def _param_full_name(param_entry: dict) -> str:
    """Return the full param name including subfield, e.g. --structured-outputs-config.disable_any_whitespace."""
    name = param_entry.get("name", "unknown")
    sfs = param_entry.get("subfields")
    if sfs:
        return f"{name}.{sfs[0]['name']}"
    return name


def _param_display(section_name: str, param_entry: dict) -> str:
    """Build a tree-style display string for progress output.

    Normal params:   "section / --param=value"
    Subfield params: "section / --parent / subfield=value"
    """
    name = param_entry.get("name", "unknown")
    sfs = param_entry.get("subfields")
    if sfs:
        sf = sfs[0]
        return f"{section_name} / {name} / {sf['name']}={sf['test_value']}"
    return f"{section_name} / {name}={param_entry.get('test_value')}"


def _param_key(param_entry: dict) -> str:
    """Build a filesystem-safe key like `disable_log_stats_True`
    or `structured_outputs_config__disable_any_whitespace_True`."""
    name = param_entry.get("name", "unknown").lstrip("-").replace("-", "_")
    sfs = param_entry.get("subfields")
    if sfs:
        sf = sfs[0]
        sf_name = sf["name"].replace(".", "_")
        return f"{name}__{sf_name}_{sf['test_value']}"
    return f"{name}_{param_entry.get('test_value')}"


def _param_test_value(param_entry: dict):
    """Return the effective test_value for display/filtering."""
    sfs = param_entry.get("subfields")
    if sfs:
        return sfs[0].get("test_value")
    return param_entry.get("test_value")


def _baseline_to_args(baseline: list[str], host: str | None) -> tuple[str, list[str]]:
    model = baseline[0]
    args = []
    for item in baseline[1:]:
        parts = item.split(None, 1)
        args.extend(parts)
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


def _upsert_summary(summary_file: Path, result: dict) -> None:
    """Insert or replace a result in summary.json, keyed by (section, param, test_value)."""
    existing = _json.loads(summary_file.read_text(encoding="utf-8")) if summary_file.exists() else []
    key = (result.get("section"), result.get("param"), result.get("test_value"))
    for i, r in enumerate(existing):
        if (r.get("section"), r.get("param"), r.get("test_value")) == key:
            existing[i] = result
            break
    else:
        existing.append(result)
    summary_file.write_text(_json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Baseline accuracy collection (once per section)
# ---------------------------------------------------------------------------

def _collect_baseline_outputs(
    section_name: str, baseline: list[str], host: str | None, timeout: int,
) -> list[str] | None:
    cached = _common.LOG_DIR / "accuracy" / section_name / "baseline.json"
    if cached.exists():
        try:
            data = _json.loads(cached.read_text(encoding="utf-8"))
            if data.get("status") == "ok" and data.get("outputs"):
                emit_progress("accuracy_baseline", f"reusing cached baseline for {section_name}")
                return data["outputs"]
        except (ValueError, KeyError):
            pass

    model, baseline_args = _baseline_to_args(baseline, host)
    port = find_free_port()
    emit_progress("accuracy_baseline", f"collecting baseline outputs for {section_name} on port {port}")
    proc = None
    try:
        proc = start_vllm_serve(model, baseline_args, port,
                                log_prefix=f"{section_name}/baseline", use_baseline_args=False)
        if not wait_for_ready(port, timeout, host=host or "127.0.0.1"):
            emit_progress("accuracy_baseline", "baseline service health timeout")
            return None
        served_model = _get_served_model(baseline)
        ok, outputs, err = send_accuracy_request(served_model, port, host=host or "127.0.0.1")
        log_data: dict
        if ok:
            log_data = {"status": "ok", "prompts": list(ACCURACY_PROMPTS),
                        "outputs": outputs, "timestamp": now_utc()}
        else:
            log_data = {"status": "failed", "error": err, "timestamp": now_utc()}
        _write_json(cached, log_data)
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
    section_env: dict | None = None,
) -> dict:
    full_name = _param_full_name(param_entry)
    pkey = _param_key(param_entry)
    tv = _param_test_value(param_entry)
    extra = build_extra_args_simple(param_entry)
    model, baseline_args = _baseline_to_args(baseline, host)

    emit_progress("test", f"testing {_param_display(section_name, param_entry)}", param=full_name, port=port)

    proc = None
    peer_procs = []
    peer_ports = []
    try:
        merged_env = {**(section_env or {}), **(param_entry.get("env") or {})} or None
        proc = start_vllm_serve(
            model, baseline_args + extra, port,
            log_prefix=f"{section_name}/{pkey}", use_baseline_args=False,
            env=merged_env,
        )
        if param_entry.get("peers"):
            peer_procs, peer_ports = _common.start_vllm_serve_peers(
                model, baseline_args, param_entry["peers"], log_prefix=f"{section_name}/{pkey}"
            )
        if not wait_for_ready(port, timeout, host=host or "127.0.0.1"):
            stdout_log, _ = read_serve_logs(proc)
            return {"section": section_name, "param": full_name, "test_value": tv,
                    "status": "FAIL", "notes": f"health timeout: {stdout_log[-500:]}"}
        for i, pp_port in enumerate(peer_ports if param_entry.get("peers") else []):
            if not wait_for_ready(pp_port, timeout, host=host or "127.0.0.1"):
                return {"section": section_name, "param": full_name, "test_value": tv,
                        "status": "FAIL", "notes": f"peer{i} health timeout"}

        served_model = _get_served_model(baseline)
        _rt = param_entry.get("request_type")
        if _rt == "tokens_only":
            print(" -------------------Warning: tokens_only request type is deprecated and may be removed in future. Please switch to using a normal completion request and ignore the text output.")
            ok, err = _common.send_tokens_only_request(served_model, port, host=host or "127.0.0.1")
        elif _rt == "multimodal_image":
            ok, err = _common.send_multimodal_image_request(served_model, port, host=host or "127.0.0.1")
        else:
            ok, err = send_completion_request(served_model, port, host=host or "127.0.0.1")
        result = {"section": section_name, "param": full_name, "test_value": tv,
                  "status": "PASS" if ok else "FAIL", "notes": "" if ok else err}

        if ok and bench:
            try:
                bench_log_dir = _common.LOG_DIR / "bench" / section_name
                bench_log_dir.mkdir(parents=True, exist_ok=True)
                bench_endpoint = "/v1/chat/completions" if _rt == "multimodal_image" else "/v1/completions"
                bench_tokenizer = model if _rt == "tokens_only" else None
                raw = run_bench(model, port, bench_num_prompts, bench_concurrency,
                                _common.LOG_DIR, log_name=f"{section_name}/{pkey}",
                                endpoint=bench_endpoint, tokenizer=bench_tokenizer)
                result["bench"] = extract_metrics(raw)
            except Exception as be:
                result["bench_error"] = str(be)

        if ok and accuracy and baseline_outputs is not None and _rt not in ("tokens_only", "multimodal_image"):
            try:
                a_ok, test_outputs, a_err = send_accuracy_request(served_model, port, host=host or "127.0.0.1")
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
        return {"section": section_name, "param": full_name, "test_value": tv,
                "status": "FAIL", "notes": f"exception: {e}"}
    finally:
        for pp in peer_procs:
            stop_vllm_serve(pp)
        if proc is not None:
            stop_vllm_serve(proc)


# ---------------------------------------------------------------------------
# Iteration
# ---------------------------------------------------------------------------

def _iter_params(section_data: list[dict], filter_param: str | None, filter_test_value=None):
    parent_filter, subfield_filter = _parse_param_filter(filter_param)
    for p in section_data:
        if "subfields" in p:
            parent_cli = p["name"]
            if parent_filter is not None and parent_cli != parent_filter:
                continue
            for sf in p["subfields"]:
                if subfield_filter is not None and sf["name"] != subfield_filter:
                    continue
                entry = {"name": parent_cli, "test_value": None, "subfields": [sf]}
                if filter_test_value is None or str(sf.get("test_value")).lower() == str(filter_test_value).lower():
                    yield entry
        else:
            if parent_filter is None or p["name"] == parent_filter:
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

    _common.LOG_DIR = Path(args.log_path).resolve()

    # --rerun-failed mode
    if args.rerun_failed:
        summary_path = Path(args.rerun_failed).resolve()
        if not summary_path.exists():
            sys.exit(f"Error: summary file not found: {summary_path}")
        data = _json.loads(summary_path.read_text(encoding="utf-8"))
        # support flat array of results or array of run summaries
        if isinstance(data, list) and data and "results" in data[0]:
            all_results = data[-1]["results"]
        else:
            all_results = data
        failed = [r for r in all_results if r.get("status") == "FAIL"]
        if not failed:
            print_json({"status": "ok", "message": "no failed cases found"})
            return
        emit_progress("rerun", f"re-running {len(failed)} failed case(s)")

        yaml_path = Path(args.params_yaml) if args.params_yaml else None
        data_yaml = load_simple_params_yaml(yaml_path)
        sections = {k: v for k, v in data_yaml.items() if k != "meta"}

        results = []
        results_dir = _common.LOG_DIR / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        interrupted = False

        def _sigint_handler(sig, frame):
            nonlocal interrupted
            if interrupted:
                sys.exit(1)
            interrupted = True
            emit_progress("interrupt", "Ctrl+C received, finishing current param and saving results...")

        prev_handler = signal.signal(signal.SIGINT, _sigint_handler)

        try:
            for r in failed:
                if interrupted:
                    break
                sname = r["section"]
                param_name = r["param"]
                test_value = r.get("test_value")
                if sname not in sections:
                    continue
                sec = sections[sname]
                tv_filter = str(test_value).lower() if test_value is not None else None
                # strip subfield suffix for parent filter
                parent_filter = param_name.split(".")[0] if "." in param_name else param_name
                entries = list(_iter_params(sec["params"], parent_filter, tv_filter))
                if not entries:
                    continue
                baseline = sec["baseline"]
                for entry in entries:
                    if interrupted:
                        break
                    port = args.port or find_free_port()
                    result = test_param(sname, entry, baseline, args.host, port, args.timeout,
                                        bench=args.bench, bench_num_prompts=args.bench_num_prompts,
                                        bench_concurrency=args.bench_concurrency,
                                        section_env=sec.get("env"))
                    results.append(result)
                    emit_progress("result", f"{_param_display(sname, entry)}: {result['status']}")
                    _upsert_summary(summary_path, result)
        finally:
            signal.signal(signal.SIGINT, prev_handler)

        passed = sum(1 for r in results if r["status"] == "PASS")
        failed_count = sum(1 for r in results if r["status"] == "FAIL")
        print_json({"status": "interrupted" if interrupted else "ok",
                    "tested": len(results), "passed": passed,
                    "failed": failed_count, "results": results, "timestamp": now_utc()})
        return

    if not args.nodes:
        parser.error("--nodes is required (choices: all, single) unless using --rerun-failed")
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
    results_dir = _common.LOG_DIR / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    summary_file = results_dir / "summary.json"

    interrupted = False

    def _sigint_handler(sig, frame):
        nonlocal interrupted
        if interrupted:
            sys.exit(1)
        interrupted = True
        emit_progress("interrupt", "Ctrl+C received, finishing current param and saving results...")

    prev_handler = signal.signal(signal.SIGINT, _sigint_handler)

    try:
        for sname, sec in sections_to_test.items():
            if interrupted:
                break
            baseline = sec["baseline"]
            params = list(_iter_params(sec["params"], args.param, args.test_value))
            emit_progress("section", f"testing {sname} ({len(params)} entries)")

            baseline_outputs = None
            if args.accuracy:
                baseline_outputs = _collect_baseline_outputs(sname, baseline, args.host, args.timeout)
                if baseline_outputs is None:
                    emit_progress("accuracy", f"failed to collect baseline outputs for {sname}, skipping accuracy")

            for entry in params:
                if interrupted:
                    break
                port = args.port or find_free_port()
                result = test_param(sname, entry, baseline, args.host, port, args.timeout,
                                    bench=args.bench, bench_num_prompts=args.bench_num_prompts,
                                    bench_concurrency=args.bench_concurrency,
                                    accuracy=args.accuracy, baseline_outputs=baseline_outputs,
                                    section_env=sec.get("env"))
                results.append(result)
                emit_progress("result", f"{_param_display(sname, entry)}: {result['status']}")

                # Upsert this result into summary.json immediately
                _upsert_summary(summary_file, result)
    finally:
        signal.signal(signal.SIGINT, prev_handler)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    summary = {"status": "interrupted" if interrupted else "ok",
               "tested": len(results), "passed": passed,
               "failed": failed, "skipped": skipped, "results": results,
               "timestamp": now_utc()}

    print_json(summary)


if __name__ == "__main__":
    main()
