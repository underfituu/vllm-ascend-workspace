#!/usr/bin/env python3
"""Pressure test for vLLM serve on Ascend.

Starts vllm serve locally, runs `vllm bench serve`, parses metrics.

Usage:
    python3 bench_test.py --model <path> [--num-prompts 100] [--concurrency 4]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    emit_progress,
    find_free_port,
    now_utc,
    print_json,
    read_serve_logs,
    start_vllm_serve,
    stop_vllm_serve,
    wait_for_ready,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Pressure test for vLLM serve")
    p.add_argument("--model", required=True, help="Model path or name")
    p.add_argument("--port", type=int, default=None, help="Port (auto-detect if omitted)")
    p.add_argument("--num-prompts", type=int, default=100, help="Number of prompts")
    p.add_argument("--concurrency", type=int, default=4, help="Max concurrency")
    p.add_argument("--timeout", type=int, default=180, help="Health-check timeout in seconds")
    p.add_argument("--extra-serve-args", nargs="*", default=[], help="Extra args for vllm serve")
    return p


def run_bench(
    model: str,
    port: int,
    num_prompts: int,
    concurrency: int,
) -> dict:
    """Run vllm bench serve and parse the result JSON."""
    served_model = model.rstrip("/").split("/")[-1]

    cmd = [
        "vllm", "bench", "serve",
        "--backend", "openai",
        "--endpoint", "/v1/completions",
        "--host", "localhost",
        "--port", str(port),
        "--model", served_model,
        "--num-prompts", str(num_prompts),
        "--max-concurrency", str(concurrency),
    ]

    emit_progress("bench_run", f"running: {' '.join(cmd)}")

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if proc.returncode != 0:
        raise RuntimeError(
            f"vllm bench serve failed (rc={proc.returncode}):\n"
            f"stdout: {proc.stdout[-2000:]}\n"
            f"stderr: {proc.stderr[-2000:]}"
        )

    # Parse last JSON object from stdout (same pattern as bench_run.py)
    stdout = proc.stdout
    json_start = stdout.rfind("\n{")
    if json_start == -1:
        json_start = 0 if stdout.startswith("{") else -1
    else:
        json_start += 1

    if json_start == -1:
        raise RuntimeError(
            f"cannot find JSON result in bench output:\n{stdout[-2000:]}"
        )

    try:
        return json.loads(stdout[json_start:])
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"cannot parse bench result JSON: {e}\n{stdout[json_start:json_start+500]}"
        )


def extract_metrics(raw_result: dict) -> dict:
    """Extract key metrics from vllm bench serve result."""
    metrics = {}
    for key in (
        "output_throughput", "mean_tpot_ms", "mean_ttft_ms",
        "median_tpot_ms", "median_ttft_ms", "request_throughput",
        "mean_e2el_ms", "median_e2el_ms", "total_input", "total_output",
    ):
        if key in raw_result:
            val = raw_result[key]
            if isinstance(val, str):
                try:
                    val = float(val)
                except ValueError:
                    pass
            metrics[key] = val
    return metrics


def main() -> None:
    args = build_parser().parse_args()

    port = args.port or find_free_port()
    proc = None

    try:
        emit_progress("start", f"starting pressure test: {args.model}")
        proc = start_vllm_serve(args.model, args.extra_serve_args, port, log_prefix="bench")

        if not wait_for_ready(port, args.timeout):
            stdout_log, stderr_log = read_serve_logs(proc)
            print_json({
                "status": "failed",
                "phase": "serve_start",
                "error": f"health timeout ({args.timeout}s)",
                "stderr_tail": stderr_log[-1000:] if stderr_log else "",
                "timestamp": now_utc(),
            })
            sys.exit(1)

        emit_progress("serve_ready", "service is ready, starting bench")

        raw_result = run_bench(args.model, port, args.num_prompts, args.concurrency)
        metrics = extract_metrics(raw_result)

        print_json({
            "status": "ok",
            "model": args.model,
            "num_prompts": args.num_prompts,
            "concurrency": args.concurrency,
            "metrics": metrics,
            "timestamp": now_utc(),
        })

    except Exception as e:
        print_json({
            "status": "failed",
            "phase": "bench_run",
            "error": str(e),
            "timestamp": now_utc(),
        })
        sys.exit(1)

    finally:
        if proc is not None:
            stop_vllm_serve(proc)
            emit_progress("cleanup", "service stopped")


if __name__ == "__main__":
    main()
