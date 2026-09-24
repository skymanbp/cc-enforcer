---
id: "09"
title: "Systematic modification, no patch-style"
severity: must
---

# Rule 09 — Systematic modification · no patch-style

**Enforced by:** `PreToolUse(Edit|Write)` — DENY on an unjustified patch marker (`try/except: pass`, `# noqa`, `# type: ignore`, `// @ts-ignore`, `// @ts-expect-error`, `// eslint-disable`, `time.sleep` with a race / wait / workaround comment) and on the 4th small edit (≤ 10 lines and < 200 chars) to one file in a session with no systematic rewrite (≥ 50 lines, ≥ 1500 chars, or ≥ 30 % of the file) in between — a net reduction or a bookkeeping edit (a version or date bump) is never counted; `PreToolUse(Bash)` — DENY on `--no-verify`, `--no-gpg-sign`, `chmod 777`, `git rebase --skip`, `--break-system-packages`, `rm -rf` on a root path / `$HOME` / `~`, and `git push --force` (not `--force-with-lease`); `Stop` layer (f) — BLOCK when an edit turn's final reply lacks the root cause + impact + solution triplet and carries no `rule 09` marker.

## Principle

> **Modifications must be systematic and complete, not local patches.**

Typical patch-style modifications:

- Treating the symptom ("add an `if` to swallow the exception") instead of the root cause;
- Local `try / except: pass` / `# noqa` / `@ts-ignore` / `// eslint-disable` silencers without justification;
- Repeated small `Edit`s on the same file in the same session (rolling patches), a few lines at a time — the hook's bound for "small" is ≤ 10 lines and < 200 characters;
- Wrapping a try at the call site to "fix" the symptom while the real bug is in the callee;
- Increasing the timeout / loosening assertions / making tests more permissive;
- Commenting out failing tests instead of fixing the code;
- Stuffing TODO / "for now" / "later" into new code;
- Fixing N symptoms of one root cause one at a time (point-to-point), instead of one unified fix at the diagnosed origin.

These are not "fixes" — they **defer** problems. Rule 09 elevates them to a hard prohibition; the line under the title says which of them a hook physically intercepts.

## Must do (MUST)

### Before modification

1. **Find the actual root cause** (rule 03) — not "where it throws", but "why it throws".
2. **Verify root-cause evidence** (rule 01 verification) — confirm the root-cause hypothesis *on the spot* via Read / Grep / command output.
3. **Map the impact** (rule 02 Q5) — list every upstream / downstream tied to the root cause.
4. **Compare ≥ 2 fix strategies** (rule 08 item 6) — across simplicity / performance / fit with existing architecture / future maintainability.

### One root cause, one unified fix

Point-to-point patching — treating each observed failure as its own
little fix — is forbidden. When a problem appears, the only accepted
shape is **trace upstream → diagnose → one unified fix**:

5. **Trace to the most-upstream cause** (rule 03 upstream ladder):
   climb the causal chain until the answer is a mechanism / design
   decision / missing invariant, and state explicitly why you stopped
   where you stopped.
6. **Diagnose before treating**: the root-cause hypothesis must be
   demonstrated by a first-party probe / reproduction / failing test
   (rule 01) *before* the first line of the fix is written.
7. **Enumerate the class, not the instance.** A diagnosed root cause
   defines a *class* of defects; the instance you observed is merely
   the one that happened to surface. Sweep the repo for every sibling
   of the class (Grep to locate, Read to confirm — rule 04; report the
   sweep — rule 12). Scope note: the sweep is part of fixing the
   reported problem, not scope creep — rule 07 bans *unrequested*
   changes. When the enumerated class materially expands the visible
   scope of the user's request, surface the enumeration and get the
   user's call before the one-pass fix.
8. **Fix the mechanism once.** One systematic change that removes the
   generating mechanism and covers every enumerated instance in the
   same pass. N symptoms sharing one root cause = **one** fix — never
   N patches, and never "fix the reported ones, leave the rest of the
   class". The unit of "one" is the mechanism, not the diff size:
   minimum effective change (rule 07) still applies.
9. **Prove the class is closed** (rule 06): re-trigger not only the
   observed instance but at least one *other* enumerated instance of
   the class. When the sweep shows the class has exactly one member,
   say so explicitly — the sweep report is then the closure evidence.

The instance-fix trap, measured on this repo: an audit named a root
cause and fixed only the instances it had seen; the mechanism survived
and regenerated a fresh crop of the same class one release later —
including one regression. The next pass replaced the mechanism (33
findings → three root causes → four shared models), which is exactly
the shape this section prescribes. A second failure with the same shape
is the class announcing itself — an obligation to test whether the
origins are truly shared, never a coincidence to ignore.

### During modification

10. **Fix the cause, not the symptom** (rule 03) — the edit point must sit at the source of the causal chain, not at the manifestation.
11. **Cover the full impact** — fix every connected point of the same root cause; never "fix one now and patch the rest later".
12. **Do not introduce patch markers** — a suppression marker is legitimate only with a rationale comment (see "Justifying a suppression marker" below).
13. **Do not accrete** — when a third small edit to the same file is on its way, stop patching: fold the pending fixes into one systematic edit, `Write` the file whole, or surface to the user that the file needs a refactor. Deleting is never a patch (a net reduction is not counted) and neither is a version or date bump — so never pad an edit to look systematic.
14. **Record new invariants** — if the change establishes a new invariant ("X is never None" / "must acquire the lock first"), declare it explicitly in code or docs.

### Bulk mechanical edits (rename / codemod / sed)

A regex that matches your intent also matches its homographs, and a bulk
rewrite is the one edit shape where a single bad rule corrupts hundreds
of files at once. Before running one:

1. **Survey first, write the rule second.** Enumerate what actually
   surrounds every occurrence of the target token and *read that list*.
   Homographs found this way in one real directory rename: an API
   version inside a URL (`…/v3/me`), a DB table version
   (`agent_subtypes v3/613`), a schema range (`Mesh v3/v4`), a **math
   variable** (`v3 = v2 * v1 + …`), a function parameter, and a report
   id (`DIV-V3`). A blind sed would have corrupted all six.
2. **Rewrite only allowlisted forms.** Never "replace everything that
   matches" — replace what the survey proved is the thing you mean.
3. **Emit a refusal report.** Every occurrence the allowlist declined is
   printed for a human to read. A silent skip is indistinguishable from
   a site you missed.
4. **Reconcile the arithmetic.** total occurrences = rewritten + skipped
   + refused. If it does not add up, the rule is wrong, not the count.
5. **Expect shapes the pattern is structurally blind to.** The token
   inside a regex alternation (`^(?:v3|docs)/` — followed by `|`, not by
   the separator you keyed on); the token as a standalone argument
   (`join(root, "v3", "assets")`); and the *symbol* named after it
   (`V3_DIR`). Each needs its own survey pass.
6. **Never rewrite a path that addresses history.**
   `git show <fixed-rev>:<path>` resolves against an old tree in which
   the old layout is still the correct one. Worktree paths move;
   history-addressing paths must not.

### After modification

15. Run rule 06 convergence — including Check 2b, since a bulk edit is
    exactly the case where totals stay equal while composition shifts;
    run rule 07 task fidelity.

## Justifying a suppression marker

A suppression marker — `# noqa`, `# type: ignore`, `// @ts-ignore`,
`// @ts-expect-error`, `// eslint-disable` (including the `-next-line` /
`-line` forms), or a `time.sleep` that waits out a race — is allowed only
with a rationale **in a comment** on the same line or an immediately
adjacent one: a token such as `because` / `why` / `rationale` / `因为` /
`原因` / `故意`, or a justification lead such as `see issue` /
`intentional` / `third-party` / `per spec`. Only comment text counts — the
same word inside code or an ordinary string literal does not — and a bare
deferral (TODO / FIXME / HACK / WIP / later) is not a reason. Block
comments and docstrings count as comments; a `#` inside a URL does not.
The hook's `PATCH_MARKERS` constant is the authoritative spelling list,
and the same rationale hatch serves rules 10 and 11.

```python
# noqa: E501  -- URL string exceeds 100 chars; splitting hurts readability
LONG_URL = "https://..."
```

```typescript
// @ts-ignore: third-party lib has incomplete type, see issue #1234
const result = legacy.foo();
```

A bare marker without justification = laziness, intercepted.

## Must not (MUST NOT)

- ❌ **Symptom patching**: wrap the call site with try/except to make the exception vanish without changing the root cause.
- ❌ **Silent suppression**: `# noqa` / `@ts-ignore` / `// eslint-disable` without a why comment.
- ❌ **Race-via-sleep**: adding `time.sleep(0.5)` to stabilize a test ≠ fixing the race.
- ❌ **Loosening tests**: original asserts `X == 5`, you change to `X > 0` to make it pass.
- ❌ **Extending timeouts**: original `timeout=5s`, you push to `60s` to mask a performance issue.
- ❌ **Commenting out failing tests**: deleting / commenting / `@skip` to declare "done".
- ❌ **Rolling patches**: ≥ 4 small Edits on the same file this session without a single systematic rewrite — reactive accumulation. The write gate counts them; net reductions and bookkeeping edits are exempt because neither accretes.
- ❌ **Fix one and leave three TODOs**: "I'll patch the rest later" is not allowed; one pass must cover the full root-cause impact.
- ❌ **Blind bulk replace**: running a rename / codemod / sed without first surveying the token's real neighbourhoods, without an allowlist, or without a refusal report of what it declined.
- ❌ **Rewriting history-addressing paths** during a move: a path handed to a fixed git rev must keep the layout that rev actually has.
- ❌ **Pattern blacklists where the invariant is a closed set**: if only a known list of names is legal, enumerate that list and reject everything else. Blacklisting the stray shapes you happen to have seen lets the next shape walk straight through — including on the gate's own first live run.
- ❌ **Point-to-point patching**: fixing symptom sites one at a time — each observed failure gets its own little fix — when they share a root cause. Includes "fix what was reported, leave the unreported siblings".
- ❌ **Instance hardening**: repairing the observed instance of a mechanism defect while leaving the mechanism in place to regenerate the class — hardening scoped to the sighting, never sweeping the class.

## Relationships

| Relationship | Note |
|---|---|
| 09 vs 03 | 03 lists specific lazy anti-patterns and owns the **upstream-tracing ladder**; 09 **structures them into a general modification discipline** — including the unified-fix requirement — with physical interception. |
| 09 vs 02 | 02 is the thinking discipline before modification; 09 is the execution discipline during. They chain. |
| 09 vs 08 | 08 verifies "did you complete pre-action prep?"; 09 verifies "is the content systematic, not patch-style?". Pre vs content. |
| 09 vs 06 | 06 verifies "did the fix converge?"; 09 verifies "was the fix done systematically?". Process vs result. |
| 09 vs 07 | 07 verifies "did you deliver everything the user asked for?"; 09 verifies "was the way of delivering it patch-style?". Coverage vs implementation. |

## Self-check triggers

- About to make a ≤ 5-line "quick fix".
- About to write `try / except: pass` or `try / except: ...` with vague handling.
- About to write `# noqa` / `@ts-ignore` / `eslint-disable` **without** a rationale.
- About to add `time.sleep` to stabilize a test.
- About to loosen a test assertion / extend a timeout.
- Commenting out / `@skip`-ing any failing test.
- Already made ≥ 3 small Edits on the same file this session and still patching, not rewriting.
- About to run a rename / codemod / sed across many files without a survey, an allowlist and a refusal report.
- About to write a guard that enumerates *bad* shapes for an invariant whose specification is a *closed set of good ones*.
- About to fix the *second* failure with the same shape as one already fixed — the class is announcing itself; diagnose the shared origin instead of patching the sighting.
- About to write a fix without having stated where the causal chain stops and why.
- Chain-of-thought lacks the "root cause + impact + alternatives" triplet.

## Termination condition

"Modification complete" is allowed only when **all** of the following hold:

1. The **most-upstream** root cause has been diagnosed — causal chain stated, diagnosis demonstrated first-party (rule 03 upstream ladder + rule 01).
2. All connected points of the root cause have been covered (rule 02 Q5).
3. Every sibling instance of the diagnosed class has been enumerated and covered in the same pass — no point-to-point residue (unified fix).
4. `new_string` contains no unjustified patch markers (the write gate passes).
5. The **final reply** explicitly records the "root cause / impact / alternatives" triplet (Stop layer (f) passes). Layer (f) reads the final reply text only — a triplet that stayed in the chain of thought does not count.
6. Rule 06 convergence + rule 07 fidelity self-quizzes done.

Otherwise → **not systematic**, return to rule 02 + rule 03 + rule 08.
