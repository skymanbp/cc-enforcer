# Tests — index

**773 tests, 21 files, zero dependencies.** Every test file appears below with
what it covers. Nothing else in the repo enumerates the suite.

## Run

```bash
# From the repo root, stdlib only — no pytest needed:
python -m unittest discover tests

# One file:
python -m unittest discover -s tests -p "test_read_guard.py" -v
```

Pytest also works (it runs `unittest` classes natively): `pytest tests/`.

## How the files are named

| Naming shape | Category | Meaning |
|---|---|---|
| `test_<hook-script>.py` | **hook** | Black-box subprocess test of one registered hook entry point. |
| `test_<module>.py` | **lib / cli** | Unit test of one shared module or auxiliary script. |
| `test_*_sync.py`, `test_demo.py` | **gate** | A CI drift gate — derives its expectations from the code, then fails when a doc, manifest, image or translation disagrees. |
| `test_audit_*.py` | **audit** | The regression suite of one audit round, pinning the defects that round confirmed. |

## Inventory

### Shared fixture

| File | Covers |
|---|---|
| [`_helpers.py`](_helpers.py) | `run_hook(...)`: launches a script as a real subprocess with a synthetic JSON stdin payload and returns `(returncode, parsed_stdout, stderr)`. It serialises with `ensure_ascii=False`, which is load-bearing: the `json.dumps` default escapes every non-ASCII character, so the wire would be pure ASCII and the encoding boundary unreachable from any test. |

### Hook entry points — black-box subprocess

Each of these invokes the target script the way Claude Code does. That
matters: module-level state, stdin handling, stdout buffering and exit codes
all behave differently when a script is imported instead of executed.

| File | Tests | Covers |
|---|---:|---|
| [`test_inject_context.py`](test_inject_context.py) | 35 | [`inject_context.py`](../hooks/scripts/inject_context.py) — payload shape for both events, language switching and fallback, UTF-8 / CJK survival, the reply-schema contract, the 10,000-character output cap with a 120-character install root and three real edicts for all four prompts, whole-edict elision with a true count, the self-locating header naming the root once, the per-turn reminder's size caps and its constraint set derived from the guards, and the chrome-less per-turn edict table. |
| [`test_read_guard.py`](test_read_guard.py) | 108 | [`read_guard.py`](../hooks/scripts/read_guard.py) — the read-before-edit allow/deny matrix, the rule 09 / 10 / 11 content detectors, the rolling-patch counter against a realistically sized target (a one-line fixture hid the small-file lock-in for twenty-two releases), path normalisation, `edited_files` recording, 12-way concurrent state writes, fail-open, and the plugin's ability to rewrite its own files. |
| [`test_bash_guard.py`](test_bash_guard.py) | 21 | [`bash_guard.py`](../hooks/scripts/bash_guard.py) — the bypass-pattern catalog, force-push spellings, the register-as-read hatch (chaining and command-position rules), event gating, fail-open. |
| [`test_stop_guard.py`](test_stop_guard.py) | 155 | [`stop_guard.py`](../hooks/scripts/stop_guard.py) (entry) and [`stop_guard_impl.py`](../hooks/scripts/stop_guard_impl.py) (body) — all nine layers, the status-table format, per-layer grace, production-shape payloads (no `turn_count`), the `last_assistant_message` field ahead of the transcript fallback, the transcript tail read (a 60 MB file costs a few windows; 256-byte windows agree with a whole-file scan), tldr presence and display-column length, and that naming a rule-06 check — in either language — is not evidence until output accompanies it. |

### Shared modules and auxiliary scripts

| File | Tests | Covers |
|---|---:|---|
| [`test_startup_cost.py`](test_startup_cost.py) | 15 | Start-up discipline across all four hooks: no common path imports `argparse` / `shutil` / `dataclasses` / `inspect` / `tomllib` / `traceback` / `hashlib` (nor `lib.state`, `lib.envfile`, `gc_state`, `lib.sync_gate` where the path never touches them), nothing in `stop_guard` compiles at import and a no-claim Stop compiles only the done set, the lazy pattern answers exactly like `re.compile`, `--event` keeps argparse's usage contract, `record_edit_turn` saves only on change, and the shared tokenisation answers like the string form. The probe environment isolates HOME as well as the project (a maintainer's global `edicts.toml` is a config that legitimately loads the parser), and a twin plants an `edicts.toml` in that controlled home to prove the inventory can see `tomllib` at all. The thin-shell pins (v0.41): each entry defines nothing and imports `<entry>_impl`; after one run of the entry the body's `.pyc` exists and the entry's never does, while the body run as a script is not cached either; importing an entry yields the body module itself, and loading an entry by file path from a bare `-I` interpreter still finds its body. |
| [`test_hookio.py`](test_hookio.py) | 21 | [`lib/hookio.py`](../hooks/scripts/lib/hookio.py) — the payload-decoding boundary, plus the encoding contract at all four hook entries end to end under a forced `cp936` stdin, with the refusal twin (non-UTF-8 bytes raise rather than being rewritten) and a liveness check that the reproduction still bites. |
| [`test_messages.py`](test_messages.py) | 17 | [`lib/messages.py`](../hooks/scripts/lib/messages.py) and the two catalogs — the English catalog carries zero CJK, the Chinese one is actually translated, and `CC_ENFORCER_LANG` changes what a guard prints end to end. Key-set and placeholder parity live in `test_i18n_sync.py`. |
| [`test_envfile.py`](test_envfile.py) | 11 | [`lib/envfile.py`](../hooks/scripts/lib/envfile.py) — the dedupe model (last occurrence wins, order survives, refusal twins for non-export lines and open quotes) plus black-box SessionStart runs. |
| [`test_edicts.py`](test_edicts.py) | 64 | [`lib/edicts.py`](../hooks/scripts/lib/edicts.py) loading / injection / DENY / severity gating, file encoding tolerance, and the [`manage_edicts.py`](../hooks/scripts/manage_edicts.py) CLI including its TOML round-trip, cwd fallback and the single-definition pin on the `--global` path. |
| [`test_sync_gate.py`](test_sync_gate.py) | 19 | [`lib/sync_gate.py`](../hooks/scripts/lib/sync_gate.py) — config resolution order, TOML tolerance, any-vs-all mode, `./` glob normalisation, project-relative boundaries. |
| [`test_editscale.py`](test_editscale.py) | 40 | [`lib/editscale.py`](../hooks/scripts/lib/editscale.py) — the change-scale model: the absolute classifier, the 30 %-coverage route with both axes and both boundaries, net reduction, the bookkeeping allowlist in code vs prose, every exemption with its refusal twin. |
| [`test_gc_state.py`](test_gc_state.py) | 19 | [`gc_state.py`](../hooks/scripts/gc_state.py) — argument validation, dry-run vs apply, threshold semantics, auto-GC on SessionStart. |
| [`test_register_read.py`](test_register_read.py) | 5 | [`register_read.py`](../hooks/scripts/register_read.py) — the user-facing stub's own hash verification and exit codes (the authoritative check lives in `bash_guard`). |
| [`test_manage_sync_gate.py`](test_manage_sync_gate.py) | 28 | [`manage_sync_gate.py`](../hooks/scripts/manage_sync_gate.py) — the rule-12 config CLI and the primitives it shares with the loader: a write lands in the named project (never the cwd the READ resolver would pick), `path` prints through the same deterministic resolver, and every written group survives a real `load_file()` round-trip. |

### CI drift gates

Each derives its expectation **from the code at test time** and never
compares one document against another — two documents can drift together.

| File | Tests | Guards against |
|---|---:|---|
| [`test_version_sync.py`](test_version_sync.py) | 9 | A version pointer that does not match `plugin.json` (the set of version-bearing JSON pointers is closed), a README badge behind it, a newest CHANGELOG heading behind it, and a released heading with no `git tag` (registered exceptions must be admitted by their own entry). The gate's own input is pinned: `fetch-depth: 0` in the workflow is what gives the tag half a tag list. |
| [`test_doc_sync.py`](test_doc_sync.py) | 25 | Stale counts and inventories (rule, command and test counts; the Bash deny set on every surface that claims to list it; the `lib/` and script inventories in both structure trees; every repo-relative markdown link), plus three behavioural claim classes: advertised hedge triggers re-derived from `stop_guard._HEDGE_INNER`, sample coverage bars re-derived from `editscale.coverage_bar`, and every backticked identifier in a non-CHANGELOG doc resolving to a real definition or a registered reason. Also: one language per document, the closed registries that make each of these checks non-vacuous, and the document set itself taken from the git index — an untracked or ignored file on the machine is invisible to every scanner and to the link resolver, pinned by a planted probe. |
| [`test_i18n_sync.py`](test_i18n_sync.py) | 13 | Translation drift: file-set parity, ATX heading-level sequence, enforcement-token parity (a `zh` session must not be promised a smaller deny set than an `en` one), and for the message catalogs exact key sets both ways, per-key `str.format` fields, and that every key a guard asks for exists. |
| [`test_demo.py`](test_demo.py) | 9 | The before/after images both READMEs embed: re-runs [`demo/run_demo.py`](../demo/run_demo.py) and compares against the committed `demo/out/*.svg` byte for byte, so a change to any guard's wording fails CI instead of leaving a stale picture; each of the three verdicts is also asserted by content. |

### Audit-round regressions

House rule, followed throughout: **every "this is allowed" assertion has a
twin that removes the reason and requires a DENY.** An allow-only test cannot
tell a working escape hatch from a deleted detector.

Second house rule: fixtures containing suppression markers, credentials or
home paths are **assembled at runtime**. This plugin scans its own test files;
a literal fixture would make the module unwritable by any agent running it.

| File | Tests | Round |
|---|---:|---|
| [`test_audit_v026_models.py`](test_audit_v026_models.py) | 93 | The shared judgement models (`TestSrclex` / `TestMdctx` / `TestShellcmd`) plus one regression class per confirmed defect of that round. |
| [`test_audit_v026_round2.py`](test_audit_v026_round2.py) | 54 | Sixteen parallel read-only reviews; each test pins a defect reproduced against the real code before anything was changed. |
| [`test_audit_v027_contracts.py`](test_audit_v027_contracts.py) | 12 | Three items recorded as "known, not fixed", each closed as a deliberate contract change. |

## Adding a test case

1. Add the **positive case** (the new pattern the guard should catch).
2. Add a **nearby negative case** that is similar but must *not* trigger, so
   the boundary is visible to the next contributor.
3. If the case asserts that something is **allowed**, add the twin that makes
   it denied. Otherwise the test survives the detector being deleted.
4. Update the connected files listed in
   [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) §8 — and this index,
   if you added a file.

## What is intentionally NOT tested here

- **End-to-end install.** `/plugin marketplace add` is a Claude Code IDE
  surface, not a CLI one. That the plugin loads is verified by hand after an
  install.
- **Live tool denial inside Claude Code.** These tests prove each script emits
  the documented JSON for the documented stdin shape. Whether Claude Code
  honours a `deny` is Claude Code's contract, not ours.
- **Judgement prose.** `test_doc_sync.py` pins numbers, inventories and three
  derivable behavioural claim classes. It says nothing about whether an
  explanation is right, what order a guard's checks run in, or whether a
  rationale is sound.
- **Latency.** `bench_hooks.py` measures it; nothing pins the milliseconds,
  because they belong to the machine. `test_startup_cost.py` pins the
  import inventory instead, which is the property the milliseconds follow.
