#!/usr/bin/env python3
"""cc-enforcer — PreToolUse(Read|Edit|Write) hook entry point.

A thin shell (v0.41). The hook's body is `read_guard_impl.py`, the module
imported below; `hooks.json` keeps pointing at this file, and so do the
tests, the benchmark, the demo and the docs.

Why the split: Python never caches the bytecode of the script it was
asked to run — `python read_guard.py` re-compiled all ~1,200 lines of the
body on every Read, Edit and Write, about 3 ms on the maintainer's
machine — while a module it *imports* is compiled once and served from
`__pycache__` for as long as the source is unchanged. Moving the body one
import away is the whole trick; nothing in the body changed.

Imported rather than run, this file hands the caller the body module
itself (the `sys.modules` swap below) and also carries the body's names,
so `read_guard.X` is the very object the hook runs with: a test that
patches through this name reaches the running code, where a copied
namespace alone would silently not. The module dunders stay this file's
own — copying `__name__` would defeat the `__main__` check.
"""

import os
import sys

# Run as a script, this file's directory is already sys.path[0]; loaded
# by path or imported from elsewhere (a test, an editor, a tool), nothing
# guarantees the body beside it is importable — so make it so here.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import read_guard_impl as _impl  # noqa: E402 — because the sibling directory must be on sys.path first

globals().update({
    name: value for name, value in vars(_impl).items()
    if not (name.startswith("__") and name.endswith("__"))
})

if __name__ == "__main__":
    sys.exit(_impl.main())
else:
    sys.modules[__name__] = _impl
