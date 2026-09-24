# cc-enforcer

> **Rules your coding agent physically cannot ignore.**
> A Claude Code plugin — and an LLM-agnostic rule pack — that stops reactive
> patching, guessed citations, surface-level "fixes" and premature "done" claims
> by intercepting the agent's own tool calls, not by asking it nicely.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Plugin Version](https://img.shields.io/badge/version-0.41.0-blue.svg)](CHANGELOG.md)
[![Tests](https://github.com/skymanbp/cc-enforcer/actions/workflows/test.yml/badge.svg)](https://github.com/skymanbp/cc-enforcer/actions/workflows/test.yml)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-plugin-purple.svg)](https://code.claude.com/docs/en/plugins.md)

**[中文文档 →](README.zh.md)**

---

## 1 · What it is

Every "be rigorous" instruction you put in a prompt shares one flaw: **the model
decides whether to follow it.** Under pressure — a long session, a compacted
context, a failing test at 2am — it decides not to, and tells you it did.

cc-enforcer moves the important half of that contract **out of the prompt and
into the harness**. Claude Code hooks run *before* each tool call and *before*
each reply is allowed to end. A violation returns a real `deny` / `block`
verdict, so the agent cannot reason, apologise, or "just this once" its way past
it.

Twelve rules. Ten of them backed by a hook. Zero dependencies, standard
library only, and every guard fails **open** — a bug in the discipline can never
brick your agent.

---

## 2 · The problem it targets

LLM coding agents (Claude Code, Cursor, Copilot, Cline, Aider…) fail in
predictable, nameable ways. Each row is a behaviour this plugin was built to
make impossible rather than discouraged:

| Lazy pattern | What it looks like in practice | Answer |
|---|---|---|
| **Reactive patching** | Sees a bug, wraps it in `try/except`, declares done. | rule 03 + 09, `PreToolUse` DENY |
| **Guessed citations** | Cites files, line numbers or APIs that do not exist. | rule 01 + 05, Stop layer (b)/(g) |
| **Keyword-search-only** | Greps once, edits, never reads the surrounding architecture. | rule 04 + 08, `PreToolUse` DENY |
| **Memory dependence** | Acts on stale recollection instead of re-reading the file. | rule 04 + 08, read-before-edit gate |
| **Root-cause bypass** | `sleep` for races, `--no-verify` for hooks, swallowed exceptions. | rule 03, `PreToolUse(Bash)` DENY |
| **Half-finished work** | Stops at "should work", leaves TODOs, skips the whole flow. | rule 07, Stop layer (d) |
| **Premature done-claim** | "Fixed" without re-running the failing case or comparing evidence. | rule 06, Stop layers (a)/(c) |
| **Stale references** | Changes a symbol; leaves its docs, tests and translations behind. | rule 12, Stop layer (i) |

**Effect goal:** an agent that either does the disciplined thing or *visibly
fails to* — never one that quietly skips a step and reports success.

---

## 3 · Features and scope

### Feature 1 — Twelve rules as a portable contract

The reasoning contract, as plain Markdown in [`rules/`](rules/). Ten of the
twelve are backed by a hook; rules 02 and 05 are text-level discipline.

| # | Rule | What it demands | Enforcement |
|---|---|---|---|
| 01 | **Verify, don't guess** | Every claim about a file, API, version, error or citation is checked *in the same turn* it is written. "I don't know" beats a confident wrong answer. | soft + Stop (b)(g) |
| 02 | **Systematic, not reactive** | Answer seven questions before editing: architecture, responsibility, root cause, plan, ripple, risk, global validity. | soft (graded by (e)) |
| 03 | **Root cause, not symptom** | Climb the causal chain — symptom site → propagation path → **origin** — until the answer is a mechanism. Stopping early is legal only if you name the true origin and say why. | **Bash DENY** + soft |
| 04 | **Read fully, not keywords** | Grep locates; understanding requires the whole file plus its callers. | **Edit/Write DENY** |
| 05 | **Cite traceable sources** | `file:line` for code, URL/DOI for literature, command + output for runtime claims. | soft |
| 06 | **Verify convergence** | Re-trigger the original symptom, exercise boundary and negative cases, run existing tests, answer four self-quiz questions. "No regression" must be a per-item set diff, never a matching total. | **Stop (a)(c)** |
| 07 | **Task fidelity** | Decompose the user's request into checkable sub-items; every modifier word they used ("all", "strict", "mandatory") must land as a hard action, not a doc line. | **Stop (d)** |
| 08 | **Read before edit, think before write** | Full read going in; root cause / architecture / impact stated coming out. | **DENY + Stop (e)** |
| 09 | **Systematic modification** | One root cause, one unified fix — sweep the whole class, never N patches. Suppression markers need an adjacent *why*. | **DENY ×2 + Stop (f)** |
| 10 | **No non-essential hardcoding** | Secrets, tokens, private keys and credentials-in-URLs never become source literals. | **Edit/Write DENY** |
| 11 | **No non-essential path dependency** | No `C:\Users\…` / `/home/you/` / `$HOME` baked into code; derive paths at runtime. | **Edit/Write DENY** |
| 12 | **Repo-wide sync** | An edit is done only when every reference to it — docs, tests, downstream code, translations — is co-updated or explicitly verified current. | **Stop (i)**, opt-in |

Full text: [`rules/`](rules/) · index: [`rules/00-index.md`](rules/00-index.md) (English) · [`docs/RULES.md`](docs/RULES.md) (Chinese)

### Feature 2 — Hard gates at the tool boundary (`PreToolUse` → DENY)

These refuse the call outright. Every one ships a named escape hatch, so they
are bypassable **by saying why**, never by accident.

| Gate | Triggers on | Escape hatch |
|---|---|---|
| **Read-before-edit** | Editing a file that exists on disk but was never opened this session. | Read it; or register a SHA-256-verified read. |
| **Suppression markers** | `# noqa`, `# type: ignore`, `@ts-ignore`, `@ts-expect-error`, `eslint-disable`, `time.sleep(…)` workarounds. | Adjacent why-comment (English *or* Chinese), or fix the cause. |
| **Bare `try/except: pass`** | An exception handler whose body is just `pass` — detected across lines, comments in between included. | Same why-comment hatch. |
| **Hardcoded secrets** | Secret-named literal, PEM private-key header, `AKIA…`, `ghp_…` / `xox…` / `AIza…`, `user:pass@host` URLs. | Env var, marked placeholder, or why-comment. |
| **Machine-specific paths** | `C:\Users\…`, `/home/<user>/`, `/Users/<user>/`, `$HOME`, `%USERPROFILE%`, quoted `~/…`. | Derive at runtime, or why-comment. Prose docs and lockfiles exempt. |
| **Rolling patches** | The 4th small edit (< 200 chars **and** ≤ 10 lines) to one file with no systematic rewrite in between. | One rewrite of ≥ 50 lines / ≥ 1500 chars / **≥ 30% of that file**. Net reductions and version bumps are never counted at all — see §5. |
| **Dangerous shell** | `--no-verify`, `--no-gpg-sign`, `git push --force` (not `--force-with-lease`), `chmod 777`, `git rebase --skip`, `--break-system-packages`, `rm -rf` on `/` `$HOME` `~`. | Fix the hook failure / permission / conflict instead. |
| **Your own edicts** | Any regex you registered as a `must` edict. | Only you can relax it. |

### Feature 3 — The done-claim gate (`Stop` → BLOCK, nine layers)

The Stop hook reads the reply the agent is about to finish with. If it contains
a completion claim, nine layers grade it. Layers (e)(f)(g)(i) apply only to
turns that actually edited a file.

| Layer | Rule | Blocks when the reply… |
|---|---|---|
| (a) | 06 | claims done with **no evidence** — no command, no output, no counts. |
| (b) | 01 | pairs a done-claim with a **first-person hedge** (`I think`, `probably`, `maybe`, `我觉得`, `应该是`). Bare `should` and `通常` are deliberately *not* hedges — they are ordinary technical prose. |
| (c) | 06 | shows evidence but never answers the **four convergence questions**. |
| (d) | 07 | passes convergence but never reconciles against the **user's original request**. |
| (e) | 08 | edited a file without surfacing ≥ 3 of root cause / architecture / solution / impact / risk. |
| (f) | 09 | edited a file without the **root cause + impact + solution** triplet. |
| (g) | 01+06 | says "I edited X" while X's **mtime on disk is unchanged**. |
| (h) | — | has **no `tldr`**, or a `tldr` item longer than 160 display columns. |
| (i) | 12 | tripped a project **sync-gate** group with no co-update and no `sync-check:` line. |

**Grace is per layer:** the layer that just blocked is forgiven on the next
attempt — you can never be blocked twice for the same row — but a *different*
layer you are still violating will still fire. Escalation is bounded by the
layer count, and any clean reply resets it.

### Feature 4 — Imperial Edicts: your own hard rules

Most "custom rules" features are just more text in a prompt. Here your rule
becomes a regex a hook matches against the literal content of every Edit, Write
and Bash call before it lands:

```bash
/cc-enforcer:edict add E01 "no mongoose, use prisma" --must \
    --deny-edit 'from ["'"'"']mongoose["'"'"']' \
    --deny-bash 'npm\s+(i|install)\s+mongoose'
```

- **Two severities, mechanically different.** `must` + a regex → `PreToolUse`
  DENY naming the edict id. `should` → reminder text only, never denies.
- **Two scopes.** `.claude/cc-enforcer/edicts.toml` (project — commit it so the
  team shares the red line) or `~/.claude/cc-enforcer/edicts.toml` (`--global`).
- **Hot-reloaded** — the loader re-reads on every hook event, so you can iterate
  on a regex mid-session.
- **Injected with the contract and again on every prompt**, so an edict is
  never out of the agent's sight.
- **Ordered after the built-ins by design**: an edict can add restrictions,
  never subtract them.
- **Fails safe, not quiet**: an unparseable severity falls back to `must`, and a
  malformed edict drops itself with a stderr diagnostic instead of blocking work.

Details: [`docs/EDICTS.md`](docs/EDICTS.md)

### Feature 5 — What you invoke yourself

**6 slash commands**, one subagent, two auto-triggered skills:

| Surface | What it does |
|---|---|
| `/cc-enforcer:checklist` | Prints the **8-section checklist** (pre-edit → post-edit → convergence → fidelity → read/think → systematic → TL;DR → repo sync). Its patch-marker item is a *closed set* synchronised with the hook's real constant, so you cannot tick every box and still get denied. |
| `/cc-enforcer:verify` | Turns the agent's last reply into untrusted input: extracts every factual claim, buckets it (code location / behaviour / external / run result) and prescribes a re-verification method per bucket. Recall is explicitly not allowed. |
| `/cc-enforcer:edict` | `list / add / remove / reload / path` for Imperial Edicts (`--global` for personal scope). |
| `/cc-enforcer:gc` | Lists — or with `--apply`, deletes — session-state files older than N days. Dry-run by default, and the command file forbids the agent from choosing `--apply` for you. |
| `/cc-enforcer:i18n` | Checks every translation still matches the English skeleton file-for-file and heading-for-heading. |
| `/cc-enforcer:sync-gate` | `init / list / check / add / remove / path` for this project's rule-12 co-update groups. **`check` is the point**: the gate's loader is failing-open, so a dropped group or a glob that matches no file makes it stop guarding *silently*. `check` names both and exits 1, so it works in CI. |
| **`verifier` subagent** | A deliberately crippled read-only checker (Read/Grep/Glob only — a permission fact, not an instruction). Returns *intact / drift / missing / mismatch / unverifiable* per claim. It cannot become the fixer, so it has no incentive to quietly patch a discrepancy. |
| **`systematic-debug` skill** | Auto-triggers on bug-fix language and takes over the workflow: build a fast deterministic reproduction loop **first**, then hypothesise. |
| **`repo-refresh` skill** | Auto-triggers on repo-audit language: sweeps code *and* prose together for stale / outdated / redundant / wrong / drifted content, then asks you to convert whatever coupling it found into a sync-gate group. |

### Out of scope — deliberately

- It does not review your code for correctness. It reviews the agent's *process*.
- It does not replace a linter, type checker or test suite; it stops the agent
  from silencing them.
- It does not sandbox anything. See §9.

---

## 4 · How it is implemented

| Event | Matcher | Behaviour | Implementation |
|---|---|---|---|
| `SessionStart` | — | Inject the 12-rule discipline summary + reply schema + Imperial Edicts (English by default, any language via `CC_ENFORCER_LANG`). Fires on startup, resume, clear and after every compaction, so the contract survives compaction by construction. | [`inject_context.py`](hooks/scripts/inject_context.py) |
| `UserPromptSubmit` | — | Inject a short per-turn reminder (the hard gates, the Stop layers, the reply-schema field names) + edicts — about 2.6k characters, because every prompt pays for it again. | [`inject_context.py`](hooks/scripts/inject_context.py) |
| `PreToolUse` | `Read\|Edit\|Write` | Record reads, capture mtime baselines, run the content + frequency + edict gates. | [`read_guard.py`](hooks/scripts/read_guard.py) |
| `PreToolUse` | `Bash` | Tokenise the command, deny bypass flags and destructive operations, process read registrations, scan edicts. | [`bash_guard.py`](hooks/scripts/bash_guard.py) |
| `Stop` | — | The nine-layer done-claim decision, rendered as a status table + recovery + plain-language line. | [`stop_guard.py`](hooks/scripts/stop_guard.py) |

Both injections are budgeted against Claude Code's 10,000-character hook-output
cap: the contract is protected and the (unbounded) edict list is what yields,
elided at whole-edict boundaries with a pointer — and when even the contract
fills the budget, the injection says how many edicts were dropped. A test holds
a 120-character install root plus three real edicts under the cap for all four
prompts, so the budget cannot erode release by release again.

Every hook decodes its payload as strict UTF-8 through
[`lib/hookio.py`](hooks/scripts/lib/hookio.py) rather than the host codepage,
so non-English replies reach the detectors intact; and everything a guard
*prints* lives in a per-language message catalog
([`lib/messages_en.py`](hooks/scripts/lib/messages_en.py) is the skeleton),
resolved per key through `CC_ENFORCER_LANG` — what the guards *match* stays
bilingual regardless ([`docs/I18N.md`](docs/I18N.md)).

Fourteen Python files under [`hooks/scripts/`](hooks/scripts/) sit on fifteen
shared [`lib/`](hooks/scripts/lib/) modules. Only the four in the table above
are registered as hooks, and each of those is a thin entry over a sibling
`_impl.py` module that holds the body: Python caches the bytecode of a module
it imports, never of the script it was asked to run, so the split is what
spares a hook re-compiling its own source on every call. The other six
(`register_read.py`, `manage_edicts.py`, `manage_sync_gate.py`, `gc_state.py`,
`i18n_check.py`, `bench_hooks.py`) back the escape hatch, the slash commands,
CI and the benchmark. Full contracts:
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) §2.

### Install

#### As a Claude Code plugin (recommended)

The repo ships `.claude-plugin/marketplace.json`, so it registers as a
single-plugin marketplace:

```bash
git clone https://github.com/skymanbp/cc-enforcer.git /path/to/cc-enforcer
```

Then in any Claude Code session (CLI or IDE):

```
/plugin marketplace add /path/to/cc-enforcer
/plugin install cc-enforcer@cc-enforcer
```

Verify with `/plugin` → **Installed** should list `cc-enforcer@cc-enforcer`.
Commands then surface as `/cc-enforcer:checklist`, `/cc-enforcer:verify`, …

> **Requirements:** Python 3.11 or newer on PATH (`tomllib` is the floor;
> CI runs 3.13). Hook scripts use the standard library only — no pip step, no
> third-party packages.

#### As a rule pack for any other LLM

You do not need Claude Code. The rules are plain Markdown (English is the source
of truth; [`rules/zh/`](rules/zh/) is the Chinese translation):

```bash
cat rules/*.md    > cc-enforcer.txt     # English skeleton
cat rules/zh/*.md > cc-enforcer.txt     # Chinese translation
# feed as system prompt / pre-context to the agent of your choice
```

You lose the hard layers (they are Claude Code hooks) and keep the reasoning
discipline. [`rules/00-index.md`](rules/00-index.md) is the short form when
the whole pack is too long; the rule-pack layer is described in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) §6.

---

## 5 · What it actually looks like

### The same task, run twice

One task, two runs, identical starting files. The only variable is whether the
hooks are in the loop. Reproduce both with `python demo/run_demo.py --svg` —
sources and the full explanation in [`demo/`](demo/README.md).

> **`charge()` crashes with `KeyError` when the payment gateway declines.
> Make it stop crashing.**

| | Without cc-enforcer | With cc-enforcer |
|---|---|---|
| Edits that landed | 5 of 5 | 3 of 5 |
| Sign-off | accepted | blocked |
| Suite at the end | **red** | green |
| What the caller gets on a decline | `None`, silently | `GatewayError`, handled |

![Without cc-enforcer: every edit lands, the crash becomes a silent None, and a
false "the suite is green" sign-off ends the turn](demo/out/without-cc-enforcer.svg)

![With cc-enforcer: the swallow is denied, the fourth small edit is denied, the
evidence-free sign-off is blocked](demo/out/with-cc-enforcer.svg)

Every cc-enforcer verdict in those images is verbatim hook output; the agent's
five moves are scripted, which is what makes the two runs identical in
everything except the hooks. [`tests/test_demo.py`](tests/test_demo.py)
re-runs the demo and compares against the committed images byte for byte, so
a change in any hook's wording fails CI rather than leaving a stale picture.

### The rolling-patch verdict, up close

The fifth edit never lands:

```text
cc-enforcer · rule 09 violation (rolling-patch interception)

Tool: Edit
Target: auth.py
Rolling-patch counter: 3 small edit(s) already applied
this session; this would be attempt #4 — at or above the
threshold of 4.
…
Classification used here:
  small      = max(|old_string|, |new_string|) < 200 chars
               AND max line count ≤ 10
  systematic = max chars ≥ 1500 OR max line count ≥ 50
               OR the change spans ≥ 30% of this file — here, 37 of 122 lines or 1102 of 3672 chars
               (resets the counter to 0)
  medium     = anything in between (does not count, does not reset)

Never counted, at any counter value:
  net reduction — new_string is SHORTER than old_string. A rolling patch
                  is an accretion; an edit that leaves the file smaller
                  than it found it cannot be one.
  bookkeeping   — only version / ISO-date literals differ and every other
                  byte is identical (in prose documents, bare integers
                  count too). Bumping a version number is not a fix.
```

That message is not advice printed after the fact. **The edit did not happen.**
The per-file bar it quotes (here `37 of 122 lines or 1102 of 3672 chars`) is
computed from the target on disk, and [`test_doc_sync.py`](tests/test_doc_sync.py)
re-derives it from [`lib/editscale.py`](hooks/scripts/lib/editscale.py) so this
sample cannot drift away from the code that produces it.

### The done-claim gate, up close

The demo above shows layer (a) refusing a claim with **no evidence**. Layer (b)
is the neighbouring case — evidence may follow, but the claim is hedged, so the
turn still cannot end. This reply:

> Fixed the race condition in the worker pool. I think it holds now.

produces:

```text
cc-enforcer · Stop check FAILED at Layer (b) [rule 01 — hedge near done-claim]

| Layer | Rule | Status      | Note                              |
|-------|------|-------------|-----------------------------------|
| (a)   | 06   | ⏸  pending  | (not evaluated)                   |
| (b)   | 01   | ❌ **FAIL** | hedge near done-claim             |
| (c)   | 06   | ⏸  pending  | (not evaluated)                   |
…
Done-claim matched: 'Fixed'
Hedge matched: 'I think'

[Recovery — rule 01 + hedge]
Your reply pairs a completion claim with hedged language
within ~50 characters. …

Pick one:
  • Drop the hedge and state the result with concrete output, or
  • Drop the done-claim and say explicitly "not yet verified" so
    the user decides whether to ship.

In plain words: You claimed it works and hedged in the same breath — drop the hedge, or say plainly that it is unverified.
```

The hedge set is **first-person uncertainty only** — `我记得` / `我觉得` /
`我相信` / `可能就` / `应该是` / `大概` / `I think` / `I believe` / `I guess` /
`maybe` / `probably` / `kinda` / `sort of`. A bare `should` is **not** in it, by
design: it is ordinary technical prose far more often than a hedge.
[`test_doc_sync.py`](tests/test_doc_sync.py) derives the trigger list from
`stop_guard._HEDGE_INNER`, so no surface can advertise a hedge the hook ignores.

Note the status table reports **evaluation** order, not the alphabet: (b) runs
first, because a hedge invalidates a done-claim however much evidence sits
beside it — so a layer-(b) block shows "(a) ⏸ pending", not "(a) ✅ Pass". A
gate built to catch unfounded claims does not get to make one.

### Output sample: the reply schema it enforces

Every done-claim reply ends with this block. The field names *are* the Stop
hook's detection markers:

```yaml
cc-enforcer:
  before: {architecture: ..., root cause: ..., solution: ...}
  edits: [{file: "path:line", what: "..."}]
  convergence:
    re-trigger: "$ python -m unittest → Ran 773 tests, OK"
    boundary case: ...
    existing tests: ...
    self-quiz: {really solved: ..., better solution: ..., unverified: ..., verification reasonable: ...}
  fidelity: {request coverage: [...], standard: ..., no degradation: ...}
  closing: {root cause: ..., impact: ..., solution: ...}
  sync-check: <co-files updated, or why none needed>
  tldr: "<one plain sentence>"
```

---

## 6 · Benchmark

Every hook is a separate OS process that Claude Code spawns and waits for, so
the plugin's latency sits directly in the critical path of the agent's prompts
and tool calls. Reproduce with:

```bash
python hooks/scripts/bench_hooks.py --runs 60
```

Measured on v0.37.0 — Windows 11, Python 3.13.3, 60 runs each after 3 discarded
warm-ups:

| Scenario | p50 | p95 | max | cc-enforcer's own share |
|---|---:|---:|---:|---:|
| `PreToolUse(Read)` | 135.2 ms | 149.9 ms | 178.4 ms | **+73.7 ms** |
| `PreToolUse(Edit)` | 137.4 ms | 152.5 ms | 161.5 ms | **+75.9 ms** |
| `PreToolUse(Bash)` | 151.9 ms | 181.4 ms | 192.5 ms | **+90.4 ms** |
| `Stop` (all nine layers) | 157.3 ms | 171.6 ms | 182.1 ms | **+95.8 ms** |
| *baseline:* `python -c pass` | 61.5 ms | 70.5 ms | 74.1 ms | — |

**The baseline row is the point.** Roughly half of every figure is the Python
interpreter starting up, which cc-enforcer does not control and which is
markedly slower on Windows than on Linux. The plugin's own work is the *own
share* column: tens of milliseconds, against an LLM turn measured in seconds.

The start-up sweep after v0.39.2 cut that share by 40–60 % on every hook, by
importing only what each hook's common path uses and compiling the Stop
hook's regexes on first use. Linux, Python 3.11, same machine, 40 runs:

| Scenario | own share before | own share after |
|---|---:|---:|
| `UserPromptSubmit` (every prompt) | ≈ +50 ms | **+19 ms** |
| `PreToolUse(Read)` | +53 ms | **+27 ms** |
| `PreToolUse(Bash)` | +50 ms | **+21 ms** |
| `Stop` (all nine layers) | +68 ms | **+33 ms** |

**Honesty about these numbers**, since a benchmark table invites more trust than
it has earned: they are one machine under normal desktop load, the median moves
by tens of milliseconds with what else is running, and the `own share` column
is a subtraction of two medians, not a measured isolate — an order of
magnitude, not a figure. **Nothing in CI pins them**; the counts, samples and
inventories on this page are derived from the code by a drift gate (§8),
latency cannot be, because it is a property of your machine. The script is the
citation — run it yourself.

### Accuracy posture

There is no precision/recall table here, and that absence is deliberate. The
detectors are tuned to **prefer false negatives** (§8): where a detector's reach
is known to stop short, the limit is written into the rule file and pinned by a
test asserting the *non*-detection, so it cannot quietly drift into an implied
guarantee — `sync-check: checked it` is just as empty as `sync-check: n/a` and
still passes, and the test says so.

---

## 7 · Why this isn't a prompt file — or a linter

The interesting engineering is in the detectors, and most of it exists because
the naive version demonstrably failed:

- **Source is lexed, not regexed.** `line.find("#")` finds the `#` inside a URL —
  which once let a single neighbouring `API = "https://api.example.com"` line
  disable the *secret* detector entirely (`example` reads as a rationale token).
  [`lib/srclex.py`](hooks/scripts/lib/srclex.py) distinguishes code from comment
  from docstring from data literal.
- **Shell is tokenised, not string-matched.** [`lib/shellcmd.py`](hooks/scripts/lib/shellcmd.py)
  splits a compound command into per-invocation argv, resolves git global options
  to the true subcommand, and recurses into `bash -c` payloads. So
  `rm -f build.log && git push origin main` never attributes `-f` to the push,
  `$(git push --force)` is still denied, and `echo git commit --no-verify` is
  correctly *allowed*.
- **Edit size is measured against the file, not a constant.**
  [`lib/editscale.py`](hooks/scripts/lib/editscale.py) asks how much of the
  target a change actually spans, so a full rewrite of a 30-line module counts
  as systematic instead of locking the file for the session.
- **Markers end at real token boundaries.** `\b` treats a hyphen as a boundary,
  so a naive matcher denied `@ts-ignore-generated` and `# noquality`. The
  detectors use `(?![\w-])`.
- **The escape hatch is self-securing.** The read-registration hatch recomputes
  the file's SHA-256 from disk; an agent that never opened it cannot produce the
  digest. `false && register_read.py …` earns no credit either — the hook fires
  before execution and cannot know which branch the shell takes.
- **Rationales must be substantive.** A leading `TODO` / `FIXME` / `HACK` is a
  deferral, not a reason, and still denies.
- **Concurrency is handled, with numbers.** Every hook invocation is a separate
  OS process and Claude Code fires tools in parallel. Mutations hold a
  cross-process advisory lock and save atomically — measured before the fix:
  2–3 of 10 recorded reads lost at 10-way parallelism.
- **One limit means one thing.** The tldr cap counts *display columns*, not code
  points, because a CJK character occupies two of them: 160 code points is about
  one English sentence and about two Chinese paragraphs.

---

## 8 · Design philosophy

**Physical enforcement over persuasion.** If a rule matters, it gets a hook. A
rule that exists only as prose is documented as such — §3 marks which is which,
and the phrase "mandatory" in a rule file with no hook behind it is treated as a
defect, not a style.

**Fail open, always.** Any exception inside a guard logs to stderr and *allows*
the call. Unreadable state is treated permissively. This is the single most
important invariant in the codebase: a discipline plugin that can brick your
agent will be uninstalled, and then it enforces nothing at all. Enforcement is
best-effort, **not a security boundary** — it is built to stop a lazy agent,
not a hostile one.

**Prefer false negatives.** A missed violation costs one lazy edit; a false
alarm costs a turn and erodes trust in the gate. Documented gaps live in the
rule file rather than being quietly patched.

**The rules are the product; the hooks are one adapter.** `rules/` is plain
Markdown with no runtime dependency, and `cat rules/*.md` is a documented
install path. A rule file describing a weaker escape hatch than the hook
enforces is therefore a shipped defect: it hands weaker discipline to every
non-Claude-Code consumer.

**Structure over text-matching.** Four `lib/` judgement models
(`srclex`, `mdctx`, `shellcmd`, `editscale`) exist because every guard had been
answering a *structural* question with a *textual* test, and each audit round
regenerated the same defect class. One model, one definition, many consumers.

**The repo is held to its own rules.** Development of cc-enforcer runs under
cc-enforcer. Four CI drift gates make documentation claims un-drift-able:

- a **version gate** — every version pointer, the badges in *both* READMEs, and
  the newest CHANGELOG heading pinned to `plugin.json` by a *closed set*, and
  every *released* CHANGELOG heading checked against `git tag`;
- a **doc gate** — every pinned number in this README derived from the code at
  test time, plus inventory checks in both directions (a tree that lists a
  deleted file is drift too);
- an **i18n gate** — every translation structurally matched to the English
  skeleton, including DENY-row token parity;
- a **demo gate** — the before/after images both READMEs embed, re-rendered
  from the live hooks and compared byte for byte.

**Tech stack:** Python 3.11+ (CI: 3.13), standard library only. No dependencies, no build
step, no lock file. CI: `ubuntu-latest` × `windows-latest`, `fail-fast: false`.
The Windows leg is not box-ticking — several regressions here are Windows-only
by construction (`os.replace` sharing violations, `\r\n` defeating end-of-line
anchors, unquoted drive paths).

---

## 9 · Limits, configuration, and what's next

### Configuration

| Variable | Effect |
|---|---|
| `CC_ENFORCER_LANG=<code>` | Injection language for prompts, edicts and deny reasons. Unset / `en` = English skeleton; `zh` = Chinese; any other code reads `<dir>/<code>/` with per-file fallback to English. |
| `CC_ENFORCER_DISABLE_LAYER_G=1` | Turn off Stop layer (g) file-claim verification. The other eight layers still apply. |
| `CC_ENFORCER_AUTO_GC_DAYS=N` | Auto-prune session state older than N days at SessionStart, rate-limited to once per 24h. Unset / `0` → disabled. |
| `CLAUDE_PLUGIN_DATA` | Session-state base dir. Set by Claude Code; falls back to `${CLAUDE_PROJECT_DIR}/.claude/local/cc-enforcer/`, then `~/.claude/local/cc-enforcer/`. |
| `CLAUDE_PROJECT_DIR` | Project root, used to resolve `.claude/cc-enforcer/edicts.toml` and `sync-gate.toml`. |

**Per-project sync gate** (rule 12) is opt-in: declare co-update groups in
`.claude/cc-enforcer/sync-gate.toml` and Stop layer (i) enforces them.

### Known limits — what it does *not* do

Stated plainly, because a discipline plugin that oversells itself is the failure
mode it exists to prevent:

- **The Stop layers only engage on a completion claim.** A reply that never says
  "done" is never graded.
- **Rules 02 and 05 have no hook of their own**, and the reasoning half of rules
  03, 09 and 12 is text-level. No hook can verify that you *actually* swept a
  defect class; it can only verify that you said you did.
- **The hard layers are Claude Code-specific.** Other agents get the rule pack.
- **The rolling-patch gate goes inert on files of ~5 lines or fewer**, where a
  two-line edit already spans a third of the file and so counts as a systematic
  rewrite. Intended — "you have not re-engaged with the file's overall
  structure" is not a claim anyone can make about a five-line file.
- **Everything fails open and prefers misses to false alarms** — see §8.

### Roadmap

**Empty, by decision.** The two entries it last carried were retired, not
deferred: per-session ephemeral edicts are structurally blocked (the edict CLI is
a Bash subprocess with no `session_id`), and the layer-(g) content-hash upgrade
had its premise measured false (mtime here resolves to 1 ms, while layer (g)
compares a first-encounter baseline against closing time, seconds apart). A
feature list carrying entries nobody will build is the staleness this repo
exists to catch.

---

## Repository structure

```
cc-enforcer/
├── rules/                       # 12 rules + index — English skeleton (source of truth)
│   └── zh/                      # Chinese translation, structurally CI-gated
├── prompts/                     # SessionStart contract + per-turn reminder (+ zh/)
├── hooks/
│   ├── hooks.json               # event → script wiring
│   └── scripts/
│       │                        # -- hook entry points (the four in hooks.json): thin shells --
│       ├── inject_context.py    # soft layer: SessionStart + per-turn injection
│       ├── read_guard.py        # hard layer: read-before-edit, content + frequency gates
│       ├── bash_guard.py        # hard layer: command discipline, read registration
│       ├── stop_guard.py        # hard layer: the nine-layer done-claim gate
│       │                        # -- their bodies, imported so the bytecode is cached --
│       ├── inject_context_impl.py
│       ├── read_guard_impl.py
│       ├── bash_guard_impl.py
│       ├── stop_guard_impl.py
│       │                        # -- auxiliary entry points (not hooks) --
│       ├── register_read.py     # SHA-256-verified read-cache escape hatch
│       ├── manage_edicts.py     # Imperial Edicts CRUD CLI
│       ├── manage_sync_gate.py  # rule-12 co-update groups: CRUD + `check` diagnostics
│       ├── gc_state.py          # session-state GC: CLI + auto-GC callee
│       ├── i18n_check.py        # skeleton ↔ translation structural parity
│       ├── bench_hooks.py       # per-hook latency benchmark (README §6)
│       └── lib/                 # -- fifteen shared modules --
│           ├── hookio.py        # boundary: stdin payload -> UTF-8, never the locale codepage
│           ├── lang.py          # boundary: the active language code, resolved once for every consumer
│           ├── messages.py      # boundary: resolve guard text for CC_ENFORCER_LANG
│           ├── messages_en.py   #   the English skeleton — every string a guard prints
│           ├── messages_zh.py   #   its Chinese translation (same keys, same fields)
│           ├── srclex.py        # judgement: code vs comment vs docstring vs literal
│           ├── mdctx.py         # judgement: markdown fence / blockquote context
│           ├── shellcmd.py      # judgement: tokenise → segments → argv → subcommand
│           ├── editscale.py     # judgement: change size relative to its target file
│           ├── state.py         # state: per-session, cross-process lock, atomic save
│           ├── tomlio.py        # config: tolerant TOML reader + the shared writer
│           ├── projroot.py      # config: project-root detection, shared by both loaders
│           ├── edicts.py        # feature: Imperial Edicts loader / matcher / renderer
│           ├── envfile.py       # feature: CLAUDE_ENV_FILE dedupe hygiene
│           └── sync_gate.py     # feature: rule-12 groups — read, write and match
├── commands/                    # 6 slash commands
├── agents/verifier.md           # read-only citation checker subagent
├── skills/                      # systematic-debug, repo-refresh (auto-invoked)
├── docs/                        # index + ARCHITECTURE, CONTRIBUTING, RULES, EDICTS, I18N
├── demo/                        # the same task run twice — §5's images
│   ├── paygate/                 #   a tiny project with a real lagging bug
│   ├── run_demo.py              #   drives the real hooks, captures both transcripts
│   ├── render_svg.py            #   transcript -> terminal SVG, zero dependencies
│   └── out/*.svg                #   the committed images, pinned by tests/test_demo.py
└── tests/                       # 773 black-box + unit tests (python -m unittest discover tests)
    │                            # each file is named after what it covers — see tests/README.md
    ├── _helpers.py              #   shared run_hook(...) subprocess fixture
    ├── test_<hook>.py           #   black-box subprocess tests, one per hook entry point
    ├── test_<lib|cli>.py        #   unit tests for shared modules and auxiliary scripts
    ├── test_startup_cost.py     #   what each hook imports on its common path; lazy regexes
    ├── test_demo.py             #   drift gate: the README's images vs a fresh demo run
    ├── test_version_sync.py     #   drift gate: version pointers + release tags
    ├── test_doc_sync.py         #   drift gate: documented counts + inventories vs code
    ├── test_i18n_sync.py        #   drift gate: every translation vs the English skeleton
    └── test_audit_*.py          #   per-audit-round regression suites (v026 x2, v027)
```

All scripts are covered by **773 tests** in [`tests/`](tests/) — black-box
subprocess tests that launch each hook exactly as Claude Code does, plus unit
tests for the shared models and the four drift gates.

---

## Contributing

The plugin enforces its own rules on its own development — expect to be denied
by it while working on it. The house rules, the local checks and the release
checklist are in [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md); the
connected-files map to consult before editing anything is
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) §8. Release history:
[`CHANGELOG.md`](CHANGELOG.md).

---

## License

MIT — see [`LICENSE`](LICENSE).
