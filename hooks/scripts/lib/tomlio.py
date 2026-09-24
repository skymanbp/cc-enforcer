"""cc-enforcer — shared, hardened TOML config reader (v0.25).

Two independent hand-edited configs drive hard guards:

    .claude/cc-enforcer/edicts.toml      → PreToolUse DENY (lib/edicts)
    .claude/cc-enforcer/sync-gate.toml   → Stop layer (i)  (lib/sync_gate)

Both had the same three failure modes, and in both the failure was
SILENT DISABLEMENT of enforcement — the worst possible direction for a
discipline plugin, because the user sees a normal-looking config file and
assumes their rules are live:

  * **UnicodeDecodeError.** `tomllib.load(fileobj)` decodes the stream
    itself and raises `UnicodeDecodeError` (a `ValueError`), which neither
    the `OSError` nor the `TOMLDecodeError` clause caught. In `edicts.load`
    it escaped the function entirely — contradicting its own "never
    raises" docstring — unwound past every downstream check in
    `read_guard._handle_pre_tool_use` (which calls `edicts_lib.load()` as
    the first statement of the Edit/Write path) and landed in the outer
    failing-open handler. Net effect: one edicts.toml saved as GBK/ANSI
    turned OFF read-before-edit (rules 04 + 08) for the whole session.
    In `sync_gate.load` it crashed layer (i), which also skipped the
    turn-boundary `clear_edit_flag`.

  * **UTF-8 BOM.** tomllib decodes strict UTF-8 and does not strip a byte
    order mark, so a leading U+FEFF makes the first `[[table]]` an invalid
    statement. A BOM is what several standard Windows save paths produce
    (PowerShell `>` / `Out-File`, some editors) for a file the plugin
    explicitly invites users to hand-edit.

  * **OSError / TOMLDecodeError.** Already handled; kept.

Why a shared module rather than the same patch in two places: this repo
keeps getting bitten by hand-copied logic drifting apart (read_guard's
three write branches in v0.24; the fence tracker duplicated between
stop_guard and i18n_check, unified in v0.30). One reader, one contract.

TOML is *defined* as UTF-8, so a non-UTF-8 file is genuinely invalid —
the job here is to say so loudly on stderr and degrade to "no config",
never to crash the caller.

v0.31 adds the WRITING primitive alongside the reading one, for the same
reason. `manage_edicts.py` owned a `_toml_basic_string` encoder whose
history is a list of things a naive version gets wrong (a raw newline is
illegal in a single-line basic string; DEL passes a `>= " "` guard but is
still forbidden), and `manage_sync_gate.py` needs exactly that encoder.
Copying it would have recreated the defect class v0.30 spent a release
removing — the second copy is always the one that misses the next fix.
"""

from __future__ import annotations

from pathlib import Path

# UTF-8 byte-order mark.
_UTF8_BOM = b"\xef\xbb\xbf"

# `tomllib` is imported on first use, not at module load (v0.40). Every
# hook imports this module, and most invocations never parse a config —
# a project without edicts.toml / sync-gate.toml, or a plain Read — yet
# each one paid the ~10 ms the parser package costs to import. The probe
# result is cached so the cost is paid at most once per process, and only
# by a process that actually reads TOML.
_tomllib = None
_probed = False


def _module():
    """The `tomllib` module, or None on an interpreter that lacks it."""
    global _tomllib, _probed
    if not _probed:
        _probed = True
        try:
            import tomllib as _t  # noqa: PLC0415 -- because the import is deferred on purpose; see above
            _tomllib = _t
        except ModuleNotFoundError:
            # because Python < 3.11 has no tomllib and every caller must fail open
            _tomllib = None
    return _tomllib


def parse_toml_file(path: Path, warn) -> dict | None:
    """Read + parse a TOML config; None (with a diagnostic) on any failure.

    `warn` is the caller's stderr-diagnostic function so the message keeps
    that module's prefix (e.g. "[cc-enforcer edicts]").
    """
    tomllib = _module()
    if tomllib is None:
        return None
    try:
        raw = path.read_bytes()
    except OSError as e:
        warn(f"could not read {path}: {e}")
        return None
    if raw.startswith(_UTF8_BOM):
        raw = raw[len(_UTF8_BOM):]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        warn(
            f"{path} is not valid UTF-8 ({e}). TOML must be UTF-8 — "
            f"re-save the file with UTF-8 encoding. Ignoring it, so the "
            f"rules it defines are NOT in effect."
        )
        return None
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        warn(f"invalid TOML in {path}: {e}")
        return None


def available() -> bool:
    """True when TOML parsing is possible at all (Python 3.11+).

    The one place that answers this. `lib/edicts.py` and `lib/sync_gate.py`
    carried their own `try: import tomllib` sentinels alongside this
    function until v0.40 — three copies of one fallback, and each of them
    imported the parser at module load for every hook invocation.
    """
    return _module() is not None


def basic_string(s: str) -> str:
    """Encode `s` as the body of a TOML basic string (no surrounding quotes).

    Moved here from `manage_edicts.py` in v0.31 so the edicts writer and the
    sync-gate writer share one encoder. Its scars are worth keeping visible,
    because each one silently corrupted a config that the CLI then reported
    as written:

    * **v0.25** — only `\\` and `"` were escaped, then the result was dropped
      into a SINGLE-LINE basic string where a raw newline is illegal. A
      multi-line value is a natural, documented way to hand-write an entry,
      and because the writer re-serialises EVERY entry on any add/remove,
      one such value made the whole file unparseable: the CLI printed
      "Added …" over a config tomllib then rejected, silently unenforcing
      every `must` rule in the project.
    * **v0.26** — the control-character guard was `ch >= " "`, which is true
      for DEL (U+007F). TOML forbids it raw in a basic string, so the
      rewritten file did not parse — same blast radius, different byte.
    """
    out = s.replace("\\", "\\\\").replace('"', '\\"')
    for raw, esc in (
        ("\n", "\\n"), ("\r", "\\r"), ("\t", "\\t"),
        ("\b", "\\b"), ("\f", "\\f"),
    ):
        out = out.replace(raw, esc)
    return "".join(
        ch if (ch >= " " and ch != "\x7f") else f"\\u{ord(ch):04X}"
        for ch in out
    )


def dumps_check(text: str) -> str | None:
    """Parse `text` as TOML; return None if it is valid, else the error.

    The write-side counterpart to `parse_toml_file`: a serialiser must
    never commit a document it cannot read back. Callers use it to turn a
    silent, total failure (an unparseable config disables every rule it
    holds) into a loud, local one.
    """
    tomllib = _module()
    if tomllib is None:
        return None
    try:
        tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        return str(e)
    return None
