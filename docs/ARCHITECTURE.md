# Architecture

> Audience: developers extending or auditing the plugin.
> Doc index: [`./README.md`](./README.md). Companion docs:
> [`./CONTRIBUTING.md`](./CONTRIBUTING.md) (how to change this repository),
> [`./RULES.md`](./RULES.md) (the rule catalog, in Chinese; the English index
> is [`../rules/00-index.md`](../rules/00-index.md)),
> [`../tests/README.md`](../tests/README.md) (the suite, file by file).
>
> This document describes the plugin **as it is**. Why each part came to be
> this way — the field failures, the measurements, the versions — is in
> [`../CHANGELOG.md`](../CHANGELOG.md), one entry per release.

---

## 1. Why a layered design

A single mechanism can never enforce discipline reliably. Prompt injection can
be ignored by a confident-and-wrong agent; a hard tool block can be bypassed by
re-phrasing; a subagent verifier only fires when invoked. So five independent
layers stack, each catching a different failure mode:

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 5 — LLM-agnostic rule pack (rules/ — plain Markdown)     │  source of truth
├─────────────────────────────────────────────────────────────────┤
│  Layer 4 — Skills (auto-invoked on debugging / audit language)  │  contextual nudge
├─────────────────────────────────────────────────────────────────┤
│  Layer 3 — Verifier subagent (independent re-reader)            │  citation audit
├─────────────────────────────────────────────────────────────────┤
│  Layer 2 — Slash commands (user/agent-triggered)                │  on-demand
├─────────────────────────────────────────────────────────────────┤
│  Layer 1 — Hooks: prompt injection + hard DENY / BLOCK gates    │  always-on
└─────────────────────────────────────────────────────────────────┘
```

Failure of any one layer does not collapse the system; the next layer still
catches the lazy behaviour, usually through a different signal.

---

## 2. Layer 1 — Hooks

**Wired in:** [`../hooks/hooks.json`](../hooks/hooks.json). Five entries, four
scripts, four events:

| Event | Matcher | Script | Does |
|---|---|---|---|
| `SessionStart` | — | [`inject_context.py`](../hooks/scripts/inject_context.py) | Injects the discipline **contract** (`prompts/session-start.md`) plus the project's Imperial Edicts; then runs two failing-open maintenance passes (opt-in auto-GC of old session state, `CLAUDE_ENV_FILE` dedupe). Fires on startup, resume, clear and after every compaction. |
| `UserPromptSubmit` | — | [`inject_context.py`](../hooks/scripts/inject_context.py) | Injects the short per-turn **reminder** (`prompts/user-prompt.md`) plus the edicts, on every prompt. |
| `PreToolUse` | `Read\|Edit\|Write` | [`read_guard.py`](../hooks/scripts/read_guard.py) | Records reads and mtime baselines; denies an Edit/Write of an unread existing file (rules 04 + 08), of content carrying an unjustified suppression marker (rule 09), a hardcoded secret (rule 10), a user-home path (rule 11) or a `must` edict match, and the 4th small edit to one file with no systematic rewrite between (rule 09); records the edit-turn signal and the edited-file set for the Stop layers. |
| `PreToolUse` | `Bash` | [`bash_guard.py`](../hooks/scripts/bash_guard.py) | Denies the bypass patterns and destructive commands (rule 03) and `must` edict matches; processes the read-registration escape hatch. |
| `Stop` | — | [`stop_guard.py`](../hooks/scripts/stop_guard.py) | The nine-layer done-claim gate. |

Why four scripts and not one: each has a different responsibility and a
different failure mode (a lost injection, a corrupted state file, a mis-parsed
command, a wrong Stop verdict), and collapsing them would chain those behind a
single `try/except` where a bug in one masks the others. Why everything is in
`PreToolUse` and nothing in `PostToolUse`: `PostToolUse` does not fire for tool
calls whose target lies outside the project directory while `PreToolUse` does,
so recording and gating in the same event is the only way both see the same
set of files. Recording in Pre is therefore speculative — it happens before
the tool result exists — which is why only targets that already exist are
recorded as read (a Read of a not-yet-built artifact must not pre-authorise an
edit of whatever the build later puts there).

### 2.1 What every hook shares

- **Payload boundary** — [`lib/hookio.py`](../hooks/scripts/lib/hookio.py) reads
  stdin's binary buffer and decodes it as strict UTF-8 (RFC 8259 §8.1). The
  text-mode alternative decodes with the host codepage under
  `surrogateescape`, which on a non-UTF-8 host silently rewrites every
  non-ASCII character before any detector sees it.
- **Message catalog** — everything a guard prints comes from
  [`lib/messages.py`](../hooks/scripts/lib/messages.py) over `messages_en.py`
  (the skeleton) and `messages_zh.py`, resolved per key for the language
  [`lib/lang.py`](../hooks/scripts/lib/lang.py) reads from `CC_ENFORCER_LANG`.
  A missing translation key falls back to English for that key only. What the
  guards *match* is bilingual regardless of the switch; only what they *say*
  follows it.
- **Failing open** — any unhandled exception in a guard is logged to stderr and
  the call is allowed (exit 0, no output). Unreadable state is treated
  permissively. A discipline plugin that can brick the agent gets uninstalled,
  and then it enforces nothing.
- **Start-up discipline** — every hook is a fresh interpreter, so module-level
  imports are a per-invocation tax. Each script imports only what its common
  path uses: the TOML parser loads when a config file exists, `traceback` when
  a handler runs, the hashing and state modules in `bash_guard` only for a
  registration, `sync_gate` in `stop_guard` only for layer (i), and
  `stop_guard`'s regexes compile the first time a layer uses them.
  [`tests/test_startup_cost.py`](../tests/test_startup_cost.py) pins the
  property; [`bench_hooks.py`](../hooks/scripts/bench_hooks.py) measures the
  milliseconds (README §6).

### 2.2 `inject_context.py` — the two injections

`--event SessionStart|UserPromptSubmit` selects the prompt file; the script
never blocks and always exits 0, emitting

```json
{"hookSpecificOutput": {"hookEventName": "<event>", "additionalContext": "<text>"}}
```

**Two tiers.** `session-start.md` (~6.8k characters) is the authoritative
contract: the twelve rules in one line each, the physical-enforcement table,
the mandatory reply schema. Because `SessionStart` fires again after every
compaction, the contract survives compaction by construction. The per-turn
`user-prompt.md` (~2.6k characters) is a reminder that names every hard gate,
every Stop layer and every schema field name, and nothing else — it is re-sent
on every prompt, so every character in it is paid on every turn.
[`tests/test_inject_context.py`](../tests/test_inject_context.py) derives the
tokens the reminder must carry from the guards themselves, so a gate cannot
quietly fall out of it.

**Language.** English at `prompts/` is the skeleton; `CC_ENFORCER_LANG=<code>`
reads `prompts/<code>/` first and falls back to the skeleton per file, with a
stderr note. Any code is accepted; an unregistered one degrades to English.

**The budget.** Claude Code caps hook output at `OUTPUT_CAP` = 10,000
characters and replaces anything longer with a file path plus a short
preview, so an over-cap contract is a contract the agent reads the first two
kilobytes of. `build_context` therefore leads with a self-locating header (the
plugin root, named once, and where to Read the full text) and splits the
payload asymmetrically: the contract is protected whole; the edict table —
the only unbounded part — yields, clipped at whole-row boundaries with a
notice of how many edicts were elided (a truncated row still reads as a
complete instruction, and a silent drop is a session governed by rules it was
never shown). The realistic-install test holds a 120-character root plus
three edicts under the cap for all four prompts.

**Edicts.** Both injections append the project's Imperial Edicts
([`EDICTS.md`](./EDICTS.md)), re-read from disk on every event so an edict
added mid-session appears on the next prompt. The per-turn table omits the
intro and footer sentences the contract already carried.

**Maintenance passes** (`SessionStart` only, after the payload is built, both
failing open): auto-GC prunes session-state files older than
`CC_ENFORCER_AUTO_GC_DAYS` days, at most once per 24 h (marker file
`AUTO_GC_MARKER` in the state directory), never the live session's own file;
`lib/envfile.py` collapses duplicate `export` lines in `CLAUDE_ENV_FILE`,
keeping the last occurrence per name, and refuses the whole pass on any line
shape it cannot represent byte-identically.

### 2.3 `read_guard.py` — the write gate

**On Read:** record the path (only if it exists) and its mtime baseline (always
— "did not exist at baseline" is what layer (g) needs to judge "I created X").
Allow silently.

**On Edit / Write:**

1. Load the edicts (hot reload; before any check, so a mis-encoded
   `edicts.toml` reports on every write, denied or not).
2. Edit of a path that does not exist → allow (Claude Code rejects it itself).
   Otherwise record the baseline.
3. Target exists but was never Read this session → **DENY** (rules 04 + 08).
   The deny text carries its own recovery: Read the file, or — when the
   harness served the Read from its cache without firing the hook — register
   it through the SHA-256 hatch (§2.4).
4. **Content pipeline** over `new_string` / `content`, first hit denies:
   - suppression markers without an adjacent rationale (`PATCH_MARKERS`:
     `# noqa`, `# type: ignore`, `// @ts-ignore`, `// @ts-expect-error`,
     `// eslint-disable[-next-line|-line]`, `time.sleep(…)` with a
     race/wait/workaround comment) and a bare `try: … except: pass` (found by
     a scanner that tracks nested `try` blocks and skips comment lines);
   - a hardcoded secret (rule 10): a secret-named identifier assigned a ≥ 8
     character literal (bare or quoted key), a PEM private-key header, an AWS
     `AKIA` access key, a provider token (`ghp_` / `xox` / `AIza`), or
     credentials in a URL — obvious placeholders (`example`, `changeme`,
     `<…>`, `your-`, `os.environ` / `getenv` / `process.env` reads) are skipped;
   - a machine-specific path (rule 11): `C:\Users\…`, `/home/…`, `/Users/…`
     (raw or escaped separators), `$HOME`, `%USERPROFILE%`, a quoted `~/…`;
   - a `must` edict's `deny_edit` regex.
   The **rationale hatch** is how "non-essential" is operationalised: a
   why-comment on the line or an adjacent one, carrying a rationale token
   (`because` / `因为` / `rationale` / `intentional` / `see issue` … and, for
   rules 10 and 11, `essential` / `example` / `fixture` / `placeholder` /
   `sample` / `test data`) clears the marker. "Comment" is decided by
   [`lib/srclex.py`](../hooks/scripts/lib/srclex.py) — a `#` inside a URL is
   not one; a `/* … */` block or an own-line docstring is — and an inline
   reason must be substantive (a leading `TODO` / `FIXME` / `HACK` is a
   deferral, not a reason). Rules 10 and 11 skip prose documents (`.md`,
   `.rst`, `.txt`, `.adoc`) and lockfiles; rule 09 matches only the bare marker
   form there. Neither rule 10 nor 11 has a Stop layer: content detectors are
   `PreToolUse`-only, so an already-denied write is never judged twice.
5. **Rolling-patch frequency** (rule 09). [`lib/editscale.py`](../hooks/scripts/lib/editscale.py)
   classifies the change against the file it edits: *small* is under 200
   characters and at most 10 lines; *systematic* is ≥ 1500 characters, ≥ 50
   lines, or ≥ 30 % of the file, and resets the per-file counter; anything
   between neither counts nor resets. A net reduction and a bookkeeping edit
   (only version / ISO-date literals differ; bare integers too in prose) are
   never counted. The `ROLLING_PATCH_THRESHOLD`th small edit (4) with no
   systematic rewrite since → **DENY**; a denied edit does not increment.
   The deny quotes the file's own coverage bar, computed from disk.
6. All clear → record the read (Write), set the edit-turn flag, add the path
   to `edited_files`. Allow silently.

Deny output, both guards:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse",
  "permissionDecision": "deny", "permissionDecisionReason": "cc-enforcer · …"}}
```

### 2.4 `bash_guard.py` — command discipline

The command is tokenised once by [`lib/shellcmd.py`](../hooks/scripts/lib/shellcmd.py)
into shell segments (`&&`, `||`, `;`, `|`, newlines, `$(…)`, backticks,
subshells; it recurses into a shell's `-c` operand) and every check works on
argv, so `echo git commit --no-verify` executes nothing and is allowed while
`$(git push --force)` really runs and is denied. Checks run in this order, and
all of them before the registration step, so a command that is going to be
denied never mutates state:

| Check | Denies | Rule |
|---|---|---|
| `STATIC_PATTERNS` | `--no-verify` · `--no-gpg-sign` · `chmod 777` (`-R`, `0777` too) · `git rebase --skip` · `--break-system-packages` · `rm -rf` on root / `$HOME` / `~` | 03 |
| force-push detector | a `git push` segment (git global options resolved, `git.exe` too) carrying `--force` / `--force=…` / `--mirror` / a `+refspec` / a short cluster containing `f` (`-f`, `-fu`) — **not** `--force-with-lease` | 03 |
| edicts | a `must` edict's `deny_bash` regex | edict |
| register hatch | a `register_read.py` invocation that fails its checks (see below) | 04 |

The deny names the pattern and how to address the real problem instead; an
authorised bypass is still denied, and the agent is told to surface the deny
so the user runs the command themselves.

**Read-cache escape hatch.** Claude Code may serve a repeated Read from its
result cache without firing the hook, which would leave a later Edit falsely
denied. The recovery is `python register_read.py --file ABS --hash SHA256`,
and the hook is the authority: the invocation must be the *entire* command (a
chained or substituted form earns no credit while the stub still prints
`register_read: ok`), the script must be in command position (`argv[0]` or a
Python interpreter's script operand — never a `-c` operand), the path must be
absolute and exist, the hash must be 64 hex characters, and `bash_guard`
recomputes the SHA-256 from disk and registers only on a match. An agent that
never opened the file cannot produce the digest. If the registration cannot be
persisted, the command is denied rather than reported as done. `--file X` and
`--file=X` are both accepted.

### 2.5 `stop_guard.py` — the done-claim gate

**The reply text** comes from the payload's `last_assistant_message` (the
field Claude Code documents), else `assistant_message` (the test harness and
older payloads), else the last text-bearing assistant entry of
`transcript_path` — read from the file's tail in growing windows
(`TRANSCRIPT_TAIL_WINDOW`, ×16, capped), never whole.

**The turn number** is `turn_count` when the payload carries one (test
harnesses do; production does not) and otherwise a monotonic counter the
session state keeps per Stop.

**The gate on everything:** a done-claim (`DONE_PATTERNS` — `已解决` / `已修复`
/ `已完成` / `完成了` / `完工` / `搞定` / `[修改弄搞]好了` / `fixed` / `done` /
`completed` / `resolved` / `implemented` / `finished` / `is complete` /
`ready to ship` / `all set` / `should work now` / `that should do it`; a match
preceded by a negator is skipped). No done-claim → the edit flag and the
grace record are cleared and the Stop is allowed. Every layer below runs only
on a done-claim turn; (e), (f), (g) and (i) only when the session's
`edited_since_last_stop` flag is set (a flag, because production payloads
carry no turn count).

**Decision order** (the status table prints in this order, marking layers not
yet reached as pending rather than passed):

| Order | Layer | Rule | Blocks when |
|---|---|---|---|
| 1 | (b) | 01 | a first-person hedge sits within 50 characters of the done-claim: `我[记觉]得` / `我相信` / `可能就` / `应该是` / `大概` / `I think` / `I believe` / `I guess` / `maybe` / `probably` / `kinda` / `sort of`. Bare `should` and `通常` are ordinary technical prose and deliberately excluded. |
| 2 | (a) | 06 | no evidence (`EVIDENCE_PATTERNS`): a shell-prompt line (`$ `, `> `, `PS C:\…>`, `C:\…>`), `Ran N tests`, `N passed/failed`, `pytest` / `unittest`, a fenced block of ≥ 20 characters, `verified` / `re-ran` / `validated`, or the Chinese `重触发` / `边界用例` / `反向用例` / `收敛`. |
| 3 | (c) | 06 | no convergence marker (`rule 06` / `convergence` / `self-quiz` / `自答` / `收敛` / `重触发` / `边界用例` / `反向用例`) and fewer than 2 of the 4 self-quiz questions (really solved? better solution? what is unverified? is the verification reasonable?). |
| 4 | (d) | 07 | no fidelity marker (`rule 07` / `task fidelity` / `request coverage` / `request fidelity` / `no degradation` / `no omission` / `no scope creep` / `covered all` / `all requested` / `任务忠实` / `请求覆盖` / `原始请求` / `无遗漏` / `无降级` / `未降级` / `未遗漏` / `无超范围` / `未超范围`, or a `✅/⚠️/❌ … done` checklist row) and fewer than 2 of the 3 fidelity questions (coverage / standard / fidelity). |
| 5 | (e) | 08 | edit turn, no rule-08 marker (`rule 08` / `read-before-edit` / `think-before-write` / `改前必读` / `写前必想` / `系统式自答`) and fewer than 3 of the 6 rule-02 keyword groups (architecture · responsibility · root cause · solution/approach · downstream/impact/connected · invariant/risk, each with its Chinese spelling). |
| 6 | (f) | 09 | edit turn, no rule-09 marker (`rule 09` / `systematic modification` / `patch-style` / `non-patch` / `系统式修改` / `打补丁` / `反补丁`) and the triplet incomplete (root cause + impact/blast-radius/downstream + solution/approach/alternative). |
| 7 | (g) | 01+06 | edit turn and a claim to have edited / created a file is contradicted by the mtime baseline recorded when the session first saw it (a created file that does not exist; an edited file whose mtime never moved). Files with no baseline pass through. `CC_ENFORCER_DISABLE_LAYER_G=1` turns the layer off. |
| 8 | (h) | — | no `tldr` (`tldr:` / `TL;DR` / `大白话` / `一句话总结` / `一句总结`) that introduces actual text, or a tldr item wider than `TLDR_MAX_ITEM_COLUMNS` (160 display columns; a CJK character costs 2, a combining mark 0). Fires on every done-claim turn, not only edit turns. Presence uses the generous *attributable* verdict of [`lib/mdctx.py`](../hooks/scripts/lib/mdctx.py) (a marker inside a code fence or a blockquote is illustrative, not a claim), measurement the conservative *countable* one. |
| 9 | (i) | 12 | edit turn, and a sync-gate group's `when` glob matched an edited file with its `require` side unsatisfied (§2.8), the group not yet acknowledged this session, and no sync marker in the reply. |

**Grace is per layer.** A block records the layers spent in this recovery
sequence; on the next Stops inside the window (`turn ∈ [last_blocked + 1,
last_blocked + 3]`) those layers are forgiven while every other layer is still
live, so a recovery reply that fixes the row it was told about but still
violates another is blocked again, and no layer can block twice in one
sequence. The first allowed Stop resets the record.

**Layer (i)'s acknowledgement.** A sync marker (`SYNC_MARKERS`: `rule 12` /
`sync-check` / `repo-wide sync` / `全库同步` / `同步核对` / `连带核对`; not
`sync-gate`, which is the config file's name) settles only the groups the
previous block *named* (`last_blocked_groups`), and only when the block being
recovered from was itself at layer (i): a first violation always blocks and
names its group, and one informed answer per group suffices for the session
(`sync_acked_groups`). The marker must carry substance — `_SYNC_NON_ANSWERS`
treats `n/a`, `无`, `-` and similar placeholders as absent — and a marker
inside a fence or blockquote is a quotation, not a claim. Vacuous prose
(`sync-check: checked it`) is not detected, and is not claimed to be.

**Block output** is the Stop hook's top-level shape, not the `PreToolUse`
envelope:

```json
{"decision": "block", "reason": "cc-enforcer · Stop check FAILED at Layer (x) [rule … — …]\n\n| Layer | Rule | Status | Note |\n…"}
```

The reason is a headline naming the failing layer, the status table in
evaluation order, the matched done-claim (and hedge), a `[Recovery — …]`
section for that layer, a plain-words line (`In plain words:` / `大白话:`)
and the per-layer grace footer. Every string comes from the message catalog.

**Known asymmetry.** `收敛`, `重触发`, `边界用例` and `反向用例` count as
*evidence* for layer (a) as well as convergence markers for layer (c), while
their English counterparts (`convergence`, `re-trigger`) are markers only. A
Chinese reply whose schema carries a `收敛:` key therefore passes layer (a) on
the key alone; an English `convergence:` key does not. Recorded here rather
than changed, because narrowing the evidence set is a strictness increase for
Chinese replies and a decision for the maintainer (CHANGELOG, Unreleased).

### 2.6 Shared modules (`lib/`)

| Module | Answers |
|---|---|
| `hookio.py` | The payload as text: stdin's bytes decoded as strict UTF-8, never the locale codepage. |
| `lang.py` | The active language code, from `CC_ENFORCER_LANG`, one definition for every consumer. |
| `messages.py` + `messages_en.py` + `messages_zh.py` | Every string a guard prints, resolved per key for the active language; the English catalog is the skeleton. |
| `srclex.py` | Is this `#` a comment, a docstring or data? Where does this literal end? Which physical lines form one logical line? A tolerant lexer, not a parser — an Edit's `new_string` is rarely a complete syntactic unit. |
| `mdctx.py` | Markdown line context: fence state and info string, blockquote depth (including under list items and lazy continuation), and the two attribution verdicts layer (h) and the sync marker use. |
| `shellcmd.py` | A shell command as segments of argv, the real git subcommand past global options, and a Python interpreter's script operand. |
| `editscale.py` | How big an edit is relative to the file it edits, plus the two shapes that are never a rolling patch (net reduction, bookkeeping). |
| `state.py` | Per-session state: reads, baselines, counters, flags, the Stop record — with the cross-process lock and the atomic save (§2.7). |
| `tomlio.py` | The hardened TOML reader (BOM, encoding, parse errors → diagnostics) and the writer primitives the two config CLIs share; imports `tomllib` on first use. |
| `projroot.py` | The plugin's name, the `.claude/cc-enforcer/<file>` layout, and "is this directory a project root?" (`.git` exists or `.claude/` is a directory). |
| `edicts.py` | Imperial Edicts: resolution, parsing and validation, the injected table, the Edit/Write and Bash matchers, the deny text. |
| `envfile.py` | `CLAUDE_ENV_FILE` hygiene: the pure dedupe model and the failing-open pass. |
| `sync_gate.py` | Rule 12's co-update groups: resolution, loading, the any/all evaluation against the session's edited files. |

### 2.7 Session state

The key is the payload's `session_id`. The directory resolves in order:
`${CLAUDE_PLUGIN_DATA}/sessions/` (set by Claude Code for plugin hooks) →
`${CLAUDE_PROJECT_DIR}/.claude/local/cc-enforcer/sessions/` →
`~/.claude/local/cc-enforcer/sessions/`; the file is `<sid>.json` (git-ignored
via `.claude/local/`). Paths inside it are canonicalised with
`os.path.realpath` + `os.path.normcase`, so case-insensitive filesystems
compare correctly. It holds: the read set, the mtime baselines, the per-file
small-edit counters, `edited_since_last_stop` (and `last_edit_turn` when a
turn count exists), `edited_files`, the Stop counter, and the grace record
(`last_blocked_turn`, layer, groups, forgiven layers, `sync_acked_groups`).

**Concurrency.** Claude Code runs parallel tool calls as concurrent hook
processes sharing one session file. Every read and every mutation holds a
per-session advisory lock (`fcntl.flock` on POSIX, `msvcrt.locking` on
Windows, on a sibling `<sid>.json.lock`) across its load → mutate → save;
`save()` writes a unique temp file and `os.replace`s it, retrying with a short
backoff because on Windows a replace fails while any reader holds the target
open (CPython's `open()` does not request `FILE_SHARE_DELETE`), and unlinks
its temp file if it gives up; `load()` retries once on a transient `OSError`.
Lock acquisition failure degrades to unlocked behaviour with a stderr note.
Mutators save only when something changed.

**GC.** [`gc_state.py`](../hooks/scripts/gc_state.py) (the `/cc-enforcer:gc`
command and the auto-GC callee) prunes `*.json` session files older than N
days and day-old orphan `*.tmp` files; it never touches lock files or the
auto-GC marker, and auto-GC never prunes the live session.

### 2.8 Configuration files

Two hand-edited TOML files, both read through `tomlio.py`, both failing open:

| File | Drives | Resolution (first existing file wins) |
|---|---|---|
| `.claude/cc-enforcer/edicts.toml` | Imperial Edicts (§2.2–2.4, [`EDICTS.md`](./EDICTS.md)) | `${CLAUDE_PROJECT_DIR}` → the process cwd if it looks like a project root → `~/.claude/cc-enforcer/edicts.toml` (`--global`) |
| `.claude/cc-enforcer/sync-gate.toml` | Stop layer (i) | the Stop payload's `cwd` → `${CLAUDE_PROJECT_DIR}` → the process cwd if it looks like a project root; no home-level fallback, groups are per-repo |

The cwd fallback exists because Claude Code's Bash tool does not reliably
propagate `CLAUDE_PROJECT_DIR` on Windows; it is gated on a project-root
marker so a session started in `~/Downloads` cannot load a stranger's hard
rules. The reader strips a UTF-8 BOM, turns a non-UTF-8 file or a parse error
into a stderr diagnostic instead of an exception (an exception here used to
unwind through `read_guard` and switch read-before-edit off for the session),
and every parsed value is type-checked before use (`severity = ["must"]` is
valid TOML). A sync-gate group is `name`, `when` globs, `require` globs, an
optional `note`, and `mode = "any"` (default: one `require` match satisfies)
or `"all"`; globs are `fnmatch` against project-relative paths, `*` crosses
separators, `./` prefixes are normalised away. `/cc-enforcer:sync-gate check`
names a group that no file matches, because the loader is failing-open and
such a group stops guarding silently.

---

## 3. Layer 2 — Slash commands

**Wired in:** [`../commands/`](../commands/). Flat Markdown files whose YAML
frontmatter declares the command and whose body is the prompt the agent
receives.

| Command | Source | Use |
|---|---|---|
| `/cc-enforcer:checklist` | [`checklist.md`](../commands/checklist.md) | The eight-section pre-action / pre-finish checklist. |
| `/cc-enforcer:verify` | [`verify.md`](../commands/verify.md) | Re-verify the agent's recent claims through the verifier subagent. |
| `/cc-enforcer:edict` | [`edict.md`](../commands/edict.md) | `list / add / remove / reload / path` for Imperial Edicts; backed by [`manage_edicts.py`](../hooks/scripts/manage_edicts.py). |
| `/cc-enforcer:gc` | [`gc.md`](../commands/gc.md) | List, or with `--apply` delete, session-state files older than N days; backed by [`gc_state.py`](../hooks/scripts/gc_state.py). |
| `/cc-enforcer:i18n` | [`i18n.md`](../commands/i18n.md) | Report drift between every translation and the English skeleton; backed by [`i18n_check.py`](../hooks/scripts/i18n_check.py). |
| `/cc-enforcer:sync-gate` | [`sync-gate.md`](../commands/sync-gate.md) | `init / list / check / add / remove / path` for the project's rule-12 groups; backed by [`manage_sync_gate.py`](../hooks/scripts/manage_sync_gate.py), whose writes are validated by parsing back **and** by a real `load_file()` round-trip (a `require = []` entry is legal TOML the loader then discards). |

Links inside a command, skill, agent or prompt file are written
repo-root-relative (`rules/03-root-cause.md`): those files are prompt
payloads the agent resolves against the project root, not rendered pages.
Human-facing documents (`README*.md`, `docs/`, `rules/`) use file-relative
links, and `test_doc_sync.py` resolves from either base.

---

## 4. Layer 3 — Verifier subagent

**Wired in:** [`../agents/verifier.md`](../agents/verifier.md). Given the
`file:line` citations the main agent produced, it independently reads each
cited file, confirms the line exists and the content matches, and reports one
of five verdicts per citation — `intact` / `drift` / `missing` / `mismatch` /
`unverifiable`. It carries `Read`, `Grep` and `Glob` only: no `Edit`, `Write`
or `Bash`, so it cannot become the fixer and has no incentive to patch a
discrepancy quietly.

---

## 5. Layer 4 — Skills

**Wired in:** [`../skills/systematic-debug/SKILL.md`](../skills/systematic-debug/SKILL.md)
and [`../skills/repo-refresh/SKILL.md`](../skills/repo-refresh/SKILL.md).
Claude Code auto-invokes a skill when its `description` matches the prompt.
`systematic-debug` triggers on debugging language and walks the agent through
the seven questions of rule 02 — after building a fast, deterministic
reproduction loop — before any code change. `repo-refresh` triggers on
whole-repo audit language and runs rule 12's active half: a sweep of code and
prose for stale, outdated, redundant, wrong or drifted content, every finding
with `file:line` evidence, deletions gated on the user, closing with an offer
to register the coupling it found as sync-gate groups.

---

## 6. Layer 5 — The rule pack

**Source of truth:** [`../rules/`](../rules/) (English skeleton) and
[`../rules/zh/`](../rules/zh/) (Chinese translation), under the contract in
[`I18N.md`](./I18N.md): a translation tracks the skeleton file for file and
heading for heading, and the English text wins on drift. Each rule is plain
Markdown with a small YAML frontmatter (`id`, `title`, `severity`); every
other layer derives from it — the prompts are distillations, the commands and
skills cite rule ids, the verifier checks rule 05.

Any agent runtime that does not speak Claude Code's plugin protocol consumes
the rules directly:

```bash
cat rules/*.md    > cc-enforcer.txt     # English skeleton
cat rules/zh/*.md > cc-enforcer.txt     # Chinese translation
# prepend to the system prompt of OpenAI / Gemini / local models; or point
# Cursor / Cline / Aider at rules/ as a rule directory
```

The hard layers are Claude Code hooks and do not travel; the reasoning
discipline does. [`../rules/00-index.md`](../rules/00-index.md) is the short
form when the whole pack is too long for a system prompt.

---

## 7. Data flow at a glance

```
Session starts (startup / resume / clear / compact / fork)
    │
    ▼
SessionStart → inject_context.py --event SessionStart
    │  reads prompts/session-start.md + the edicts, emits the contract
    │  then, failing open: auto-GC (opt-in) · CLAUDE_ENV_FILE dedupe
    ▼
User submits a prompt
    │
    ▼
UserPromptSubmit → inject_context.py --event UserPromptSubmit
    │  reads prompts/user-prompt.md + the edicts, emits the reminder
    ▼
Agent calls Read / Edit / Write
    │
    ▼
PreToolUse (Read|Edit|Write) → read_guard.py
    ├─ Read                              → record path (if it exists) + baseline; ALLOW
    ├─ Edit/Write, target exists, unread → DENY (rule 04 + 08)
    ├─ Edit, target missing              → ALLOW (Claude Code rejects it)
    └─ otherwise, the content pipeline on new_string / content:
           patch marker (09) → secret (10) → path (11) → edict → rolling patch (09)
         any hit → DENY; all clear → record read + edit flag + edited_files; ALLOW

Agent calls Bash
    │
    ▼
PreToolUse (Bash) → bash_guard.py
    ├─ a static pattern / a force push / a must edict → DENY (rule 03 / edict)
    ├─ a register_read.py invocation                  → SHA-256 verified:
    │       match → record as read, ALLOW; otherwise DENY
    └─ nothing matched                                → ALLOW (silent)

Agent's reply ends
    │
    ▼
Stop → stop_guard.py
    ├─ no done-claim                         → clear the edit flag; ALLOW
    └─ done-claim → layers in order (b)(a)(c)(d)(e)(f)(g)(h)(i)
           first live failing layer → BLOCK with table + recovery + grace record
           all pass                 → clear the edit flag and the record; ALLOW

State: ${CLAUDE_PLUGIN_DATA}/sessions/<sid>.json (or the fallbacks in §2.7)

  /cc-enforcer:verify   → verifier subagent re-reads every cited file:line
  "fix this bug"        → systematic-debug skill: reproduction loop, then the 7 questions
  "audit the repo"      → repo-refresh skill: the whole-repo staleness sweep
```

---

## 8. Editing this plugin — connected-files map

What to re-check in the same change. The registered floor is
[`../.claude/cc-enforcer/sync-gate.toml`](../.claude/cc-enforcer/sync-gate.toml)
(Stop layer (i) enforces it on this repository); the release procedure is
[`CONTRIBUTING.md`](./CONTRIBUTING.md). Rows are sorted by path.

| If you edit… | Also re-check… |
|---|---|
| `.claude-plugin/plugin.json` | `.claude-plugin/marketplace.json` and `CHANGELOG.md` (the version gate holds all three to one number; `README*.md` badges too). Do **not** add `commands` / `agents` / `skills` / `hooks` path fields for the standard locations: Claude Code auto-discovers them, and the explicit fields make `claude plugin install` fail with a duplicate-hooks or invalid-agents error. |
| `.claude-plugin/marketplace.json` | `.claude-plugin/plugin.json` (version), `README.md` (install steps). |
| `.claude/cc-enforcer/sync-gate.toml` | `hooks/scripts/lib/sync_gate.py` (schema), `rules/12-repo-wide-sync.md` (the documented example), this section. |
| `.github/workflows/*.yml` | `tests/test_version_sync.py` — `fetch-depth: 0` is the tag gate's input; a depth-1 checkout makes the released-heading check skip itself while the run stays green. |
| `CHANGELOG.md` | `.claude-plugin/plugin.json` (the newest released heading must equal it), `git tag` (every released heading needs one, or a registration in `UNTAGGED_BY_RECORD`). |
| `README.md` / `README.zh.md` | Each other (hand-maintained mirrors, same heading sequence); the pinned sentences `tests/test_doc_sync.py` derives from the code (counts, structure trees, hedge examples, coverage bars, links); the fenced guard samples, which are copies of catalog output. |
| `agents/verifier.md` | `commands/verify.md` (invocation), §4. |
| `commands/*.md` | §3, `README.md` (the command table, whose count is pinned); `commands/checklist.md` also `tests/test_doc_sync.py` (its `## A.`–`## H.` section count). |
| `demo/**` | `demo/out/*.svg` are regenerated by `python demo/run_demo.py --svg` and compared byte for byte by `tests/test_demo.py`; a wording change in any guard changes the image. |
| `docs/*.md` | `docs/README.md` (the index), `tests/test_doc_sync.py` (`ENGLISH_DOCS` / `CHINESE_DOCS` registries, `DOC_ONLY_IDENTIFIERS`, link resolution). |
| `hooks/hooks.json` | §2 (the event table), `tests/test_doc_sync.py` (exactly four scripts and four events are registered). |
| `hooks/scripts/bash_guard.py` | `hooks/hooks.json` (matcher), §2.4, `lib/shellcmd.py`, `lib/messages*.py` (the deny texts), `tests/test_bash_guard.py` (a positive and a nearby negative for every pattern; register-flow cases), `tests/test_startup_cost.py`. |
| `hooks/scripts/bench_hooks.py` | `README*.md` §6 (they quote its output and name it as the reproduction); it must never appear in `hooks.json`. |
| `hooks/scripts/gc_state.py` | `commands/gc.md`, `hooks/scripts/inject_context.py` (the auto-GC callee), `lib/state.py` (`state_dir`, `AUTO_GC_MARKER`), `tests/test_gc_state.py`. |
| `hooks/scripts/i18n_check.py` | `docs/I18N.md`, `commands/i18n.md`, `tests/test_i18n_sync.py`; the two computed key families it expands for the message catalogs. |
| `hooks/scripts/inject_context.py` | `hooks/hooks.json`, `prompts/*.md` (both tiers, both languages), §2.2, `tests/test_inject_context.py` (content, budget and constraint-completeness gates), `tests/test_startup_cost.py`. |
| `hooks/scripts/manage_edicts.py` | `commands/edict.md`, `lib/edicts.py` (both resolvers), `lib/tomlio.py` (the shared writer), `tests/test_edicts.py`. |
| `hooks/scripts/manage_sync_gate.py` | `commands/sync-gate.md`, `lib/sync_gate.py` (`default_project_path` for writes, `config_path` for reads — conflating them is the defect the CLI shipped with), `lib/tomlio.py`, `tests/test_manage_sync_gate.py`. |
| `hooks/scripts/read_guard.py` | `hooks/hooks.json`, `lib/state.py`, `lib/srclex.py`, `lib/editscale.py`, `lib/messages*.py`, §2.3, `rules/09` / `10` / `11` (the rules it enforces, both languages), `prompts/*.md` (the DENY rows), `tests/test_read_guard.py` (every allow with its deny twin), `tests/test_startup_cost.py`. |
| `hooks/scripts/register_read.py` | `hooks/scripts/bash_guard.py` (the authoritative check lives there), §2.4, `tests/test_register_read.py`. |
| `hooks/scripts/stop_guard.py` | `hooks/hooks.json`, `lib/state.py` (grace helpers, `did_edit_this_turn`), `lib/mdctx.py`, `lib/sync_gate.py`, `lib/messages*.py`, §2.5, `prompts/*.md` (the layer rows), `README*.md` (the nine-layer table and the hedge examples), `tests/test_stop_guard.py` (both directions for every pattern), `tests/test_startup_cost.py` (nothing may compile at import). |
| `hooks/scripts/lib/edicts.py` | `hooks/scripts/inject_context.py`, `read_guard.py`, `bash_guard.py`, `manage_edicts.py`, `docs/EDICTS.md`, `tests/test_edicts.py`, `tests/test_inject_context.py` (the elision boundary is keyed to the rendered row shape). |
| `hooks/scripts/lib/editscale.py` | `read_guard.py` (the frequency layer formats the live constants), `rules/09` (+ zh: the classification and exemption tables), `prompts/*.md`, `README*.md` (the coverage-bar samples are derived from it), `tests/test_editscale.py`, `tests/test_read_guard.py`. |
| `hooks/scripts/lib/envfile.py` | `inject_context.py` (the SessionStart call site), `tests/test_envfile.py` — the refusal twins in both directions. |
| `hooks/scripts/lib/hookio.py` | all four hook entry points, `tests/_helpers.py` (`ensure_ascii=False` is what makes the boundary reachable), `tests/test_hookio.py`. |
| `hooks/scripts/lib/lang.py` | `inject_context.py`, `lib/edicts.py`, `lib/messages.py`, `docs/I18N.md`. |
| `hooks/scripts/lib/mdctx.py` | `stop_guard.py` (both halves of layer (h) and the sync-marker attribution), `i18n_check.py` (the fence helper), `tests/test_audit_v026_models.py`, `tests/test_stop_guard.py`. |
| `hooks/scripts/lib/messages*.py` | all three guards; `messages_zh.py` must move with `messages_en.py` (key sets and placeholder fields, both directions — `i18n_check`); `i18n_check.py`'s computed key families; `tests/test_messages.py`, `tests/test_i18n_sync.py`; the fenced samples in both READMEs; `demo/out/*.svg`. |
| `hooks/scripts/lib/projroot.py` | `lib/edicts.py`, `lib/sync_gate.py`, `lib/state.py` (they alias its name and layout); widening the root predicate widens where *both* configs are picked up — a security-shaped change. `tests/test_edicts.py`, `tests/test_sync_gate.py`. |
| `hooks/scripts/lib/shellcmd.py` | `bash_guard.py` (the force-push detector and the register parser, both directions), `tests/test_audit_v026_models.py`, `tests/test_bash_guard.py`. |
| `hooks/scripts/lib/srclex.py` | `read_guard.py` (every content detector and the rationale hatch — both directions), `tests/test_audit_v026_models.py`. |
| `hooks/scripts/lib/state.py` | `read_guard.py`, `stop_guard.py`, `bash_guard.py` (registration), `gc_state.py`, `.gitignore` (the state dir stays ignored), §2.7, `tests/test_read_guard.py`, `tests/test_stop_guard.py`. |
| `hooks/scripts/lib/sync_gate.py` | `stop_guard.py` (layer (i)), `manage_sync_gate.py`, `rules/12` (+ zh), `.claude/cc-enforcer/sync-gate.toml`, §2.8, `tests/test_sync_gate.py`, `tests/test_stop_guard.py`. |
| `hooks/scripts/lib/tomlio.py` | both config loaders and both config CLIs; a change here changes how every hand-edited config degrades. `tests/test_edicts.py`, `tests/test_sync_gate.py`, `tests/test_manage_sync_gate.py`. |
| `prompts/*.md` | `prompts/zh/*.md` (same heading sequence, then `python hooks/scripts/i18n_check.py`), `docs/I18N.md`, §2.2, `tests/test_inject_context.py` (needles, the 10,000-character budget with a 120-character root and three edicts, the reminder's size cap and its derived constraint set). Growing a prompt spends the edict allowance. |
| `rules/<nn>-*.md` | `rules/zh/<nn>-*.md`, `rules/00-index.md` (+ zh), `prompts/*.md`, `docs/RULES.md`, `commands/checklist.md`, `tests/test_inject_context.py`; `rules/09` (+ zh) must keep naming the whole Bash deny set (`tests/test_doc_sync.py`). |
| `skills/repo-refresh/SKILL.md` | `rules/12`, `rules/06`, `rules/09`, `commands/sync-gate.md` + `manage_sync_gate.py` (the skill tells the agent to register findings as groups; verify the claim from both ends), §5. |
| `skills/systematic-debug/SKILL.md` | `rules/02`, `rules/03`, §5. |
| `tests/_helpers.py` | every `tests/test_*.py`. |
| `tests/test_*.py` | `tests/README.md` (the inventory), `README*.md` (the pinned test count). |
