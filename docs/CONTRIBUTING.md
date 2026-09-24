# Contributing

> Audience: anyone changing this repository. Doc index:
> [`./README.md`](./README.md). What the components are and how they
> connect: [`./ARCHITECTURE.md`](./ARCHITECTURE.md), whose §8 is the
> connected-files map to consult before editing anything.

The plugin enforces its own rules on its own development — expect to be
denied by it while working on it.

## Before opening a pull request

1. Read every related file end-to-end before editing.
2. Trace downstream impact — editing a rule means updating the prompt, the
   docs, the checklist and the translation in the same change. The registered
   floor is [`../.claude/cc-enforcer/sync-gate.toml`](../.claude/cc-enforcer/sync-gate.toml)
   (Stop layer (i) enforces it here); the full map is
   [`ARCHITECTURE.md`](./ARCHITECTURE.md) §8.
3. Cite `file:line`; never "I think" / "should be".
4. Fix root causes. No `--no-verify`, no swallowed errors.
5. Run the checks a contributor runs locally:

   ```bash
   python -m unittest discover tests          # the whole suite
   python hooks/scripts/i18n_check.py         # zero skeleton / translation drift
   python hooks/scripts/bench_hooks.py        # if you touched a hook's start-up path
   ```

## Conventions the gates enforce

- **English is the skeleton.** `rules/`, `prompts/` and `lib/messages_en.py`
  are the source of truth; `rules/zh/`, `prompts/zh/` and `messages_zh.py`
  follow them file for file, heading for heading, key for key
  ([`I18N.md`](./I18N.md)). On drift, the translation moves.
- **One document, one language.** English documents carry no Chinese prose
  outside code spans (a detector token in backticks is data, not prose);
  `tests/test_doc_sync.py` registers every markdown file as English, Chinese
  or deliberately unscanned, and a new file must be registered.
- **Numbers are derived, not typed.** Test counts, command counts, the
  structure trees, the advertised hedge triggers, the sample coverage bars
  and every backticked `UPPER_SNAKE`-style identifier in the docs are checked
  against the code by `tests/test_doc_sync.py`. Change the code, then let the
  gate tell you which sentence is stale.
- **Every allow has a deny twin.** A test that only shows what passes stays
  green when the detector is deleted ([`../tests/README.md`](../tests/README.md)).
- **Fixtures with markers are assembled at runtime.** The plugin scans its own
  test files; a literal `# noqa` or credential in a fixture makes the module
  unwritable by any agent running it.
- **Start-up stays light.** No hook imports on its common path a module that
  path does not use; `tests/test_startup_cost.py` names the forbidden set.
- **History lives in the CHANGELOG.** Reference docs describe the plugin as it
  is; the field failure that motivated a design, and the version it shipped
  in, go in the release entry, not in the rule file or the architecture doc.

## Release checklist

The end of a release is the **GitHub Release object**, not the tag. v0.22.1
shipped twice-broken on exactly that: `marketplace.json`'s version fields
never followed `plugin.json`, so installs still reported the previous version;
and the tag was pushed while no Release was ever created, so the repository
front page kept showing the old one as Latest. Walk it, do not recall it:

1. `python -m unittest discover -s tests -p "test_version_sync.py" -v` — the
   version drift gate. `.claude-plugin/plugin.json` is the single authority;
   **every** `"version"` key in both manifests (a closed set, not a path
   allowlist), the badge in both READMEs, and the newest CHANGELOG release
   heading must equal it. Bump `plugin.json` **first** and let the gate tell
   you who has not caught up. It also compares **every** released CHANGELOG
   heading against `git tag`, so a version whose entry shipped without a tag
   is named here rather than at the next audit.
2. Move the `## [Unreleased]` notes under a `## [X.Y.Z] — date` heading in
   `CHANGELOG.md`; the gate checks it is the newest released heading.
3. `python hooks/scripts/i18n_check.py` — zero skeleton/translation drift,
   message catalogs included.
4. `python -m unittest discover -s tests -v` — the whole suite.
5. `git commit` → `git tag -a vX.Y.Z -m "..."` → `git push origin main --follow-tags`.
6. `gh release create vX.Y.Z --title "..." --notes-file <file>`. Without this
   step the front page and the releases page still show the previous version
   to every user. Confirm with `gh release list` that the new tag carries
   `Latest` before calling it done.

Earlier releases: [`../CHANGELOG.md`](../CHANGELOG.md).
