"""Start-up cost of the four hook entry points — what the v0.40 sweep bought.

Every hook is a fresh interpreter, so whatever a script imports at
module load is a per-invocation tax on the agent's tool calls. Before
the sweep the common path of every hook paid for modules it never used
there: `argparse` (and the `shutil` / `bz2` / `lzma` it drags in) for one
flag, `dataclasses` (and `inspect` / `ast` / `dis`) for two record types,
`tomllib` for a config file that usually does not exist, `traceback` for
a handler that usually does not run — and `stop_guard` compiled ~115
regexes up front on a path that mostly returns after the done-claim
check. Measured on Linux that was ~50 ms of a ~65 ms hook.

These tests pin the property, not the milliseconds (which are the
machine's): the common path of each hook imports none of those modules,
`stop_guard`'s patterns compile only when a layer asks, and the lazy
pattern answers exactly what `re.compile` would. The import inventory is
taken from `-X importtime` in a subprocess, because the test runner has
long since imported most of these modules itself.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _helpers import SCRIPTS_DIR, run_hook  # noqa: E402 -- after the path bootstrap above

sys.path.insert(0, str(SCRIPTS_DIR))


def _imported_modules(script: str, args: list[str], payload: dict,
                      env: dict, cwd: str) -> tuple[set[str], subprocess.CompletedProcess]:
    """Module names a fresh interpreter imports while running `script`."""
    proc = subprocess.run(
        [sys.executable, "-X", "importtime", str(SCRIPTS_DIR / script), *args],
        input=json.dumps(payload).encode("utf-8"),
        capture_output=True, env=env, cwd=cwd,
    )
    names: set[str] = set()
    for line in proc.stderr.decode("utf-8", errors="replace").splitlines():
        # "import time:      self |   cumulative | <indent>module.name"
        if line.startswith("import time:") and "|" in line:
            names.add(line.rsplit("|", 1)[1].strip())
    return names, proc


# What no common path may import any more. `shutil` is listed on its own
# because it is what argparse costs; `inspect` because it is what
# dataclasses costs.
_NEVER_ON_A_COMMON_PATH = {
    "argparse", "shutil", "dataclasses", "inspect", "tomllib", "traceback",
    "hashlib",
}


class TestCommonPathsStayLight(unittest.TestCase):
    """No hook's common path imports a module that path never uses."""

    def setUp(self) -> None:
        # An empty project: no edicts.toml, no sync-gate.toml, fresh state.
        self.tmp = tempfile.mkdtemp(prefix="ccenf-startup-")
        self.env = dict(os.environ)
        self.env["CLAUDE_PLUGIN_DATA"] = self.tmp
        self.env["CLAUDE_PROJECT_DIR"] = self.tmp
        self.env.pop("CC_ENFORCER_AUTO_GC_DAYS", None)
        self.env.pop("CLAUDE_ENV_FILE", None)
        # And an empty home. `edicts.global_path()` is `Path.home()` plus
        # `.claude/cc-enforcer/edicts.toml`; a maintainer who keeps global
        # edicts (this repository's does) would otherwise watch every hook
        # load `tomllib` for a config that genuinely exists, and this class
        # call it a regression on that one machine while CI stays green.
        # Both spellings, because `Path.home()` reads USERPROFILE on Windows
        # and HOME elsewhere — the isolation `test_edicts.py` already uses.
        self.env["HOME"] = self.tmp
        self.env["USERPROFILE"] = self.tmp

    def _check(self, script: str, args: list[str], payload: dict,
               also_forbidden: set[str], expect_stdout: bool) -> None:
        names, proc = _imported_modules(script, args, payload, self.env, self.tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr[-500:])
        self.assertEqual(bool(proc.stdout.strip()), expect_stdout, proc.stdout[:200])
        self.assertTrue(names, "importtime produced no inventory")
        offenders = sorted((names & _NEVER_ON_A_COMMON_PATH) | (names & also_forbidden))
        self.assertEqual(
            offenders, [],
            f"{script} imports {offenders} on its common path; each one is paid "
            f"on every invocation for work this path never does",
        )

    def test_per_turn_injection(self) -> None:
        self._check(
            "inject_context.py", ["--event", "UserPromptSubmit"],
            {"session_id": "t", "hook_event_name": "UserPromptSubmit"},
            also_forbidden={"lib.state", "lib.envfile", "gc_state"},
            expect_stdout=True,
        )

    def test_session_start_without_maintenance_passes(self) -> None:
        # No auto-GC opt-in, no CLAUDE_ENV_FILE: state is still needed for
        # nothing here, and gc_state must not load without the opt-in.
        self._check(
            "inject_context.py", ["--event", "SessionStart"],
            {"session_id": "t", "hook_event_name": "SessionStart"},
            also_forbidden={"lib.state", "gc_state"},
            expect_stdout=True,
        )

    def test_plain_read(self) -> None:
        target = os.path.join(self.tmp, "x.py")
        Path(target).write_text("x = 1\n", encoding="utf-8")
        self._check(
            "read_guard.py", [],
            {"session_id": "t", "hook_event_name": "PreToolUse",
             "tool_name": "Read", "tool_input": {"file_path": target}},
            also_forbidden=set(),
            expect_stdout=False,
        )

    def test_clean_bash_command(self) -> None:
        self._check(
            "bash_guard.py", [],
            {"session_id": "t", "hook_event_name": "PreToolUse",
             "tool_name": "Bash", "tool_input": {"command": "git status --short"}},
            also_forbidden={"lib.state"},
            expect_stdout=False,
        )

    def test_stop_without_a_done_claim(self) -> None:
        self._check(
            "stop_guard.py", [],
            {"session_id": "t", "hook_event_name": "Stop", "cwd": self.tmp,
             "last_assistant_message": "Still looking; no conclusion yet."},
            also_forbidden={"lib.sync_gate"},
            expect_stdout=False,
        )

    def test_a_config_in_the_controlled_home_does_load_the_parser(self) -> None:
        """The twin: an edicts.toml in the home this class controls, and
        `tomllib` must appear in the inventory.

        Two things it proves. The negative checks above are not vacuous —
        the `-X importtime` inventory can see the parser when it loads. And
        the home the hooks consult is the one `setUp` points them at: this
        is the exact shape of the false red this class produced before
        `setUp` isolated HOME, reproduced on purpose.
        """
        from lib import projroot
        home = tempfile.mkdtemp(prefix="ccenf-home-")
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        cfg = projroot.config_file(Path(home), "edicts.toml")
        cfg.parent.mkdir(parents=True)
        cfg.write_text(
            '[[edicts]]\nid = "E01"\ntext = "probe"\nseverity = "should"\n'
            'deny_bash = ["never-typed-here"]\n',
            encoding="utf-8")
        env = dict(self.env, HOME=home, USERPROFILE=home)
        names, proc = _imported_modules(
            "bash_guard.py", [],
            {"session_id": "t", "hook_event_name": "PreToolUse",
             "tool_name": "Bash", "tool_input": {"command": "git status --short"}},
            env, self.tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr[-500:])
        self.assertIn(
            "tomllib", names,
            "a config exists in the controlled home and the parser did not "
            "load: either the hooks read a different home than this class "
            "isolates, or the inventory cannot see tomllib at all — in which "
            "case every negative check above is vacuous",
        )


_LAZINESS_PROBE = r"""
import sys
sys.path.insert(0, sys.argv[1])
import stop_guard as sg

seen, found = set(), []
def walk(obj):
    if id(obj) in seen:
        return
    seen.add(id(obj))
    if isinstance(obj, sg._LazyPattern):
        found.append(obj)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            walk(item)
    elif isinstance(obj, dict):
        for item in obj.values():
            walk(item)

for name, value in list(vars(sg).items()):
    if not name.startswith("__"):
        walk(value)
at_import = sum(p._compiled is not None for p in found)
sg._has_done_claim("nothing is claimed here")
after_done_check = sum(p._compiled is not None for p in found)
print(len(found), at_import, after_done_check)
"""


class TestStopGuardRegexesAreLazy(unittest.TestCase):
    def test_nothing_compiles_at_import_and_little_for_a_no_claim_stop(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-c", _LAZINESS_PROBE, str(SCRIPTS_DIR)],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-800:])
        total, at_import, after = (int(x) for x in proc.stdout.split())
        self.assertGreaterEqual(total, 100, "the probe did not find the pattern tables")
        self.assertEqual(at_import, 0, "a pattern compiled at import time")
        self.assertLess(
            after, total // 4,
            f"a Stop with no done-claim compiled {after} of {total} patterns; "
            f"only the done-claim set should be needed to return",
        )

    def test_lazy_pattern_answers_like_re_compile(self) -> None:
        import stop_guard as sg
        samples = [
            "已修复。tldr: 好了，可以 ship。",
            "Fixed. I think it works now.\n$ pytest\n3 passed in 0.2s",
            "sync-check: docs and tests updated together",
            "No claim is made in this sentence.",
            "I edited foo.py and created bar.md; rule 12 checked.",
        ]
        tables = ("DONE_PATTERNS", "EVIDENCE_PATTERNS", "HEDGE_NEAR_DONE_PATTERNS",
                  "SYNC_MARKERS", "TLDR_MARKERS")
        checked = 0
        for table in tables:
            for lazy in getattr(sg, table):
                real = re.compile(lazy.pattern, lazy.flags)
                for text in samples:
                    a, b = lazy.search(text), real.search(text)
                    self.assertEqual(a and a.span(), b and b.span(), (table, lazy.pattern))
                    self.assertEqual([m.span() for m in lazy.finditer(text)],
                                     [m.span() for m in real.finditer(text)])
                    self.assertEqual(lazy.sub("#", text), real.sub("#", text))
                    checked += 1
        self.assertGreater(checked, 50)
        # Delegation covers what is not spelled out (e.g. `groups`).
        self.assertEqual(sg._FILE_CLAIMS_ZH.groups, re.compile(sg._FILE_CLAIMS_ZH.pattern).groups)


class TestSmallerContracts(unittest.TestCase):
    """The three behaviour-preserving rewrites the sweep made elsewhere."""

    def test_inject_event_flag_keeps_argparse_semantics(self) -> None:
        inject = str(SCRIPTS_DIR / "inject_context.py")
        for argv in ([inject, "--event", "Bogus"], [inject], [inject, "--events"]):
            with self.subTest(argv=argv[1:]):
                rc, out, err = run_hook(argv, {"session_id": "t"})
                self.assertEqual(rc, 2)
                self.assertIsNone(out)
                self.assertIn("usage:", err)
                self.assertIn("SessionStart", err)
        rc, out, _ = run_hook([inject, "--event=UserPromptSubmit"], {"session_id": "t"})
        self.assertEqual(rc, 0)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")

    def test_record_edit_turn_saves_only_when_something_changes(self) -> None:
        from lib import state as state_lib
        saves: list[int] = []
        original_save = state_lib.save
        old_env = os.environ.get("CLAUDE_PLUGIN_DATA")
        with tempfile.TemporaryDirectory(prefix="ccenf-state-") as tmp:
            os.environ["CLAUDE_PLUGIN_DATA"] = tmp
            state_lib.save = lambda state: (saves.append(1), original_save(state))[1]
            try:
                state_lib.record_edit_turn("s1", None)   # sets the flag: saved
                state_lib.record_edit_turn("s1", None)   # nothing new: not saved
                state_lib.record_edit_turn("s1", 7)      # a turn number: saved
                state_lib.record_edit_turn("s1", 7)      # same again: not saved
                self.assertTrue(state_lib.did_edit_this_turn("s1", 7))
            finally:
                state_lib.save = original_save
                if old_env is None:
                    os.environ.pop("CLAUDE_PLUGIN_DATA", None)
                else:
                    os.environ["CLAUDE_PLUGIN_DATA"] = old_env
        self.assertEqual(len(saves), 2)

    def test_bash_guard_answers_the_same_from_a_shared_tokenisation(self) -> None:
        import bash_guard
        from lib import shellcmd
        push = "rm -f build.log && git push --force origin main"
        self.assertEqual(
            bash_guard._detect_force_push(push),
            bash_guard._detect_force_push(push, shellcmd.segments(push)),
        )
        self.assertIsNotNone(bash_guard._detect_force_push(push))
        reg = ("python /abs/register_read.py --file /abs/f.py --hash " + "a" * 64)
        self.assertEqual(
            bash_guard._parse_register_invocation(reg),
            bash_guard._parse_register_invocation(reg, shellcmd.segments(reg)),
        )
        self.assertEqual(bash_guard._parse_register_invocation(reg)["file"], "/abs/f.py")


if __name__ == "__main__":
    unittest.main()
