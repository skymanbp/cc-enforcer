---
id: "11"
title: "No non-essential path dependency"
severity: must
---

# Rule 11 — No non-essential path dependency

**Enforced by:** `PreToolUse(Edit|Write)` — DENY when new code carries a user-home absolute path (`C:\Users\<name>\…`, `/home/<name>/…`, `/Users/<name>/…`, with raw or escaped separators), a literal `$HOME` / `%USERPROFILE%`, or a quoted `~/…` — unless an adjacent comment carries a rationale token. System roots, bare drive letters and relative paths are not flagged; prose documents and lockfiles are not scanned.

## Principle

> **A filesystem path that is specific to one machine, one user, or one
> checkout must not be baked into code as an absolute literal.** Derive
> paths from a base the runtime already knows — the plugin root, the
> current working directory, an environment variable, or a passed-in
> argument.

A machine-specific absolute path is a portability landmine: it works on
the author's box and breaks on every other machine, CI runner, and
container. This repo lived that failure — a hotfix once repaired a
Windows path-portability bug in its *own* hook (a `~`-containing runner
`$TEMP` the path regex could not parse). Rule 11 makes "don't hardcode a
user-home path" a write-time, root-cause discipline (rule 03).

## Scope — user-home roots are the hard class

Faithful to the conservative-detector philosophy (prefer false negatives
to false positives), only paths anchored at a **user-specific root** are
refused at write time — the class that is almost never legitimately
portable:

| Class | Hard-enforced? |
|---|---|
| Windows user-home absolute path (`C:\Users\<name>\…`, raw or escaped separators) | ✅ yes |
| POSIX user-home absolute path (`/home/<name>/…`, `/Users/<name>/…`) | ✅ yes |
| Shell home variable in a literal (`$HOME`, `%USERPROFILE%`) | ✅ yes |
| User-home tilde path in a string literal (`"~/…"`) | ✅ yes |
| System paths (`/etc/…`, `/usr/…`, bare `C:\`) | ❌ soft guidance only |
| Relative paths (`./data`, `../lib`) | ❌ allowed (already portable) |

System roots and bare drive letters are deliberately *not* flagged: they
are often legitimately fixed, and a hard detector for them would fire on
correct code. Relative paths are the desired outcome, not a violation. A
`/home/<x>/` segment glued to a hostname is not flagged either — in
`https://host.test/home/alice/dashboard` it is a URL route, not a
filesystem path — while a `file:///home/…` URI still matches, because
that IS a machine path. Prose documents and lockfiles are exempt: docs
carry illustrative paths, and lockfiles legitimately record resolved
absolute ones (the `requirements*.txt` / `constraints*.txt` carve-out
from rule 10 applies here too).

The portable alternatives the detector wants you to reach for:
`Path(__file__).resolve().parent…`, `os.environ["CLAUDE_PLUGIN_DATA"]`,
`Path.home()` computed at runtime (not a literal), a CLI argument, or a
path relative to the repo root.

## Marking an essential path

The user's scope is *non-essential* path dependency. An essential,
genuinely-fixed path (a documented example, a test fixture pinned to a
known layout, a platform path that truly cannot move) is allowed through
when the offending line, or an immediately adjacent line (±1), carries a
rationale token **inside a comment** — the same hatch, and the same token
list, as rule 10 (`because` / `因为` / `essential` / `example` /
`fixture` / `placeholder` / `sample` / `test data` …). A bare user-home
path with no rationale = the non-essential case = **DENY**.

## Must do (MUST)

1. **Derive, don't hardcode** — compute paths from the plugin root, cwd,
   an env var, or an argument, so the same code runs on any machine.
2. **Prefer relative paths** — anchor data/config relative to the repo or
   module, not to `/home/<you>` or `C:\Users\<you>`.
3. **Mark genuine fixtures** — if a path really must be a fixed literal,
   add an adjacent rationale so the check can tell intent from laziness.

## Must not (MUST NOT)

- ❌ Bake `C:\Users\<name>\…` or `/home/<name>/…` into shipped code.
- ❌ Hardcode `$HOME` / `%USERPROFILE%` / `~/…` as a string literal.
- ❌ Assume the author's directory layout on every other machine.
- ❌ Suppress the detector with a false rationale on a real dependency.

## Relationships

| Relationship | Note |
|---|---|
| 11 vs 03 | 03 says fix the root cause; 11 makes "derive the path, don't hardcode the machine" a hard, write-time portability fix. |
| 11 vs 09 | Same mechanism (write-time content detector with a why-comment escape hatch); 09 targets suppression markers, 11 targets machine-specific paths. |
| 11 vs 10 | Sibling detectors; 10 is *what* is inlined (secrets), 11 is *where* it points (machine-specific paths). |

## Self-check triggers

- About to paste an absolute path that starts with `C:\Users\` or
  `/home/` or `/Users/`.
- Writing `$HOME` / `%USERPROFILE%` / `"~/…"` as a literal in code.
- "It works on my machine" is the only reason the path is correct.
- Copying a path from your own shell straight into shipped source.

## Termination condition

Writing an absolute filesystem path is allowed only when **one** of:

1. It is derived at runtime from a known base (plugin root / cwd / env /
   argument), not a machine-specific literal; or
2. It is an obvious example / fixture (marked as such); or
3. An adjacent rationale explicitly justifies it as essential.

Otherwise → **non-essential path dependency**, return to rule 03 and
derive it.
