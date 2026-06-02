#!/usr/bin/env python3
"""Shared utilities for vllm-api-compat scripts."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]

STATE_DIR = ROOT / ".vaws-local" / "vllm-api-compat"
PARAMS_YAML = STATE_DIR / "params.yaml"
RESULTS_DIR = STATE_DIR / "results"
DAILY_DIR = STATE_DIR / "daily"

# Overridable log root; split into results/ (test outcome) and serve/ (vllm output)
LOG_DIR = Path("./server-api-log")
PROGRESS_SENTINEL = "__VAWS_VLLM_API_COMPAT_PROGRESS__="

# Baseline args always added to vllm serve (keep test fast and low-memory)
BASELINE_ARGS = ["--max-model-len", "512", "--enforce-eager"]

SIMPLE_PARAMS_YAML = ROOT / ".agents" / "skills" / "vllm-api-compat" / "references" / "params_simple.yaml"


def load_simple_params_yaml(path: Path | None = None) -> dict[str, Any]:
    yaml_mod = _try_yaml_import()
    if yaml_mod is None:
        raise RuntimeError("PyYAML is required: pip install pyyaml")
    p = path or SIMPLE_PARAMS_YAML
    with open(p, "r", encoding="utf-8") as f:
        return yaml_mod.safe_load(f)


def build_extra_args_simple(param_entry: dict[str, Any]) -> list[str]:
    """Build CLI args from a params_simple.yaml entry {name, test_value}.

    - bool_flag with test_value=True  → ["--flag"]
    - bool_flag with test_value=False → [] (omit; absence is the false state)
    - name starts with '--no-'        → ["--no-flag"] (always test_value=True)
    - json_config (has subfields)     → build --flag '{"sub": val, ...}'
    """
    import json as _json
    name = param_entry.get("name", "")
    test_value = param_entry.get("test_value")
    subfields = param_entry.get("subfields")

    if subfields is not None:
        # json_config: compose a JSON object from all subfields
        obj = {}
        for sf in subfields:
            sfname = sf["name"]
            sfval = sf["test_value"]
            # handle dotted keys: "pass_config.fuse_norm_quant" → nested dict
            parts = sfname.split(".")
            d = obj
            for part in parts[:-1]:
                d = d.setdefault(part, {})
            d[parts[-1]] = sfval
        return [name, _json.dumps(obj)]

    if isinstance(test_value, bool):
        return [name] if test_value else []

    return [name, str(test_value)]


# ---------------------------------------------------------------------------
# Progress / output helpers
# ---------------------------------------------------------------------------

def emit_progress(phase: str, message: str, **extra: Any) -> None:
    payload: dict[str, Any] = {"phase": phase, "message": message}
    payload.update({k: v for k, v in extra.items() if v is not None})
    sys.stderr.write(PROGRESS_SENTINEL + json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stderr.flush()


def print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def now_utc() -> str:
    from datetime import datetime, timezone
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


# ---------------------------------------------------------------------------
# YAML config management
# ---------------------------------------------------------------------------

def _try_yaml_import():
    try:
        import yaml
        return yaml
    except ImportError:
        return None


def load_params_yaml() -> dict[str, Any]:
    """Load the parameter registry YAML. Raises FileNotFoundError if missing."""
    yaml_mod = _try_yaml_import()
    if yaml_mod is None:
        raise RuntimeError("PyYAML is required: pip install pyyaml")
    if not PARAMS_YAML.exists():
        raise FileNotFoundError(
            f"params.yaml not found at {PARAMS_YAML}. "
            "Run the seed script first or create it manually."
        )
    with open(PARAMS_YAML, "r", encoding="utf-8") as f:
        return yaml_mod.safe_load(f)


def save_params_yaml(data: dict[str, Any]) -> None:
    """Write the parameter registry YAML back to disk."""
    yaml_mod = _try_yaml_import()
    if yaml_mod is None:
        raise RuntimeError("PyYAML is required: pip install pyyaml")
    PARAMS_YAML.parent.mkdir(parents=True, exist_ok=True)
    with open(PARAMS_YAML, "w", encoding="utf-8") as f:
        yaml_mod.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


# ---------------------------------------------------------------------------
# Network helpers
# ---------------------------------------------------------------------------

def find_free_port() -> int:
    """Bind to port 0 and return the OS-assigned free port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


# ---------------------------------------------------------------------------
# Local vllm serve lifecycle
# ---------------------------------------------------------------------------

def start_vllm_serve(
    model: str,
    extra_args: list[str],
    port: int,
    log_prefix: str = "serve",
    use_baseline_args: bool = True,
) -> subprocess.Popen:
    """Launch a local vllm serve process.

    Returns the Popen handle. stdout/stderr are written to log files under
    RESULTS_DIR so the caller can inspect them on failure.
    """
    serve_dir = LOG_DIR / "serve"
    serve_dir.mkdir(parents=True, exist_ok=True)
    ts = now_utc().replace(":", "-")
    log_stdout = serve_dir / f"{log_prefix}_{ts}_stdout.log"
    log_stderr = serve_dir / f"{log_prefix}_{ts}_stderr.log"

    baseline = BASELINE_ARGS if use_baseline_args else []
    cmd = ["vllm", "serve", model, "--port", str(port)] + baseline + extra_args

    emit_progress("serve_start", f"starting: {' '.join(cmd)}")

    f_out = open(log_stdout, "w", encoding="utf-8")
    f_err = open(log_stderr, "w", encoding="utf-8")

    proc = subprocess.Popen(
        cmd,
        stdout=f_out,
        stderr=f_err,
        preexec_fn=os.setsid,  # new process group for clean kill
    )

    # Attach log file handles so we can close them later
    proc._log_stdout = f_out  # type: ignore[attr-defined]
    proc._log_stderr = f_err  # type: ignore[attr-defined]
    proc._log_stdout_path = log_stdout  # type: ignore[attr-defined]
    proc._log_stderr_path = log_stderr  # type: ignore[attr-defined]

    return proc


def wait_for_ready(port: int, timeout: int = 120, host: str = "localhost") -> bool:
    """Poll http://<host>:<port>/health every 2s until 200 or timeout."""
    from urllib.request import urlopen
    from urllib.error import URLError

    url = f"http://{host}:{port}/health"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = urlopen(url, timeout=5)
            if resp.status == 200:
                return True
        except (URLError, OSError, ConnectionError):
            pass
        time.sleep(2)
    return False


def send_completion_request(model: str, port: int, host: str = "localhost") -> tuple[bool, str]:
    """POST a minimal completion request and check for valid response."""
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError

    url = f"http://{host}:{port}/v1/completions"
    payload = json.dumps({
        "model": model,
        "prompt": "Hello",
        "max_tokens": 1,
    }).encode("utf-8")

    req = Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        resp = urlopen(req, timeout=30)
        body = resp.read().decode("utf-8")
        data = json.loads(body)
        if "choices" in data:
            return True, ""
        return False, f"response missing 'choices': {body[:200]}"
    except HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except (URLError, OSError, ConnectionError) as e:
        return False, f"connection error: {e}"
    except json.JSONDecodeError:
        return False, "response is not valid JSON"


def stop_vllm_serve(proc: subprocess.Popen) -> None:
    """Stop a vllm serve process: SIGTERM → 10s wait → SIGKILL."""
    if proc.poll() is not None:
        _close_log_handles(proc)
        return

    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        _close_log_handles(proc)
        return

    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        proc.wait(timeout=5)

    _close_log_handles(proc)
    _wait_descendants_gone(proc.pid)


def _wait_npu_memory_free(timeout: int = 60) -> None:
    """Wait until all ASCEND_RT_VISIBLE_DEVICES show no running processes."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            out = subprocess.check_output(
                ["npu-smi", "info"], stderr=subprocess.DEVNULL, text=True
            )
            if out.count("No running processes") >= 4:
                return
        except (subprocess.CalledProcessError, FileNotFoundError):
            return  # npu-smi not available, skip
        time.sleep(3)


def _wait_descendants_gone(pid: int, timeout: int = 60) -> None:
    """Wait until all descendant processes are gone, then add extra grace time."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            out = subprocess.check_output(
                ["pgrep", "-g", str(pid)], stderr=subprocess.DEVNULL
            )
            if not out.strip():
                break
        except subprocess.CalledProcessError:
            break
        time.sleep(2)
    # Extra grace for HCCL/NPU ports and HBM to release
    time.sleep(15)
    # Poll NPU memory until all devices show near-zero usage
    _wait_npu_memory_free(timeout=60)


def _close_log_handles(proc: subprocess.Popen) -> None:
    for attr in ("_log_stdout", "_log_stderr"):
        fh = getattr(proc, attr, None)
        if fh and not fh.closed:
            fh.close()


def read_serve_logs(proc: subprocess.Popen) -> tuple[str, str]:
    """Read the stdout and stderr log files of a serve process."""
    stdout_path = getattr(proc, "_log_stdout_path", None)
    stderr_path = getattr(proc, "_log_stderr_path", None)
    stdout_content = ""
    stderr_content = ""
    if stdout_path and Path(stdout_path).exists():
        stdout_content = Path(stdout_path).read_text(encoding="utf-8", errors="replace")
    if stderr_path and Path(stderr_path).exists():
        stderr_content = Path(stderr_path).read_text(encoding="utf-8", errors="replace")
    return stdout_content, stderr_content


# ---------------------------------------------------------------------------
# Parameter test helpers
# ---------------------------------------------------------------------------

def build_extra_args(param_entry: dict[str, Any]) -> list[str] | None:
    """Build the CLI args list for a single parameter entry.

    Returns None if the param cannot be tested (no test_value and not a bool flag).
    """
    cli_flag = param_entry.get("cli", "")
    param_type = param_entry.get("type", "")
    test_value = param_entry.get("test_value")

    if param_type == "positional":
        return None  # positional args are part of the baseline

    if param_type == "bool_flag":
        return [cli_flag]

    if test_value is not None:
        return [cli_flag, str(test_value)]

    return None  # cannot test without a value
