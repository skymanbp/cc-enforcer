# Documentation index

Five documents, five audiences. Each fact is meant to live in exactly one of
them; when two disagree, the one that owns the fact wins and the other is a
bug.

| Document | Audience | Owns |
|---|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Developers extending or auditing the plugin | How the five layers fit together, every hook's input/output contract, the Stop decision table layer by layer, the detector inventory, session state, configuration files, and §8's **connected-files map** — the table to consult before editing anything here. |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Anyone changing this repository | The house rules the gates enforce, the local checks, and the release checklist. |
| [`RULES.md`](RULES.md) | Anyone looking a rule up, in Chinese | The catalog of all 12 rules: id, title, severity, full-text link, what enforces each. An index, not the rules themselves; the English index is [`../rules/00-index.md`](../rules/00-index.md). |
| [`EDICTS.md`](EDICTS.md) | Users writing their own hard rules | The Imperial Edicts system: the TOML schema, `must` vs `should`, project vs global scope, how a regex becomes a `PreToolUse` DENY, and how to debug one that is not firing. |
| [`I18N.md`](I18N.md) | Translators and CI | The skeleton↔translation contract: English at the root is the source of truth; what `i18n_check.py` compares, what it deliberately does not, and what to do when it goes red. |

## Where everything else lives

| You want… | Go to |
|---|---|
| The rules themselves | [`../rules/`](../rules/) (English skeleton) · [`../rules/zh/`](../rules/zh/) (Chinese) |
| What the agent is actually told — at session start and on every prompt | [`../prompts/`](../prompts/) |
| Install steps, the pitch, the enforcement tables, the benchmark | [`../README.md`](../README.md) · [`../README.zh.md`](../README.zh.md) |
| Release history — the only copy of it, and where the "why" of every design lives | [`../CHANGELOG.md`](../CHANGELOG.md) |
| The test suite, file by file | [`../tests/README.md`](../tests/README.md) |
| The before/after demo on the front page | [`../demo/README.md`](../demo/README.md) |

## A note on scope

These documents describe **what the plugin does and why**. They are not the
enforcement itself: the rules are Markdown in `../rules/`, the hooks are
Python in `../hooks/scripts/`, and the guarantee that this documentation still
matches them is [`../tests/test_doc_sync.py`](../tests/test_doc_sync.py) — a
CI gate that derives every pinned number and inventory from the code at test
time, plus three behavioural claim classes (advertised hedge triggers, printed
coverage bars, backticked identifiers). A green gate still says nothing about
judgement prose: whether an explanation is right, or a rationale sound.
