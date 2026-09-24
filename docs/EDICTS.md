# Imperial Edicts — user-defined hard rules

> Project-specific hard rules that ride on top of cc-enforcer's built-in
> 12 rules: a regex you register becomes a `PreToolUse` DENY.

---

## 1. Why Imperial Edicts

The built-in 12 rules cover general AI laziness patterns (verify don't
guess, root cause not symptom, etc.). But every project has its own red
lines that no general rule can cover:

- "No mongoose — this project uses prisma."
- "Every API call goes through `src/api/client.ts`."
- "No direct fetch inside a React component."
- "No await inside .map."
- "Every migration file ships a matching rollback."

These are **per-project**, **user-defined**, and ideally **physically
enforced** (not just soft reminders that get ignored). An edict is that.

The metaphor: built-in rules are constitutional law; an edict is project
royal decree — more specific, top priority, can override default
suggestions, but cannot override constitutional safeguards (the built-in
hooks still run first).

---

## 2. File format

Location: `${CLAUDE_PROJECT_DIR}/.claude/cc-enforcer/edicts.toml`.
Fallback: `~/.claude/cc-enforcer/edicts.toml` (personal global).

Format: TOML, array of tables.

```toml
[[edicts]]
id = "E01"                                  # required: unique short id
text = "No mongoose — this project uses prisma"  # required: imperative text shown to the agent
severity = "must"                           # "must" (default) | "should"
deny_edit = ['''from ["']mongoose["']''']   # optional: regex list, matched against Edit/Write content
deny_bash = ['''npm (i|install) mongoose''']  # optional: regex list, matched against Bash commands
note = "Standardised on prisma; mongoose removed in PR #142"  # optional: rationale shown in deny reason

[[edicts]]
id = "E02"
text = "Every API call goes through src/api/client.ts"
severity = "should"                         # soft layer only: injected as reminder, NOT physically enforced
```

### Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `id` | yes | string | Unique short id (any string). Appears in deny reasons. |
| `text` | yes | string | Imperative one-liner the agent sees in the injection. |
| `severity` | no (default `must`) | `"must"` \| `"should"` | `must` = physically DENY on regex match. `should` = soft reminder only. |
| `deny_edit` | no | list[string] | Regexes matched against Edit/Write `new_string` / `content`. |
| `deny_bash` | no | list[string] | Regexes matched against Bash `command`. |
| `note` | no | string | Optional context shown in the deny reason (e.g. PR link, ticket id). |

### Regex tips

- **Use triple-quoted strings** (`'''...'''`) — TOML's single-quoted
  literal strings need no escaping inside, so your regex stays readable.
- Regexes use Python's `re` syntax. Test interactively with
  `python -c "import re; print(re.search(r'PATTERN', 'TEST_STRING'))"`.
- Each edict can have multiple `deny_edit` / `deny_bash` patterns; any
  match triggers the deny.
- A broken regex is **skipped with a stderr warning**; the other
  patterns in the same edict still apply.

---

## 3. Enforcement contract

| Layer | When | Behavior |
|---|---|---|
| Soft (SessionStart) | At session boot, and again after every compaction | All edicts (must + should) injected as a markdown table under the contract. |
| Soft (UserPromptSubmit) | Every user turn | The same table, without its intro and footer sentences, under the per-turn reminder. |
| Hard (`PreToolUse(Edit\|Write)`) | When agent calls Edit / Write | For each `must` edict with `deny_edit`: scan `new_string` / `content`. First match → DENY with reason naming the edict id. |
| Hard (`PreToolUse(Bash)`) | When agent calls Bash | For each `must` edict with `deny_bash`: scan `command`. First match → DENY. |

The loader re-reads the file on every hook event, so an edict added
mid-session is live on the next prompt. When the injection would exceed
Claude Code's 10,000-character hook-output cap, the edict table is what
yields — clipped at whole rows, with a notice of how many were elided — and
the contract stays whole ([`ARCHITECTURE.md`](./ARCHITECTURE.md) §2.2).

### Language

Both the injected block and the DENY reason follow `CC_ENFORCER_LANG`;
English is the default and unknown codes fall back to English:

| `CC_ENFORCER_LANG` | Injection banner | DENY headline |
|---|---|---|
| unset / `en` / unknown | `🏛️ Imperial Edicts (project hard rules; priority > builtin 12)` | `cc-enforcer · Imperial Edict E01 violation` |
| `zh` | `🏛️ 圣旨（项目自定义硬规则；优先级 > 通用 12 条）` | `cc-enforcer · 圣旨 E01 violation` |

The edict `text` / `note` strings themselves are passed through verbatim —
they are whatever you wrote in `edicts.toml`. Only the framing switches.

### Check order

**Built-in rules run first, with one documented exception.** In
`read_guard.py`:

1. read-before-edit guard (rule 04 + 08)
2. patch-style marker guard (rule 09)
3. hardcoded-secret guard (rule 10)
4. path-dependency guard (rule 11)
5. **Edict scan**
6. rolling-patch frequency guard (rule 09) — the one built-in layer that
   runs *after* the edict scan, because it is a counter over the session
   rather than a content check, and it must not increment for a write that
   some earlier layer is going to deny anyway

In `bash_guard.py`:

1. static deny patterns: `--no-verify` / `--no-gpg-sign` / `chmod 777` /
   `git rebase --skip` / `--break-system-packages` / `rm -rf` on a root
   path (rule 03)
2. force-push detection (parsed through `lib/shellcmd`, not a regex)
3. **Edict scan**
4. the `register_read.py` escape hatch — last, so a command that contains a
   registration *and* something to deny (`register_read.py … && git push
   --force`) is denied and never mutates session state

You cannot define an edict that whitelists `--no-verify` — the built-in
hook fires before reaching the edict layer.

---

## 4. Managing edicts

### Slash command (`/cc-enforcer:edict`)

```
/cc-enforcer:edict list
/cc-enforcer:edict add E01 "No mongoose" --must --deny-edit 'mongoose' --deny-bash 'npm i mongoose'
/cc-enforcer:edict remove E01
/cc-enforcer:edict path
```

### Direct CLI

```bash
python "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/manage_edicts.py" list
python "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/manage_edicts.py" add ID "TEXT" [--must|--should] \
    [--deny-edit REGEX]* [--deny-bash REGEX]* [--note NOTE] [--global]
python "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/manage_edicts.py" remove ID [--global]
python "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/manage_edicts.py" path
```

#### `--global` flag

By default `add` writes to `${CLAUDE_PROJECT_DIR}/.claude/cc-enforcer/edicts.toml`
(team-shareable, recommended). Pass `--global` to write to
`${HOME}/.claude/cc-enforcer/edicts.toml` instead — useful for
personal rules that should apply across all your projects (e.g. "never
let claude touch my dotfiles", "always use my preferred test runner").

`remove` without `--global` looks in the project file first then falls
back to the global file; pass `--global` to restrict removal to the
global file only.

The loader (used by all hooks) tries project first then global, so
project edicts take precedence when both files define the same id.

### Hand-edit

The file is small enough to edit directly. Changes take effect on the
next hook event — no reload needed (the loader reads disk on every
invocation).

---

## 5. Examples

### Block a specific library

```toml
[[edicts]]
id = "E01"
text = "No mongoose — this project uses prisma (migrated in PR #142)"
severity = "must"
deny_edit = [
    '''from ["']mongoose["']''',
    '''require\(["']mongoose["']\)''',
    '''import .* from ["']mongoose["']''',
]
deny_bash = [
    '''npm\s+(i|install)\s+.*\bmongoose\b''',
    '''yarn\s+add\s+.*\bmongoose\b''',
]
note = "see PR #142 / RFC 0007"
```

### Enforce architecture boundary (soft)

```toml
[[edicts]]
id = "E02"
text = "Every HTTP call goes through src/api/client.ts; no bare fetch or axios"
severity = "should"  # soft -- complex to regex perfectly, prefer reminder
```

### Block a known footgun

```toml
[[edicts]]
id = "E03"
text = "No await inside .map / .forEach — use Promise.all with map"
severity = "must"
deny_edit = [
    '''\.(map|forEach)\s*\(\s*(?:async\b[^)]*=>|\([^)]*\)\s*=>\s*\{[^}]*\bawait\b)''',
]
note = "It serialises what should be concurrent; use Promise.all(arr.map(async ...))"
```

---

## 6. Limitations

These are decided, not pending — a limitations section that doubles as a
wish-list is how a permanent constraint gets read as a temporary one.

- **No per-session ephemeral edicts** (`/cc-enforcer:edict add --session ...`).
  The blocker is structural: the CLI is a Bash subprocess and has no
  `session_id`; only the hook payload carries one. A `should` edict already
  covers the light-touch case. Use the file, or pass `--should`.
- **No exception mechanism** — an edict either matches or it doesn't.
  If you want a per-file exemption, write a more specific regex or
  remove the edict.
- **Regex is the only matcher.** AST-based / semantic matching is out of
  scope; if you need it, write a custom hook in `hooks/hooks.json`.

The enforcement contract's history starts at the `[0.12.0]` entry of
[`CHANGELOG.md`](../CHANGELOG.md).
