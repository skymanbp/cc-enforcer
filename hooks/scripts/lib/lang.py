"""The active language code, resolved in one place.

`CC_ENFORCER_LANG` is the single switch the user toggles, and it reaches
three consumers: the injected prompts (`inject_context.py`), the edict
block and deny reason (`lib/edicts.py`) and the guard message catalog
(`lib/messages.py`). Each carried its own copy of the same five lines
until v0.40, one of them annotated "deliberately duplicated in spirit
rather than imported" because importing an entry-point script from a
library would have inverted the dependency direction. A library module
resolves that: every consumer imports downwards, and there is one
definition of what "the active language" means.

The contract, unchanged from the copies it replaces:

  * English is the DEFAULT and the skeleton (source-of-truth) language.
  * Any non-empty code passes through verbatim, lower-cased. There is no
    membership gate here: each consumer falls back to English on its own
    terms (a missing prompt translation, a missing message catalog, an
    unregistered chrome dictionary), so an unknown code degrades rather
    than crashes.
"""

from __future__ import annotations

import os

DEFAULT = "en"
ENV_VAR = "CC_ENFORCER_LANG"


def resolve(explicit: str | None = None) -> str:
    """Return the active language code; an explicit argument wins over the env."""
    if explicit is not None:
        code = explicit.strip().lower()
    else:
        code = (os.environ.get(ENV_VAR) or "").strip().lower()
    return code or DEFAULT
