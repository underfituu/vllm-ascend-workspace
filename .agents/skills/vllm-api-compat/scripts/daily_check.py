#!/usr/bin/env python3
"""Daily routine: poll vllm-project/vllm PRs, detect new params, test, auto-fix.

Usage:
    GITHUB_TOKEN=ghp_... python3 daily_check.py --model <path>
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    DAILY_DIR,
    ROOT,
    emit_progress,
    load_params_yaml,
    now_utc,
    print_json,
    save_params_yaml,
)

GITHUB_API = "https://api.github.com"
UPSTREAM_REPO = "vllm-project/vllm"
PARAM_SOURCE_FILES = {"vllm/entrypoints/cli/serve.py", "vllm/config.py"}

# Patterns that indicate an Ascend-specific failure
ASCEND_ERROR_PATTERNS = ("NotImplementedError", "AscendError", "npu", "torch_npu", "cann")


def _gh_get(path: str, token: str) -> dict | list:
    url = f"{GITHUB_API}/{path.lstrip('/')}"
    req = Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        resp = urlopen(req, timeout=30)
        return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        raise RuntimeError(f"GitHub API error {e.code} for {url}: {e.reason}")
    except URLError as e:
        raise RuntimeError(f"GitHub API connection error for {url}: {e}")


def load_daily_state() -> dict:
    state_file = DAILY_DIR / "state.json"
    if state_file.exists():
        return json.loads(state_file.read_text(encoding="utf-8"))
    return {"last_pr_number": 0, "last_run": None}


def save_daily_state(state: dict) -> None:
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    (DAILY_DIR / "state.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _infer_param_type(diff_context: str) -> str:
    if 'action="store_true"' in diff_context or "action='store_true'" in diff_context:
        return "bool_flag"
    if "choices=" in diff_context:
        return "Enum"
    if "type=int" in diff_context:
        return "int"
    if "type=float" in diff_context:
        return "float"
    return "str"


def _infer_test_value(param_type: str, diff_context: str) -> str | None:
    if param_type == "bool_flag":
        return None
    if param_type == "Enum":
        m = re.search(r"choices=\[([^\]]+)\]", diff_context)
        if m:
            first = m.group(1).split(",")[0].strip().strip("'\"")
            return first
    m = re.search(r'default=([^,\)]+)', diff_context)
    if m:
        val = m.group(1).strip().strip("'\"")
        if val not in ("None", "none", ""):
            return val
    return None


def _infer_section(diff_context: str) -> str:
    """Guess which config section a new param belongs to from surrounding diff."""
    section_hints = {
        "ModelConfig": ["ModelConfig", "model_config", "dtype", "quantization", "max_model_len"],
        "ParallelConfig": ["ParallelConfig", "tensor_parallel", "data_parallel", "pipeline_parallel"],
        "CacheConfig": ["CacheConfig", "gpu_memory_utilization", "kv_cache", "block_size"],
        "SchedulerConfig": ["SchedulerConfig", "max_num_seqs", "chunked_prefill"],
        "LoadConfig": ["LoadConfig", "load_format", "download_dir"],
        "Frontend": ["api_key", "cors", "ssl", "uvicorn"],
        "LoRAConfig": ["LoRAConfig", "lora", "max_lora"],
        "MultiModalConfig": ["MultiModalConfig", "mm_", "multimodal"],
        "ObservabilityConfig": ["ObservabilityConfig", "otlp", "metrics"],
        "CompilationConfig": ["CompilationConfig", "cudagraph", "compilation"],
        "KernelConfig": ["KernelConfig", "linear_backend", "moe_backend"],
    }
    for section, hints in section_hints.items():
        for hint in hints:
            if hint in diff_context:
                return section
    return "Frontend"  # fallback


def detect_new_params(token: str, last_pr_number: int) -> tuple[list[dict], int]:
    """Scan recent merged PRs for new serve parameters.

    Returns (new_param_entries, highest_pr_number_seen).
    """
    emit_progress("pr_poll", f"fetching PRs newer than #{last_pr_number}")

    prs = _gh_get(
        f"repos/{UPSTREAM_REPO}/pulls?state=closed&per_page=100&sort=updated&direction=desc",
        token,
    )

    new_params = []
    highest_seen = last_pr_number

    for pr in prs:
        pr_number = pr.get("number", 0)
        if pr_number <= last_pr_number:
            continue
        if pr.get("merged_at") is None:
            continue

        highest_seen = max(highest_seen, pr_number)

        files = _gh_get(f"repos/{UPSTREAM_REPO}/pulls/{pr_number}/files", token)
        relevant_files = [f for f in files if f.get("filename") in PARAM_SOURCE_FILES]
        if not relevant_files:
            continue

        emit_progress("pr_scan", f"scanning PR #{pr_number}: {pr.get('title', '')}")

        for file_info in relevant_files:
            patch = file_info.get("patch", "")
            for line in patch.splitlines():
                if not line.startswith("+"):
                    continue
                m = re.search(r'add_argument\(["\'](-{1,2}[\w-]+)["\']', line)
                if not m:
                    continue
                cli_flag = m.group(1)
                param_name = cli_flag.lstrip("-").replace("-", "_")
                param_type = _infer_param_type(line)
                test_value = _infer_test_value(param_type, line)
                section = _infer_section(patch)

                new_params.append({
                    "name": param_name,
                    "cli": cli_flag,
                    "type": param_type,
                    "test_value": test_value,
                    "status": "UNKNOWN",
                    "last_tested": None,
                    "notes": f"detected from PR #{pr_number}",
                    "source_pr": pr_number,
                    "section": section,
                })

    return new_params, highest_seen


def add_new_params_to_yaml(data: dict, new_params: list[dict]) -> int:
    """Append new params to params.yaml sections. Returns count added."""
    sections = data.setdefault("sections", {})
    added = 0

    for entry in new_params:
        section_name = entry.pop("section")
        section = sections.setdefault(section_name, {"params": []})
        existing_flags = {p.get("cli") for p in section.get("params", [])}
        if entry["cli"] not in existing_flags:
            section.setdefault("params", []).append(entry)
            added += 1
            emit_progress("param_added", f"added {entry['cli']} to {section_name}")

    return added


def run_cli_all(model: str) -> dict:
    """Run cli.py --nodes all and return its parsed JSON output."""
    cli_script = Path(__file__).resolve().parent / "cli.py"
    result = subprocess.run(
        [sys.executable, str(cli_script), "--model", model, "--nodes", "all"],
        capture_output=True,
        text=True,
    )
    if not result.stdout.strip():
        raise RuntimeError(
            f"cli.py produced no output (rc={result.returncode}):\n{result.stderr[:1000]}"
        )
    return json.loads(result.stdout)


def run_cli_single(model: str, section: str, param_name: str) -> dict:
    """Re-run cli.py for a single section to verify a fix."""
    cli_script = Path(__file__).resolve().parent / "cli.py"
    result = subprocess.run(
        [sys.executable, str(cli_script), "--model", model, "--nodes", "single",
         "--section", section],
        capture_output=True,
        text=True,
    )
    if not result.stdout.strip():
        return {"status": "failed", "results": []}
    return json.loads(result.stdout)


def is_ascend_error(notes: str) -> bool:
    return any(p in notes for p in ASCEND_ERROR_PATTERNS)


def write_fix_stub(param_name: str, section: str, error_notes: str) -> Path:
    """Write a fix stub markdown file for manual review."""
    fixes_dir = DAILY_DIR / "fixes"
    fixes_dir.mkdir(parents=True, exist_ok=True)
    stub_path = fixes_dir / f"{section}_{param_name}.md"
    stub_path.write_text(
        f"# Fix needed: {section}.{param_name}\n\n"
        f"**Error:**\n```\n{error_notes}\n```\n\n"
        f"**Suggested location:** `vllm-ascend/` — search for the parameter name "
        f"and add Ascend-specific handling.\n\n"
        f"**Generated:** {now_utc()}\n",
        encoding="utf-8",
    )
    return stub_path


def invoke_auto_commit_pr(today: str) -> str | None:
    """Invoke auto-commit-pr skill to commit and open a PR. Returns PR URL or None."""
    auto_commit_script = (
        ROOT / ".agents" / "skills" / "auto-commit-pr" / "scripts" / "auto_commit_pr.py"
    )
    if not auto_commit_script.exists():
        emit_progress("warn", "auto-commit-pr script not found, skipping PR creation")
        return None

    branch = f"fix/api-compat-{today}"
    message = f"[CI] fix API compat for new vllm params ({today})"

    # probe first
    subprocess.run(
        [sys.executable, str(auto_commit_script), "probe"],
        capture_output=True,
    )

    # commit
    commit_result = subprocess.run(
        [sys.executable, str(auto_commit_script), "commit",
         "--repo", "vllm-ascend",
         "--branch", branch,
         "--message", message],
        capture_output=True,
        text=True,
    )
    if commit_result.returncode != 0:
        emit_progress("warn", f"auto-commit failed: {commit_result.stderr[:300]}")
        return None

    # push
    subprocess.run(
        [sys.executable, str(auto_commit_script), "push",
         "--repo", "vllm-ascend"],
        capture_output=True,
    )

    # pr
    pr_result = subprocess.run(
        [sys.executable, str(auto_commit_script), "pr",
         "--repo", "vllm-ascend",
         "--title", message],
        capture_output=True,
        text=True,
    )
    if pr_result.stdout.strip():
        try:
            pr_data = json.loads(pr_result.stdout)
            return pr_data.get("html_url")
        except json.JSONDecodeError:
            pass
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily vLLM API compat check")
    parser.add_argument("--model", required=True, help="Model path for test runs")
    parser.add_argument("--dry-run", action="store_true",
                        help="Detect params and report without running tests")
    args = parser.parse_args()

    token = __import__("os").environ.get("GITHUB_TOKEN", "")
    if not token:
        sys.stderr.write("Error: GITHUB_TOKEN env var is required\n")
        sys.exit(1)

    state = load_daily_state()
    today = str(date.today())

    # 1. Detect new params from upstream PRs
    new_params, highest_pr = detect_new_params(token, state["last_pr_number"])
    emit_progress("detect", f"found {len(new_params)} new params from upstream PRs")

    data = load_params_yaml()
    added = add_new_params_to_yaml(data, new_params)
    if added:
        save_params_yaml(data)

    if args.dry_run:
        print_json({
            "status": "ok",
            "dry_run": True,
            "new_params_detected": len(new_params),
            "added_to_yaml": added,
            "timestamp": now_utc(),
        })
        return

    # 2. Run full test suite
    emit_progress("test_all", "running cli.py --nodes all")
    try:
        test_output = run_cli_all(args.model)
    except Exception as e:
        print_json({"status": "failed", "phase": "test_all", "error": str(e), "timestamp": now_utc()})
        sys.exit(1)

    failed_results = [r for r in test_output.get("results", []) if r["status"] == "FAIL"]

    # 3. Attempt fixes for Ascend-specific failures
    auto_fixed = 0
    for r in failed_results:
        if not is_ascend_error(r.get("notes", "")):
            continue
        emit_progress("fix_attempt", f"Ascend error in {r['section']}.{r['name']}")
        stub = write_fix_stub(r["name"], r["section"], r.get("notes", ""))
        emit_progress("fix_stub", f"wrote fix stub: {stub}")
        # Re-run single section to check if anything changed
        retest = run_cli_single(args.model, r["section"], r["name"])
        if any(
            x["name"] == r["name"] and x["status"] == "PASS"
            for x in retest.get("results", [])
        ):
            auto_fixed += 1

    # 4. Invoke auto-commit-pr if there are fix stubs to commit
    pr_url = None
    fixes_dir = DAILY_DIR / "fixes"
    if fixes_dir.exists() and any(fixes_dir.iterdir()):
        emit_progress("pr", "invoking auto-commit-pr")
        pr_url = invoke_auto_commit_pr(today)

    # 5. Update state
    state["last_pr_number"] = highest_pr
    state["last_run"] = now_utc()
    save_daily_state(state)

    print_json({
        "status": "ok",
        "new_params_detected": len(new_params),
        "tested": test_output.get("tested", 0),
        "passed": test_output.get("passed", 0),
        "failed": test_output.get("failed", 0),
        "auto_fixed": auto_fixed,
        "pr_url": pr_url,
        "timestamp": now_utc(),
    })


if __name__ == "__main__":
    main()
