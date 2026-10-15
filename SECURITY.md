# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.42.x | yes |
| < 0.42 | no: upgrade first |

## Reporting a vulnerability

Please do not open a public issue. Use GitHub's private reporting:
[Security → Report a vulnerability](https://github.com/skymanbp/cc-enforcer/security/advisories/new).

Include the plugin version, the operating system and shell, and a
reproduction: the tool call the hook saw and the verdict it gave.

## What counts as a vulnerability here

cc-enforcer is a set of Claude Code hooks whose job is to deny or block a
tool call. Its value is that a verdict cannot be talked around, so the
following count:

- A way past a `must` check that the rule says must deny: a command
  wrapper, a quoting or an encoding the Bash guard does not see through, a
  path spelling the read guard does not normalise, a suppression marker
  the edit guard does not recognise.
- A Stop-hook block that text other than evidence can satisfy.
- Content of a tool result, a file or a transcript that changes a hook's
  verdict in its own favour. The hooks read what the model saw; nothing
  there may grant itself a pass.
- An edict (`must`) that is loaded from a file the project did not write.

## What does not count

- A `should` edict not being enforced: by design it is a reminder, not a
  gate.
- A user who disables the plugin, edits its hooks or answers a permission
  prompt: the hooks run with the user's rights and do not defend against
  the user.
- A verdict's wording in a language other than the two shipped.
