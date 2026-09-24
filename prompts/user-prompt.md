# cc-enforcer — per-turn reminder

> Full contract: injected at session start and again after every compaction;
> this is the short form. Every DENY / BLOCK message carries its own
> recovery — fix the row it names.

## Hard gates (hooks intercept; not advice)

- **Edit/Write → `PreToolUse` DENY**: an existing file not Read this session (read-before-edit); a suppression marker with no adjacent why-comment — `try/except: pass` / `# noqa` / `# type: ignore` / `@ts-ignore` / `@ts-expect-error` / `eslint-disable` / `time.sleep` workaround; a hardcoded secret / token / credentials-in-a-URL in **code** (rule 10); a user-home path in **code** — `C:\Users\…` / `/home/…` / `$HOME` / `%USERPROFILE%` / quoted `~/…` (rule 11); the 4th small edit (≤ 10 lines and < 200 chars) to one file with no systematic rewrite between (net reductions and version/date-only edits never count).
- **Bash → `PreToolUse(Bash)` DENY**: `--no-verify` / `--no-gpg-sign` / `git push --force` (not `--force-with-lease`) / `chmod 777` / `git rebase --skip` / `--break-system-packages` / `rm -rf` on root / `$HOME` / `~`; any `must` edict listed below.
- **Stop → BLOCK** when the reply claims done and: (a) shows no `$ command → output` evidence · (b) hedges within 50 chars of the claim (`I think` / `probably` / `maybe` / `我觉得` / `应该是`) · (c) skips the four-question self-quiz (really solved? better solution? unverified? verification reasonable?) — convergence · (d) never re-checks the user's original request item by item — fidelity · (e) edit turn without ≥ 3 of root cause / architecture / solution / impact / risk (think-before-write) · (f) edit turn without the root cause + impact + solution triplet · (g) says "edited X" while X's mtime is unchanged · (h) has no `tldr`, or a tldr item over 160 display columns (CJK counts 2) — Stop layer (h) · (i) a sync-gate group matched, no `require` file changed, and no `sync-check:` answers the group the last block named (`n/a`-style placeholders count as absent).

## Closing (mandatory on any done-claim)

End with a ```yaml `cc-enforcer:` block; the field names ARE the Stop markers: `before` (rule 02) · `edits` (09) · `convergence` (06: `re-trigger`, `boundary case`, `existing tests`, `self-quiz`) · `fidelity` (07: `request coverage`, `standard`, `no degradation`) · `closing` (08+09: `root cause`, `impact`, `solution`) · `sync-check:` (12, edit turns) · `tldr` (one plain sentence per item, ≤ 160 columns). Q&A needs only `convergence` + `fidelity` + `tldr`. Full contract: `prompts/session-start.md` under the plugin root.
