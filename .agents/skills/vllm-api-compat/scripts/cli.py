#!/usr/bin/env python3
"""CLI test runner for vLLM serve API parameter compatibility.

Usage (legacy params.yaml):
    python3 cli.py --model <path> --nodes all [--timeout 120]
    python3 cli.py --model <path> --nodes single --section ModelConfig

Usage (params_simple.yaml):
    python3 cli.py --format simple --host <host> --port <port> --nodes all
    python3 cli.py --format simple --host <host> --port <port> --nodes single --section ModelConfig
    python3 cli.py --format simple --host <host> --port <port> --nodes single --section ModelConfig --param --aggregate-engine-logging
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    SIMPLE_PARAMS_YAML,
    build_extra_args,
    build_extra_args_simple,
    emit_progress,
    find_free_port,
    load_params_yaml,
    load_simple_params_yaml,
    now_utc,
    print_json,
    read_serve_logs,
    save_params_yaml,
    send_completion_request,
    start_vllm_serve,
    stop_vllm_serve,
    wait_for_ready,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Test vLLM serve CLI parameters for Ascend compatibility"
    )
    p.add_argument("--model", default=None, help="Model path (legacy format; simple format reads from baseline)")
    p.add_argument("--host", default=None, help="Host to pass to vllm serve (simple format)")
    p.add_argument("--port", type=int, default=None, help="Port override (both formats; default: auto)")
    p.add_argument("--nodes", required=True, choices=["all", "single"])
    p.add_argument("--section", default=None, help="Section name (required when --nodes single)")
    p.add_argument("--param", default=None, help="Single param name to test (simple format, e.g. --aggregate-engine-logging)")
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--params-yaml", default=None, help="Override path to params yaml")
    p.add_argument("--format", choices=["legacy", "simple"], default="legacy")
    p.add_argument("--log-path", default="./server-api-log",
                   help="Root log directory; results/ and serve/ subdirs created inside")
    return p


# ---------------------------------------------------------------------------
# Simple format runner
# ---------------------------------------------------------------------------

def _baseline_to_args(baseline: list[str], host: str | None) -> tuple[str, list[str]]:
    """Extract model and build the baseline arg list (no --port, injected by start_vllm_serve)."""
    model = baseline[0]
    args = []
    for item in baseline[1:]:
        args.extend(item.split())
    if host:
        args += ["--host", host]
    return model, args


def test_simple_param(
    section_name: str,
    param_entry: dict,
    baseline: list[str],
    host: str | None,
    port: int,
    timeout: int,
) -> dict:
    name = param_entry.get("name", "")
    extra = build_extra_args_simple(param_entry)
    model, baseline_args = _baseline_to_args(baseline, host)

    emit_progress("test", f"testing {section_name} {name}={param_entry.get('test_value')}", param=name, port=port)

    proc = None
    try:
        proc = start_vllm_serve(
            model,
            baseline_args + extra,
            port,
            log_prefix=f"{section_name}_{name.lstrip('-').replace('-','_')}_{param_entry.get('test_value')}",
            use_baseline_args=False,
        )
        if not wait_for_ready(port, timeout, host=host or "localhost"):
            _, stderr = read_serve_logs(proc)
            return {"section": section_name, "param": name, "test_value": param_entry.get("test_value"),
                    "status": "FAIL", "notes": f"health timeout: {stderr[-300:]}"}

        # Extract served model name from baseline args if present
        served_model = baseline[0].rstrip("/").split("/")[-1]
        for i, item in enumerate(baseline[1:], 1):
            if item == "--served-model-name" and i + 1 < len(baseline):
                served_model = baseline[i + 1]
                break
            if item.startswith("--served-model-name "):
                served_model = item.split(" ", 1)[1]
                break
        ok, err = send_completion_request(served_model, port, host=host or "localhost")
        return {"section": section_name, "param": name, "test_value": param_entry.get("test_value"),
                "status": "PASS" if ok else "FAIL", "notes": "" if ok else err}
    except Exception as e:
        return {"section": section_name, "param": name, "test_value": param_entry.get("test_value"),
                "status": "FAIL", "notes": f"exception: {e}"}
    finally:
        if proc is not None:
            stop_vllm_serve(proc)


def _iter_simple_params(section_data: list[dict], filter_param: str | None):
    """Yield param entries, optionally filtered to a single param name."""
    # Expand subfields into flat entries for independent testing
    for p in section_data:
        if "subfields" in p:
            parent_cli = p["name"]
            for sf in p["subfields"]:
                entry = {"name": parent_cli, "test_value": None,
                         "subfields": [sf]}
                if filter_param is None or parent_cli == filter_param:
                    yield entry
        else:
            if filter_param is None or p["name"] == filter_param:
                yield p


def run_simple(args: argparse.Namespace, data: dict) -> list[dict]:
    sections = {k: v for k, v in data.items() if k != "meta"}
    if args.nodes == "single":
        if args.section not in sections:
            sys.stderr.write(f"Error: section '{args.section}' not found. Available: {', '.join(sections)}\n")
            sys.exit(1)
        sections_to_test = {args.section: sections[args.section]}
    else:
        sections_to_test = sections

    results = []
    for sname, sec in sections_to_test.items():
        baseline = sec["baseline"]
        params = list(_iter_simple_params(sec["params"], args.param))
        emit_progress("section", f"testing {sname} ({len(params)} entries)")
        for entry in params:
            port = args.port or find_free_port()
            result = test_simple_param(sname, entry, baseline, args.host, port, args.timeout)
            results.append(result)
            emit_progress("result", f"{sname} {result['param']}={result['test_value']}: {result['status']}")
    return results


# ---------------------------------------------------------------------------
# Legacy format runner (unchanged logic)
# ---------------------------------------------------------------------------

def test_legacy_param(model: str, section_name: str, param_entry: dict, timeout: int) -> dict:
    name = param_entry.get("name", "unknown")
    cli_flag = param_entry.get("cli", "")
    if param_entry.get("status") == "SKIP":
        return {"section": section_name, "param": cli_flag, "name": name,
                "status": "SKIP", "notes": param_entry.get("notes", "")}
    extra_args = build_extra_args(param_entry)
    if extra_args is None:
        return {"section": section_name, "param": cli_flag, "name": name,
                "status": "SKIP", "notes": "no safe test value"}
    port = find_free_port()
    emit_progress("test", f"testing {section_name}.{name}", param=cli_flag, port=port)
    proc = None
    try:
        proc = start_vllm_serve(model, extra_args, port, log_prefix=f"{section_name}_{name}")
        if not wait_for_ready(port, timeout):
            _, stderr = read_serve_logs(proc)
            return {"section": section_name, "param": cli_flag, "name": name,
                    "status": "FAIL", "notes": f"health timeout ({timeout}s): {stderr[-500:]}"}
        served_model = model.rstrip("/").split("/")[-1]
        ok, err = send_completion_request(served_model, port)
        return {"section": section_name, "param": cli_flag, "name": name,
                "status": "PASS" if ok else "FAIL", "notes": "" if ok else err}
    except Exception as e:
        return {"section": section_name, "param": cli_flag, "name": name,
                "status": "FAIL", "notes": f"exception: {e}"}
    finally:
        if proc is not None:
            stop_vllm_serve(proc)


def run_legacy(args: argparse.Namespace, data: dict) -> list[dict]:
    sections = data.get("sections", {})
    if args.nodes == "all":
        sections_to_test = list(sections.keys())
    else:
        if args.section not in sections:
            sys.stderr.write(f"Error: section '{args.section}' not found. Available: {', '.join(sections)}\n")
            sys.exit(1)
        sections_to_test = [args.section]

    results = []
    for section_name in sections_to_test:
        section = sections[section_name]
        params = section.get("params", [])
        emit_progress("section", f"testing section {section_name} ({len(params)} params)")
        for param_entry in params:
            result = test_legacy_param(args.model, section_name, param_entry, args.timeout)
            results.append(result)
            param_entry["status"] = result["status"]
            param_entry["last_tested"] = now_utc()
            if result["notes"]:
                param_entry["notes"] = result["notes"]
            emit_progress("result", f"{section_name}.{param_entry.get('name','?')}: {result['status']}")
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.nodes == "single" and not args.section:
        parser.error("--section is required when --nodes is single")

    # Set global log directory
    import _common
    _common.LOG_DIR = Path(args.log_path).resolve()
    results_dir = _common.LOG_DIR / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    if args.format == "simple":
        yaml_path = Path(args.params_yaml) if args.params_yaml else None
        data = load_simple_params_yaml(yaml_path)
        emit_progress("start", f"simple format, sections={[k for k in data if k!='meta']}")
        results = run_simple(args, data)
    else:
        if not args.model:
            parser.error("--model is required for legacy format")
        if args.params_yaml:
            import _common
            _common.PARAMS_YAML = Path(args.params_yaml)
        data = load_params_yaml()
        emit_progress("start", f"testing sections", model=args.model)
        results = run_legacy(args, data)
        data.setdefault("meta", {})["last_updated"] = now_utc()
        save_params_yaml(data)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    summary = {"status": "ok", "tested": len(results), "passed": passed,
               "failed": failed, "skipped": skipped, "results": results,
               "timestamp": now_utc()}

    # Write summary to results dir
    ts = now_utc().replace(":", "-")
    (results_dir / f"summary_{ts}.json").write_text(
        __import__("json").dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print_json(summary)


if __name__ == "__main__":
    main()
