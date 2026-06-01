#!/usr/bin/env python3
"""CLI test runner for vLLM serve API parameter compatibility.

Usage:
    python3 cli.py --model <path> --nodes all [--timeout 120]
    python3 cli.py --model <path> --nodes single --section ModelConfig
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure _common is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    build_extra_args,
    emit_progress,
    find_free_port,
    load_params_yaml,
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
    p.add_argument("--model", required=True, help="Model path or name for vllm serve")
    p.add_argument(
        "--nodes",
        required=True,
        choices=["all", "single"],
        help="'all' tests every section; 'single' tests one section",
    )
    p.add_argument(
        "--section",
        default=None,
        help="Section name to test (required when --nodes single)",
    )
    p.add_argument("--timeout", type=int, default=120, help="Health-check timeout in seconds")
    p.add_argument("--params-yaml", default=None, help="Override path to params.yaml")
    return p


def test_single_param(
    model: str,
    section_name: str,
    param_entry: dict,
    timeout: int,
) -> dict:
    """Run one parameter test. Returns a result dict."""
    name = param_entry.get("name", "unknown")
    cli_flag = param_entry.get("cli", "")

    if param_entry.get("status") == "SKIP":
        return {
            "section": section_name,
            "param": cli_flag,
            "name": name,
            "status": "SKIP",
            "notes": param_entry.get("notes", ""),
        }

    extra_args = build_extra_args(param_entry)
    if extra_args is None:
        return {
            "section": section_name,
            "param": cli_flag,
            "name": name,
            "status": "SKIP",
            "notes": "no safe test value",
        }

    port = find_free_port()
    emit_progress("test", f"testing {section_name}.{name}", param=cli_flag, port=port)

    proc = None
    try:
        proc = start_vllm_serve(model, extra_args, port, log_prefix=f"{section_name}_{name}")

        if not wait_for_ready(port, timeout):
            stdout_log, stderr_log = read_serve_logs(proc)
            error_tail = stderr_log[-500:] if stderr_log else stdout_log[-500:]
            return {
                "section": section_name,
                "param": cli_flag,
                "name": name,
                "status": "FAIL",
                "notes": f"health timeout ({timeout}s): {error_tail}",
            }

        # Use model basename as served model name for the request
        served_model = model.rstrip("/").split("/")[-1]
        ok, err = send_completion_request(served_model, port)
        if ok:
            return {
                "section": section_name,
                "param": cli_flag,
                "name": name,
                "status": "PASS",
                "notes": "",
            }
        else:
            return {
                "section": section_name,
                "param": cli_flag,
                "name": name,
                "status": "FAIL",
                "notes": err,
            }

    except Exception as e:
        return {
            "section": section_name,
            "param": cli_flag,
            "name": name,
            "status": "FAIL",
            "notes": f"exception: {e}",
        }
    finally:
        if proc is not None:
            stop_vllm_serve(proc)


def run_tests(
    model: str,
    sections_to_test: list[str],
    data: dict,
    timeout: int,
) -> list[dict]:
    """Run tests for all params in the given sections. Returns result list."""
    results = []
    sections = data.get("sections", {})

    for section_name in sections_to_test:
        section = sections.get(section_name)
        if section is None:
            emit_progress("warn", f"section {section_name} not found in params.yaml")
            continue

        params = section.get("params", [])
        emit_progress("section", f"testing section {section_name} ({len(params)} params)")

        for param_entry in params:
            result = test_single_param(model, section_name, param_entry, timeout)
            results.append(result)

            # Update param_entry in-place
            param_entry["status"] = result["status"]
            param_entry["last_tested"] = now_utc()
            if result["notes"]:
                param_entry["notes"] = result["notes"]

            status_icon = "PASS" if result["status"] == "PASS" else result["status"]
            emit_progress(
                "result",
                f"{section_name}.{param_entry.get('name', '?')}: {status_icon}",
            )

    return results


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.nodes == "single" and not args.section:
        parser.error("--section is required when --nodes is 'single'")

    # Load params.yaml
    if args.params_yaml:
        import _common
        _common.PARAMS_YAML = Path(args.params_yaml)

    data = load_params_yaml()
    sections = data.get("sections", {})

    if args.nodes == "all":
        sections_to_test = list(sections.keys())
    else:
        if args.section not in sections:
            sys.stderr.write(
                f"Error: section '{args.section}' not found. "
                f"Available: {', '.join(sections.keys())}\n"
            )
            sys.exit(1)
        sections_to_test = [args.section]

    emit_progress("start", f"testing {len(sections_to_test)} sections", model=args.model)

    results = run_tests(args.model, sections_to_test, data, args.timeout)

    # Update meta and save
    data.setdefault("meta", {})["last_updated"] = now_utc()
    save_params_yaml(data)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")

    print_json({
        "status": "ok",
        "tested": len(results),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "results": results,
        "timestamp": now_utc(),
    })


if __name__ == "__main__":
    main()
