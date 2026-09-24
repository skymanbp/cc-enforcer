"""English message catalog — the skeleton, and the source of truth.

Every user-facing string the three guards emit lives here, keyed by a
dotted name. A translation is the same key set with translated values
(`messages_zh.py`); `messages.py` resolves per key and falls back to
this module, so a partial translation degrades to English rather than to
a blank message.

Why a Python dict and not a `.md` / `.toml` file beside `prompts/`: these
strings are read on EVERY hook invocation, which sits in the critical
path of the agent's tool calls (README section 6 publishes that cost).
An import is compiled once to `.pyc`; a parse is paid every time. The
gate is also stronger on a dict — `i18n_check.py` can compare exact key
sets and per-key placeholder sets, where a markdown translation can only
be compared on heading structure.

This file was GENERATED from the constants the guards carried through
v0.37, so the English output is byte-identical to what shipped for the
thirty-seven releases before it. Edit it by hand from here on; the
generator was a one-off and is not part of the build.

Placeholders are `str.format` fields. `i18n_check.py` asserts that every
translation carries the same key set AND the same placeholder set per
key — a translation that drops a field silently changes what a guard
tells the user, and one that invents a field raises at format time, in
the hook, in front of the user.
"""

from __future__ import annotations

MESSAGES: dict[str, str] = {
    # ---- stop_guard ------------------------------------------------------
    'stop.recovery.a': """Your reply claims completion but carries no convergence
evidence: no `$ ` shell prompt line, no test counts (`Ran N tests` /
`N passed`), no fenced output block, no `verified` / `re-ran` /
`validated` statement.

Per rule 06 (rules/06-verify-convergence.md), paste the original failing
command with its now-passing output, or a `pytest` / `unittest` /
`npm test` run with counts. If you verified mentally and skipped writing
it down, write it down now — the concrete command and its output.""",
    'stop.tldr.a': 'You said it is done but showed no evidence — paste one command and its output and this passes.',
    'stop.fail_note.a': 'no convergence evidence',
    'stop.layer_label.a': 'rule 06 — no evidence',
    'stop.layer_keyword.a': 'rule 06',
    'stop.recovery.b': """Your reply pairs a completion claim with hedged language
within ~50 characters. Per rule 01 (rules/01-verify-dont-guess.md),
confident verification cannot coexist with "I think / I believe /
I guess / maybe / probably / kinda / sort of" near the done-claim.

Pick one:
  • Drop the hedge and state the result with concrete output, or
  • Drop the done-claim and say explicitly "not yet verified" so
    the user decides whether to ship.

A hedge marker is not a rhetorical flourish — it signals you are not
sure. If you are sure, write so; if you are not, say so.""",
    'stop.tldr.b': 'You claimed it works and hedged in the same breath — drop the hedge, or say plainly that it is unverified.',
    'stop.fail_note.b': 'hedge near done-claim',
    'stop.layer_label.b': 'rule 01 — hedge near done-claim',
    'stop.layer_keyword.b': 'rule 01 + hedge',
    'stop.recovery.c': """Your reply has evidence but does not surface the rule-06
self-quiz. Pass condition is either:

  (a) an explicit marker — `rule 06`, `convergence`, `self-quiz`
      (the reply schema's `convergence:` field counts); OR
  (b) ≥ 2 of the 4 self-quiz questions:
        1. Really solved?  Specific evidence, not just "no error"
        2. Better solution?  Compared against alternatives
        3. What is unverified?  Enumerate what was not tested
        4. Is the verification reasonable?  Does it exercise the
           root-cause chain, or only its symptom?

Tests passing alone is not convergence. Surface the self-quiz now.""",
    'stop.tldr.c': 'Evidence but no self-quiz — answer really solved / better solution / what is unverified / is the check reasonable.',
    'stop.fail_note.c': 'self-quiz / marker absent',
    'stop.layer_label.c': 'rule 06 — self-quiz missing',
    'stop.layer_keyword.c': 'rule 06 self-quiz',
    'stop.recovery.d': """You passed rule-06 convergence on the part you edited, but
your reply does not surface rule-07 task fidelity (a different axis:
"did I deliver everything the user asked for, at the standard
requested?").

Pass condition is either:
  (a) an explicit marker — `rule 07`, `task fidelity`,
      `request coverage`, `request fidelity`, `no degradation`,
      `no omission`, `no scope creep`, `covered all`,
      `all requested`; OR
  (b) ≥ 2 of 3 fidelity questions:
        1. Coverage — decompose the original request, list which
           sub-items you did vs. didn't, and why
        2. Standard — for each modifier word (mandatory / strict /
           complete / every / all): did it land as a hard action,
           or stay a soft note in a document?
        3. Fidelity — any concept swap, scope creep, trimmed
           requirement or buried TODO?

Re-read the user's *original* message, not your in-flight restatement.""",
    'stop.tldr.d': "You never went back to the user's original request — list what you did, and what you dropped or downgraded.",
    'stop.fail_note.d': 'fidelity marker / quiz absent',
    'stop.layer_label.d': 'rule 07 — task fidelity missing',
    'stop.layer_keyword.d': 'rule 07 fidelity',
    'stop.recovery.e': """You modified a file this turn but did not surface the
rule-08 (read-before-edit / think-before-write) closing markers.

Pass condition is either:
  (a) an explicit marker — `rule 08`, `read-before-edit`,
      `think-before-write`; OR
  (b) ≥ 3 of 6 rule-02 keywords:
        architecture
        responsibility
        root cause
        solution / approach
        downstream / impact / connected
        invariant / risk

If you did the rule-08 work in chain-of-thought but didn't surface it
in the final reply, surface it now.""",
    'stop.tldr.e': 'You edited a file without showing your reasoning — name the root cause, the architecture and the solution.',
    'stop.fail_note.e': 'rule-08 marker / 3+ keywords absent',
    'stop.layer_label.e': 'rule 08 — read-before-edit / think-before-write',
    'stop.layer_keyword.e': 'rule 08',
    'stop.recovery.f': """You modified a file this turn but did not surface the
rule-09 systematic-modification triplet (root cause + impact + solution).

Pass condition is either:
  (a) an explicit marker — `rule 09`, `systematic modification`,
      `patch-style`, `non-patch`; OR
  (b) **all three** of the triplet keywords in the same reply:
        • root cause
        • impact / blast radius / downstream
        • solution / approach / alternative

If the edit was actually patch-style (one local suppression, no impact
analysis, no alternative considered), redo it systematically or flag
the half-finish to the user.""",
    'stop.tldr.f': 'You edited a file but the root cause / impact / solution triplet is incomplete — finish it before signing off.',
    'stop.fail_note.f': 'rule-09 marker / triplet incomplete',
    'stop.layer_label.f': 'rule 09 — systematic-modification triplet',
    'stop.layer_keyword.f': 'rule 09',
    'stop.recovery.g': """Your reply claims to have edited / created / modified files,
but the on-disk state contradicts at least one of those claims:

{contradictions}

Per rule 01 (verify, don't guess) + rule 06 (verify convergence), a
claim about your own actions must be true. If you said "I edited X.py"
and X.py's mtime still matches what it was when you first saw it this
session, then the Edit was DENIED by another hook (check earlier in the
transcript), landed on a different file, or made no net change. Retry
the edit, correct the path, or withdraw the claim.

This layer fires only on a contradiction: a file with no baseline (you
never Read it) is not checked, and a change you forgot to mention is not
an error. If you did change the file through another tool, say so and
let the user decide.""",
    'stop.tldr.g': 'You claimed you edited a file whose bytes never changed — make the edit, or withdraw the claim.',
    'stop.fail_note.g': 'file-edit claim contradicts disk state',
    'stop.layer_label.g': 'rule 01+06 — file-claim verification',
    'stop.layer_keyword.g': 'rule 01 + 06 file-claim',
    'stop.recovery.h': """Your reply claims completion but does not end with a
plain-language TL;DR.

Per the reply schema, every done-claim reply must close with a
one-sentence takeaway the user can read at a glance. Add either:

  • The schema's final field:  tldr: "<one plain sentence>"
  • A line starting with `tldr:` or `TL;DR:`

The sentence should say, in plain words: what you actually did, what the
result was, and whether the user needs to do anything next. Not a restate
of the rule checks — a human takeaway.

Example:
  tldr: "Added the tldr layer to the Stop hook; 203 tests green; ready to ship."
""",
    'stop.tldr.h': 'The reply has no one-line takeaway — add a tldr: "..." line and this passes.',
    'stop.fail_note.h': 'tldr / TL;DR absent',
    'stop.layer_label.h': 'TL;DR — plain-language summary missing',
    'stop.layer_keyword.h': 'TL;DR',
    'stop.recovery.i': """One or more of this project's co-update groups
(.claude/cc-enforcer/sync-gate.toml) are unmet for this session's edits:

{violations}

Per rule 12 (rules/12-repo-wide-sync.md), editing a file that has
registered downstream/reference siblings requires either:

  (1) editing at least one file matching the group's `require` globs in
      the same session (co-update the references, docs, tests,
      translations that depend on what you changed), or
  (2) explicitly acknowledging the check in your reply with a sync
      marker — e.g. a line like:
        sync-check: <why the require side needs no change>

Silently editing only the `when` side is exactly the stale-reference
laziness rule 12 exists to stop. Check each listed group now: update
the co-files, or say out loud why they are already correct.""",
    'stop.tldr.i': 'You edited one side of a registered pair and not the other — co-update it, or say in one line why it is fine.',
    'stop.fail_note.i': 'sync-gate group unmet',
    'stop.layer_label.i': 'rule 12 — repo-wide sync gate',
    'stop.layer_keyword.i': 'rule 12 sync-gate',
    'stop.recovery.h_long': """Your reply has a TL;DR, but at least one of its items is
too long to be one:

  item ({length} columns > {cap} cap): {snippet!r}

Each tldr item is ONE sentence — cause, action, outcome — within {cap}
display columns. The unit is columns, not characters: an ASCII character
costs 1, a CJK character 2 (an all-CJK item is about {cjk_cap} of them),
a combining mark 0, and the number quoted above is that count. Several
things to report → one short item per line, each within the cap:

  tldr:
    - "Fixed X: the root cause was A, and the suite is green."
    - "Co-updated B's references; no behaviour change."

Drop process detail, not the outcome — the body already carries the
detail. An item that is only slightly over is usually two sentences
joined by a comma: split them into two items.""",
    'stop.one_shot_footer': '(Grace is per layer: this layer will not block again in the current recovery sequence, but any other layer still failing will. Fix what the FAIL row names; the sequence resets on the next allowed Stop.)',
    'stop.headline': 'cc-enforcer · Stop check FAILED at Layer {layer} [{label}]',
    'stop.table_header': """| Layer | Rule | Status      | Note                              |
|-------|------|-------------|-----------------------------------|""",
    'stop.status.pass': '✅ Pass',
    'stop.status.fail': '❌ **FAIL**',
    'stop.status.pending': '⏸  pending',
    'stop.status.na': '—  n/a',
    'stop.note.non_edit_turn': '(non-edit turn)',
    'stop.note.not_evaluated': '(not evaluated)',
    'stop.matched_prefix': 'Done-claim matched',
    'stop.recovery_header': '[Recovery — {keyword}]',
    'stop.tldr_prefix': 'In plain words',
    # ---- read_guard ------------------------------------------------------
    'read.deny.unread': """cc-enforcer · rule 04 + 08 violation (read-before-edit)

Tool: {tool_name}
Target: {file_path}

This file exists on disk but has not been Read (or Written) in this
session. Per rule 04 (rules/04-full-context.md) + rule 08
(rules/08-read-before-edit-think-before-write.md), an edit must be
preceded by a complete reading of the target, so you know the
surrounding architecture and downstream impact.

To proceed: Read this file (the whole file, not just the diff context),
then retry the {tool_name}.

If you HAVE Read it this session and the guard still denies (Claude Code
occasionally serves a Read from its result cache without firing the
hook), register the file as read -- as TWO SEPARATE Bash calls. A
chained form (`&&`, `||`, `;`, a pipe, a command substitution) earns no
credit even though the script still prints "register_read: ok".

  Bash call 1 -- SHA-256 of the file currently on disk:
  python -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' PATH

  Bash call 2 -- register, with NOTHING chained before or after it
  (HEX = the digest printed by call 1):
  python "${{CLAUDE_PLUGIN_ROOT}}/hooks/scripts/register_read.py" --file PATH --hash HEX

The Bash hook recomputes the hash from disk and registers only on a
match, so the escape hatch cannot bypass the read requirement.
""",
    'read.deny.patch': """cc-enforcer · rule 09 violation (patch-style new_string)

Tool: {tool_name}
Target: {file_path}
Pattern matched: {pattern_label}

Snippet (the offending segment in your new_string):
{snippet}

Per rule 09 (rules/09-systematic-modification.md), the modification
you are trying to commit contains a "patch marker" that silences
type / lint / test / error handling **without justifying why**.

Allowed forms require a why-comment on the same line or an
immediately adjacent line, containing one of: `because`, `why`,
`reason`, `rationale`, or a concrete justification (issue id / spec ref /
clear technical rationale). Bare suppressions are not allowed.

Examples of acceptable forms:

  # noqa: E501  -- URL string exceeds 100 chars; splitting hurts readability
  LONG_URL = "https://..."

  // @ts-ignore: third-party lib has incomplete type, see issue #1234
  const result = legacy.foo();

If you actually meant to fix the underlying issue (rule 03), do that
instead of suppressing the signal. If the suppression is truly
warranted, add the rationale comment and retry. If you genuinely need
to bypass this guard, surface the deny to the user and let them edit
manually -- the discipline exists to flag laziness, not block you.
""",
    'read.deny.hardcode': """cc-enforcer · rule 10 violation (non-essential hardcoding)

Tool: {tool_name}
Target: {file_path}
Pattern matched: {pattern_label}

Snippet (the offending segment in your content):
{snippet}

Per rule 10 (rules/10-no-hardcoding.md), a value that by design belongs
in configuration, an environment variable, a secret store or a parameter
has been inlined as a literal. Credentials, API keys, tokens and
private-key material never go into source.

To proceed, do one of:

  (1) **Externalize it** (preferred, rule 03 root cause), e.g.
        api_key = os.environ["API_KEY"]          # not a literal
      with the real value only in an untracked .env / secret store.

  (2) **If it is genuinely a placeholder / example / test fixture**, make
      that visible: an obvious placeholder value (`example`, `changeme`,
      `your-`, `<...>`, `${{...}}`, `dummy`, `redacted`) OR an adjacent
      why-comment naming it as such (a token from: essential / example /
      fixture / placeholder / sample / test data).

  (3) **Stop and surface**: if the hardcoding is truly unavoidable, tell
      the user and let them decide -- do not silently commit a secret.

Prose docs (.md / .rst / .txt / .adoc) and lockfiles are exempt; this
detector targets freshly authored *code*.
""",
    'read.deny.pathdep': """cc-enforcer · rule 11 violation (non-essential path dependency)

Tool: {tool_name}
Target: {file_path}
Pattern matched: {pattern_label}

Snippet (the offending segment in your content):
{snippet}

Per rule 11 (rules/11-no-path-dependency.md), a machine-specific
absolute path -- a user-home directory, or a shell home variable baked
into a string literal -- has been committed into code. It breaks the
moment the code runs on another machine, another OS, or in CI.

To proceed, do one of:

  (1) **Derive the path at runtime** (preferred, rule 03 root cause):
        base = Path(__file__).resolve().parent          # module-relative
        base = Path(os.environ["CLAUDE_PLUGIN_DATA"])    # from a config var
      A project-root marker, an env var, tempfile, or a passed-in
      argument -- never a literal user directory.

  (2) **If the path is genuinely essential** (a fixed OS location that is
      identical on every target machine), add an adjacent why-comment
      saying so (a token from: essential / because / why / example /
      fixture / sample).

  (3) **Stop and surface**: if portability truly cannot be achieved, tell
      the user rather than silently hardcoding your own machine.

Prose docs (.md / .rst / .txt / .adoc) and lockfiles are exempt; this
detector targets freshly authored *code*.
""",
    'read.deny.rolling': """cc-enforcer · rule 09 violation (rolling-patch interception)

Tool: {tool_name}
Target: {file_path}
Rolling-patch counter: {current_count} small edit(s) already applied
this session; this would be attempt #{attempt_count} — at or above the
threshold of {threshold}.

Per rule 09 (rules/09-systematic-modification.md), repeated **small**
edits to one file with no **systematic** rewrite between them are
rolling patches: each fixes one symptom in isolation, and the aggregate
says the file's structure and root cause were never re-engaged.

Classification used here:
  small      = max(|old_string|, |new_string|) < {small_chars} chars
               AND max line count ≤ {small_lines}
  systematic = max chars ≥ {sys_chars} OR max line count ≥ {sys_lines}
               OR the change spans ≥ {ratio_pct}% of this file{scale_note}
               (resets the counter to 0)
  medium     = anything in between (does not count, does not reset)

Never counted, at any counter value:
  net reduction — new_string is SHORTER than old_string. A rolling patch
                  is an accretion; an edit that leaves the file smaller
                  than it found it cannot be one.
  bookkeeping   — only version / ISO-date literals differ and every other
                  byte is identical (in prose documents, bare integers
                  count too). Bumping a version number is not a fix.

To proceed, do one of:

  (1) **Systematic rewrite**: combine the pending fixes into ONE Edit (or
      Write) of ≥ {sys_lines} lines / ≥ {sys_chars} chars on
      `new_string` / `content`{cover_hint}. That resets the counter to 0
      for this file.

  (2) **Delete rather than add**: a net reduction is never counted, so
      removing the accretion is always allowed. Never pad an edit to
      clear a threshold — padding is what this gate exists to catch.

  (3) **Stop and surface**: tell the user "this file needs a systematic
      rewrite; please review my plan before I continue" and let them
      decide whether to relax the constraint or refactor the approach.

This is NOT the patch-marker check (your new_string carries no
suppression marker); it is the AGGREGATE check: too many small fixes
signal a comprehension gap, not a suppression.
""",
    'read.scale_note': ' — here, {lines_bar} of {file_lines} lines or {chars_bar} of {file_chars} chars',
    'read.cover_hint': ', or ≥ {lines_bar} lines / ≥ {chars_bar} chars — whichever bar you clear first',
    'stop.extra.hedge_matched': 'Hedge matched',
    'bash.register.header': 'cc-enforcer · register_read rejected',
    'bash.register.command_label': 'Command',
    'bash.register.needs_absolute': 'register_read needs an absolute --file path (got {got}).',
    'bash.register.missing_file': 'register_read: file does not exist on disk: {path}',
    'bash.register.bad_hash': 'register_read: --hash must be 64 lowercase hex chars (SHA-256). Got: {got}',
    'bash.register.hash_mismatch': 'register_read: hash mismatch.\n  --hash:  {claimed}\n  on-disk: {actual}\nEither you have not actually read the file, or it changed since you computed the hash. Re-Read with fresh content and retry.',
    'bash.register.not_persisted': 'register_read: the registration could not be persisted to session state (another process is holding the state file).\nNothing was recorded — retry in a moment, or simply Read the file again, which is the primary path this hatch exists to work around.',
    # ---- bash_guard ------------------------------------------------------
    'bash.deny': """cc-enforcer · rule {rule} violation (bypass pattern)

Pattern matched: {name}
Command: {command}

{explanation}
""",
    'bash.pattern.no_verify.name': '--no-verify (skipping commit hooks)',
    'bash.pattern.no_verify.explanation': 'The `--no-verify` flag skips git/commit hooks. Hooks exist to catch broken code; bypassing them ships broken code. Per rule 03 (rules/03-root-cause.md), fix the hook-failure root cause instead of bypassing the hook. If the user has explicitly instructed you to bypass, ask them to run the command manually rather than acting on their behalf.',
    'bash.pattern.no_gpg_sign.name': '--no-gpg-sign (skipping commit signature)',
    'bash.pattern.no_gpg_sign.explanation': 'Skipping GPG signing strips commit verification. If signing is broken, fix the signing setup. Per rule 03 (rules/03-root-cause.md), do not bypass verification to make a command go through.',
    'bash.pattern.chmod_777.name': 'chmod 777 (world-writable)',
    'bash.pattern.chmod_777.explanation': 'World-writable permissions (777) almost never solve the underlying access issue and introduce security risk. Per rule 03 (rules/03-root-cause.md), identify the actual user or process that needs access and grant it specifically (e.g., `chown` + a restrictive mode like 750 or 640).',
    'bash.pattern.rebase_skip.name': 'git rebase --skip (silently abandoning a conflict)',
    'bash.pattern.rebase_skip.explanation': "`git rebase --skip` abandons the conflicting commit silently rather than resolving the conflict. Per rule 03 (rules/03-root-cause.md), conflicts arise from real semantic divergence — skipping them loses code or hides design issues that surface for a reason. Either: (1) resolve the conflict (`git status` to see what's in conflict, edit, `git add`, `git rebase --continue`), (2) abort and pick a different rebase strategy (`git rebase --abort`), or (3) if you are absolutely sure the skipped commit is unnecessary, ask the user to run --skip manually.",
    'bash.pattern.break_system_packages.name': 'pip install --break-system-packages (bypassing PEP 668)',
    'bash.pattern.break_system_packages.explanation': '`--break-system-packages` bypasses the PEP 668 protection added in Python 3.11+ to prevent pip from modifying the system Python and breaking package-manager-installed software. Per rule 03 (rules/03-root-cause.md), the fix is to install into a venv (`python -m venv .venv && source .venv/bin/activate && pip install …`), pipx for tools, or the system package manager (`apt install python3-X`). Breaking the system Python to make one install succeed is the canonical symptom-over-root-cause anti-pattern.',
    # essential: this message's subject IS the home paths the guard refuses.
    'bash.pattern.rm_rf_root.name': 'rm -rf on root / $HOME / ~',
    # essential: this message's subject IS the home paths the guard refuses.
    'bash.pattern.rm_rf_root.explanation': "Recursive force-deletion against system root, $HOME, or ~ is catastrophic and almost never the right tool. Per rule 03 (rules/03-root-cause.md), if you need to clean a build artifact use the project's clean target (`make clean`, `npm run clean`, etc.) or remove a more specific path; if you need to reset the workspace, use git (`git clean -fdx` scoped to the worktree, or `git reset --hard HEAD` after stashing). If the user truly asked for a destructive root-level rm, surface the deny and let them run the command manually — do not act on their behalf for irrecoverable operations.",
    # The force-push detector is a parse, not a static pattern, but its
    # deny text is user-facing like the rest and was the one string the
    # v0.38 catalog missed (it stayed hardcoded English in bash_guard).
    'bash.pattern.force_push.name': 'git push --force without --force-with-lease',
    'bash.pattern.force_push.explanation': "Force-pushing can irreversibly overwrite teammates' work. Per rule 03 (rules/03-root-cause.md): use `--force-with-lease` (refuses the push if the remote moved), or rebase and do a regular push, or address the divergence root cause. If you are absolutely certain force-push is warranted, ask the user to run it manually.",
}
