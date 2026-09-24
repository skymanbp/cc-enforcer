#!/usr/bin/env python3
"""cc-enforcer — measure what the hooks cost per event.

Every hook here is a separate OS process that Claude Code spawns and
waits for, so the plugin's latency sits directly in the critical path of
the agent's prompts and tool calls. That makes "how slow is it?" a real
question about the product, and one the README should not answer from
memory.

What it reports and why the baseline row matters
------------------------------------------------
Each hook's wall-clock is measured end to end: spawn, interpret, read
stdin, decide, write stdout, exit. On Windows most of that is the Python
interpreter starting up, not any detector running — so a bare
``python -c pass`` is measured in the same loop and printed alongside.
Without that row a reader would attribute the whole figure to the
guards, and the interesting number (what cc-enforcer itself adds) would
be invisible.

What each scenario exercises
----------------------------
* ``SessionStart`` / ``UserPromptSubmit`` — the two injections. The
  second runs on every prompt, which makes it the most frequent hook in
  the plugin; it was missing from this table until v0.40.
* ``PreToolUse(Read)`` — a repeat Read of an already-recorded file.
* ``PreToolUse(Edit)`` — an ALLOWED systematic edit: the content
  detectors, the on-disk scale measurement and every state write. Until
  v0.40 the Edit row measured a small edit against one session, so the
  warm-ups pushed the rolling-patch counter to its threshold and every
  measured run was the DENY path — the shortest one, not the common one.
* ``PreToolUse(Bash)`` — a clean command through every deny check.
* ``Stop (9 layers)`` — a done-claim reply on an edit turn (the Edit
  above landed in the same session), so all nine layers are evaluated
  and all nine pass. Until v0.40 the warm-up Edits were denied, the Stop
  was a non-edit turn, and layers (e)/(f)/(g)/(i) never ran.

Every run is checked: a hook that exits non-zero, or produces output
where none is expected, aborts the benchmark. Without that a crashing
hook would look like a speed-up.

Numbers are machine-specific by nature; nothing in CI pins them. This
script is the reproduction the README cites, so a reader can get their
own figures instead of trusting the author's.

Usage
-----
    python hooks/scripts/bench_hooks.py [--runs N] [--json]

``--json`` emits one object per scenario for scripted comparison.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent

# Warm-up runs discarded before measurement: the first spawn of a script
# pays for the OS file cache and the .pyc write, which is a one-off the
# steady-state figure should not carry.
WARMUP_RUNS = 3
DEFAULT_RUNS = 25


def _percentile(values: list[float], pct: float) -> float:
    """The `pct` percentile by nearest-rank, on a copy sorted ascending.

    Nearest-rank rather than interpolation: at n=25 an interpolated p95
    invents a value between two samples, and every number printed here
    should be one that was actually observed.
    """
    ordered = sorted(values)
    rank = max(1, min(len(ordered), round(pct / 100.0 * len(ordered))))
    return ordered[rank - 1]


def _time_one(argv: list[str], payload: str | None, env: dict,
              expect_stdout: bool | None, label: str) -> float:
    start = time.perf_counter()
    proc = subprocess.run(
        argv,
        input=payload.encode("utf-8") if payload is not None else b"",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    elapsed = (time.perf_counter() - start) * 1000.0
    if proc.returncode != 0:
        raise SystemExit(
            f"{label}: exit status {proc.returncode} -- a failing hook is not "
            f"a fast one\n{proc.stderr.decode('utf-8', 'replace')[-800:]}"
        )
    if expect_stdout is not None and bool(proc.stdout.strip()) != expect_stdout:
        raise SystemExit(
            f"{label}: {'no output' if expect_stdout else 'unexpected output'} "
            f"-- the scenario is not exercising the path it names\n"
            f"{proc.stdout.decode('utf-8', 'replace')[:400]}"
        )
    return elapsed


def _measure(argv: list[str], payload: str | None, env: dict, runs: int,
             expect_stdout: bool | None, label: str) -> dict:
    for _ in range(WARMUP_RUNS):
        _time_one(argv, payload, env, expect_stdout, label)
    samples = [_time_one(argv, payload, env, expect_stdout, label)
               for _ in range(runs)]
    return {
        "p50_ms": round(statistics.median(samples), 1),
        "p95_ms": round(_percentile(samples, 95), 1),
        "max_ms": round(max(samples), 1),
    }


def _dumps(payload: dict) -> str:
    """Serialise a benchmark payload the way Claude Code sends one.

    `ensure_ascii=False` matters here (v0.37): the Stop scenario below is
    written in Chinese, and the `json.dumps` default would escape it to
    `\\uXXXX` before it reached the wire. That is a shorter payload AND a
    different code path — the layers would find no CJK markers to match —
    so the number printed would not be the number production pays.
    """
    return json.dumps(payload, ensure_ascii=False)


def _scenarios(target: str, session: str) -> list[dict]:
    """One dict per scenario: label, script (None = baseline), args, payload,
    and whether stdout is expected (None = not checked)."""
    # The Edit scenario before it is ALLOWED, so this Stop is an edit turn
    # and layers (e)/(f)/(g)/(i) are live: the reply carries the rule-08
    # and rule-09 markers those layers look for, so every layer is
    # evaluated and every layer passes.
    done = (
        "已修复并验证。\n$ python -m unittest → Ran 617 tests, OK\n"
        "重触发原症状: 已通过。\nrule 07: 无降级、无遗漏。\n"
        "rule 08: 改前必读、写前必想 —— 根因 / 架构 / 方案 / 影响范围 / 风险均已说明。\n"
        "rule 09: 系统式修改，根因 + 影响范围 + 方案三件套齐全。\n"
        "tldr: 修好了，测试全绿。"
    )
    # A systematic edit (>= 50 lines) resets the rolling-patch counter on
    # every run, so each measured Edit is ALLOWED and walks the full path.
    old_block = "".join(f"# line {i:03d}\n" for i in range(100, 160))
    new_block = "".join(f"# line {i:03d} revised\n" for i in range(100, 160))
    return [
        {"label": "SessionStart", "script": "inject_context.py",
         "args": ["--event", "SessionStart"], "expect_stdout": True,
         "payload": _dumps({"session_id": session,
                            "hook_event_name": "SessionStart"})},
        {"label": "UserPromptSubmit", "script": "inject_context.py",
         "args": ["--event", "UserPromptSubmit"], "expect_stdout": True,
         "payload": _dumps({"session_id": session,
                            "hook_event_name": "UserPromptSubmit"})},
        {"label": "PreToolUse(Read)", "script": "read_guard.py", "args": [],
         "expect_stdout": False,
         "payload": _dumps({
             "session_id": session, "hook_event_name": "PreToolUse",
             "tool_name": "Read", "tool_input": {"file_path": target},
         })},
        {"label": "PreToolUse(Edit)", "script": "read_guard.py", "args": [],
         "expect_stdout": False,
         "payload": _dumps({
             "session_id": session, "hook_event_name": "PreToolUse",
             "tool_name": "Edit", "tool_input": {
                 "file_path": target,
                 "old_string": old_block, "new_string": new_block,
             },
         })},
        {"label": "PreToolUse(Bash)", "script": "bash_guard.py", "args": [],
         "expect_stdout": False,
         "payload": _dumps({
             "session_id": session, "hook_event_name": "PreToolUse",
             "tool_name": "Bash", "tool_input": {"command": "git status --short"},
         })},
        {"label": "Stop (9 layers)", "script": "stop_guard.py", "args": [],
         "expect_stdout": False,
         "payload": _dumps({
             "session_id": session, "hook_event_name": "Stop",
             "last_assistant_message": done,
         })},
        {"label": "baseline: python -c pass", "script": None, "args": [],
         "expect_stdout": None, "payload": ""},
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=int, default=DEFAULT_RUNS,
                    help=f"measured runs per scenario (default {DEFAULT_RUNS})")
    ap.add_argument("--json", action="store_true",
                    help="emit JSON instead of a table")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="ccenf-bench-") as tmp:
        env = dict(os.environ)
        env["CLAUDE_PLUGIN_DATA"] = tmp
        # An empty project root: no edicts, no sync-gate, so every row is
        # the plugin's own floor rather than this checkout's config.
        env["CLAUDE_PROJECT_DIR"] = tmp
        env.pop("CC_ENFORCER_AUTO_GC_DAYS", None)
        # A 300-line target: big enough that the v0.35 scale measurement
        # actually reads a file, which is the cost this benchmark exists
        # to keep honest about.
        target = os.path.join(tmp, "target.py")
        with open(target, "w", encoding="utf-8") as fh:
            fh.write("".join(f"# line {i:03d}\n" for i in range(300)))

        results = []
        for sc in _scenarios(target, "bench-session"):
            if sc["script"] is None:
                argv = [sys.executable, "-c", "pass"]
                stdin = None
            else:
                argv = [sys.executable, str(SCRIPTS / sc["script"]), *sc["args"]]
                stdin = sc["payload"]
            stats = _measure(argv, stdin, env, args.runs,
                             sc["expect_stdout"], sc["label"])
            results.append({"scenario": sc["label"], **stats})

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    baseline = next(
        (r["p50_ms"] for r in results if r["scenario"].startswith("baseline")),
        0.0,
    )
    # Output is deliberately ASCII-only. Windows consoles default to a
    # legacy codepage (cp936 here), which renders an em dash as mojibake
    # and can raise UnicodeEncodeError outright on a redirected stream --
    # a benchmark that crashes while reporting is worse than a plain one.
    print(f"cc-enforcer hook latency - {args.runs} runs each, "
          f"{WARMUP_RUNS} discarded warm-ups")
    print(f"python {sys.version.split()[0]} on {sys.platform}\n")
    print(f"{'scenario':<26} {'p50':>10} {'p95':>10} {'max':>10}"
          f"   {'own share':>10}")
    print("-" * 72)
    for r in results:
        own = r["p50_ms"] - baseline
        is_base = r["scenario"].startswith("baseline")
        share = "-" if is_base else f"{own:+.1f} ms"
        print(f"{r['scenario']:<26} {r['p50_ms']:>7.1f} ms {r['p95_ms']:>7.1f} ms "
              f"{r['max_ms']:>7.1f} ms   {share:>10}")
    print("\n'own share' = p50 minus the bare-interpreter baseline: the part "
          "that\nis cc-enforcer's work rather than process startup.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
