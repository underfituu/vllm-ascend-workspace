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

import _common
from _common import (
    emit_progress,
    extract_metrics,
    find_free_port,
    now_utc,
    print_json,
    read_serve_logs,
    run_bench,
    start_vllm_serve,
    stop_vllm_serve,
    wait_for_ready,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Pressure test for vLLM serve")
    p.add_argument("--model", required=True, help="Model path or name")
    p.add_argument("--port", type=int, default=None, help="Port (auto-detect if omitted)")
    p.add_argument("--num-prompts", type=int, default=10, help="Number of prompts")
    p.add_argument("--concurrency", type=int, default=4, help="Max concurrency")
    p.add_argument("--timeout", type=int, default=180, help="Health-check timeout in seconds")
    p.add_argument("--extra-serve-args", nargs="*", default=[], help="Extra args for vllm serve")
    p.add_argument("--skip-serve", action="store_true", help="Skip starting vllm serve; connect to existing service on --port")
    p.add_argument("--log-path", default="./server-api-log", help="Root log dir; results/ and serve/ subdirs created inside")
    return p


def main() -> None:
    args = build_parser().parse_args()

    log_path = Path(args.log_path)
    _common.LOG_DIR = log_path

    port = args.port or find_free_port()
    proc = None

    try:
        emit_progress("start", f"starting pressure test: {args.model}")

        if args.skip_serve:
            emit_progress("skip_serve", f"skipping serve startup, using existing service on port {port}")
        else:
            proc = start_vllm_serve(args.model, args.extra_serve_args, port, log_prefix="bench")

            if not wait_for_ready(port, args.timeout):
                stdout_log, _ = read_serve_logs(proc)
                print_json({
                    "status": "failed",
                    "phase": "serve_start",
                    "error": f"health timeout ({args.timeout}s)",
                    "stdout_tail": stdout_log[-1000:] if stdout_log else "",
                    "timestamp": now_utc(),
                })
                sys.exit(1)

        emit_progress("serve_ready", "service is ready, starting bench")

        raw_result = run_bench(args.model, port, args.num_prompts, args.concurrency, log_path)
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
