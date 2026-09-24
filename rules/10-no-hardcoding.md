---
id: "10"
title: "No non-essential hardcoding"
severity: must
---

# Rule 10 — No non-essential hardcoding

**Enforced by:** `PreToolUse(Edit|Write)` — DENY when new code carries a secret-named identifier or quoted key assigned a literal of 8+ characters, a private-key PEM header, an AWS access-key or provider-issued token literal (`ghp_…` / `xox…` / `AIza…`), or credentials inside a URL — unless the value is an obvious placeholder or an adjacent comment carries a rationale token. Prose documents and lockfiles are not scanned (`requirements*.txt` / `constraints*.txt` are); magic numbers and bare endpoints are guidance only.

## Principle

> **A value that by design should be a variable — read from
> configuration, an environment variable, a secret manager, or a passed-in
> argument — must not be lazily inlined as a source literal.**

The canonical laziness this rule intercepts is the
should-have-been-a-variable class — literals that are unambiguously *supposed*
to live outside the code:

- credentials: passwords, API keys, access keys, auth tokens, client
  secrets, bearer tokens;
- private-key material (PEM `BEGIN ... PRIVATE KEY` blocks);
- credentials embedded inside a connection string / URL
  (`scheme://user:password@host`).

Hardcoding a secret is worse than untidy: it leaks the secret into version
control, CI logs, and every clone of the repo, and it makes rotation a
code change. Externalizing it is the root-cause fix (rule 03).

## Scope — secrets are the hard class

Faithful to the conservative-detector philosophy (prefer false negatives
to false positives), only the unambiguous should-be-config classes are
refused at write time:

| Class | Hard-enforced? |
|---|---|
| Secret-named variable or quoted key assigned a quoted literal (≥ 8 chars) | ✅ yes |
| Private-key PEM header | ✅ yes |
| AWS access-key literal (`AKIA…`) or provider-issued token (`ghp_…` / `xox…` / `AIza…`) | ✅ yes |
| Credentials inside a connection URL | ✅ yes |
| Magic numbers | ❌ soft guidance only (FP-prone) |
| Bare network endpoints / ports | ❌ soft guidance only |

Magic numbers and bare endpoints are *soft* guidance — call them out in
review, but they are **not** intercepted by a hook, because a hard
detector for them would fire constantly on legitimate code. The
provider-token row exists instead of a bare `token` keyword for the same
reason: `token = "NUMBER_LITERAL"` is ordinary lexer code.

A value is treated as a harmless placeholder when it contains `example` /
`changeme` / `your-` / `<…>` / `${…}` / `dummy` / `redacted`, or is an
env-read (`os.environ[…]`, `getenv`, `process.env`); a pure-alpha CamelCase
value after a `:` (`password: "SecretStr"`, a type annotation) is skipped
too. Prose documents (`.md` / `.rst` / `.txt` / `.adoc`) and lockfiles are
exempt because they legitimately carry example values and are
machine-generated; `requirements*.txt` / `constraints*.txt` stay scanned
because an index URL with embedded credentials there is a real leak
vector.

## Marking an essential literal

The user's scope is *non-essential* hardcoding. An essential, example or
fixture literal is allowed through when the offending line, or an
immediately adjacent line (±1), carries a rationale token **inside a
comment**: the tokens of rule 09's hatch (`because` / `why` / `因为` /
`原因` …) plus `essential` / `必须` / `必需` / `example` / `fixture` /
`placeholder` / `占位` / `sample` / `test data`. Only comment text counts,
and "comment" is decided lexically — a `#` inside a URL is not one; a
`/* … */` block or an own-line docstring is. A bare secret with no
rationale = the non-essential case = **DENY**.

## Must do (MUST)

1. **Externalize secrets** — read them from the environment or a secret
   store; keep the real value only in an untracked `.env` / secret store.
2. **Mark genuine placeholders** — use an obvious placeholder value, or
   add an adjacent rationale comment, so the check can tell an example
   from a leak.
3. **Rotate on exposure** — if a real secret was ever committed, treat it
   as compromised and rotate it; do not just delete the line.

## Must not (MUST NOT)

- ❌ Commit a real credential / token / private key as a source literal.
- ❌ Bury a password inside a connection string.
- ❌ "Temporarily" hardcode a secret with a plan to externalize it later.
- ❌ Suppress the detector with a false rationale comment on a real secret.

## Relationships

| Relationship | Note |
|---|---|
| 10 vs 03 | 03 says fix the root cause; 10 makes "the value belongs in config, not code" a hard, write-time root-cause fix for the secret class. |
| 10 vs 09 | Same mechanism (write-time content detector with a why-comment escape hatch); 09 targets suppression markers, 10 targets hardcoded secrets. |
| 10 vs 11 | Sibling detectors; 10 is *what* is inlined (secrets), 11 is *where* it points (machine-specific paths). |

## Self-check triggers

- About to type a quoted literal right after `password` / `api_key` /
  `token` / `secret` / `bearer`.
- Pasting a key, token, or connection string "just to get it working".
- Writing a `-----BEGIN … PRIVATE KEY-----` block into a source file.
- Telling yourself "I'll move this to an env var later".

## Termination condition

Writing a credential-bearing value is allowed only when **one** of:

1. It is read from the environment / a secret store (not a literal); or
2. It is an obvious placeholder / example / fixture (marked as such); or
3. An adjacent rationale explicitly justifies it as essential.

Otherwise → **non-essential hardcoding**, return to rule 03 and
externalize it.
