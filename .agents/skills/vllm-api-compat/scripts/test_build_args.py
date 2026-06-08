#!/usr/bin/env python3
"""Quick test for build_extra_args_simple with prerequisite CLI args in subfields."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import build_extra_args_simple, load_simple_params_yaml

# --- unit tests ---

def check(label, got, expected):
    ok = got == expected
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        print(f"       got:      {got}")
        print(f"       expected: {expected}")

# 1. Normal bool flag true
check("bool true",
      build_extra_args_simple({"name": "--disable-log-stats", "test_value": True}),
      ["--disable-log-stats"])

# 2. Normal bool flag false → empty
check("bool false",
      build_extra_args_simple({"name": "--disable-log-stats", "test_value": False}),
      [])

# 3. Non-bool value
check("string value",
      build_extra_args_simple({"name": "--guided-decoding-backend", "test_value": "xgrammar"}),
      ["--guided-decoding-backend", "xgrammar"])

# 4. Subfields without prerequisite (normal JSON config)
check("subfields no prereq",
      build_extra_args_simple({"name": "--kv-events-config", "subfields": [
          {"name": "enable_kv_cache_events", "test_value": True}
      ]}),
      ["--kv-events-config", '{"enable_kv_cache_events": true}'])

# 5. Subfields with deps (the new feature)
check("subfields with deps",
      build_extra_args_simple({"name": "--structured-outputs-config", "subfields": [
          {"name": "disable_any_whitespace", "test_value": True, "deps": {"backend": "xgrammar"}},
      ]}),
      ["--structured-outputs-config", '{"backend": "xgrammar", "disable_any_whitespace": true}'])

# 6. Dotted subfield key
check("dotted subfield",
      build_extra_args_simple({"name": "--compilation-config", "subfields": [
          {"name": "pass_config.fuse_norm_quant", "test_value": True}
      ]}),
      ["--compilation-config", '{"pass_config": {"fuse_norm_quant": true}}'])

# --- load from actual params_simple.yaml and find structured-outputs-config ---
print()
print("--- params_simple.yaml: --structured-outputs-config entry ---")
data = load_simple_params_yaml()
for sec_name, sec in data.items():
    if sec_name == "meta":
        continue
    for p in sec.get("params", []):
        if p.get("name") == "--structured-outputs-config":
            print("entry:", p)
            print("built args:", build_extra_args_simple(p))
            break
