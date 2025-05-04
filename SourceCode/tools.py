import json, re, itertools
from collections import deque
from collections.abc import Iterable
from typing import Any

import sources  # metaadatok (system üzenet, tool‑sémák)
from pydantic import BaseModel  # OpenAI SDK modelljeinek ősosztálya

# ────────────────────────────────────────────────────────────────
#  Segédstruktúra a regex fordítás eredményéhez
# ────────────────────────────────────────────────────────────────
class RegexInfo:
    """Egyetlen regex‑fordítás eredményét tartalmazza.
    `to_json()` metódus JSON‑t állít elő, hogy visszaküldhessük a modellnek."""

    def __init__(self, message: str,
                 flags: int | None = None,
                 groups: int | None = None,
                 is_match: bool | None = None):
        self.message = message
        self.flags = flags
        self.groups = groups
        self.is_match = is_match

    def to_json(self) -> str:
        # Listába tesszük a sorokat → json.dumps → JSON‑t tartalmazó string
        return json.dumps([
            self.message,
            f"Fordítási flag‑ek: {self.flags}" if self.flags else "Nincsenek flag‑ek",
            f"Capture csoportok száma: {self.groups}" if self.groups else "Nincsenek csoportok",
            "Tesztstring egyezett" if self.is_match else "Nincs egyezés / nem volt tesztstring",
        ])

# ────────────────────────────────────────────────────────────────
#  ChatHistory: fix hosszú, JSON‑biztos üzenetgyűjtő
# ────────────────────────────────────────────────────────────────
class ChatHistory:
    """Deque, ami mindig JSON‑szérializálható dict‑eket tárol."""

    def __init__(self, system_msg: dict | None = None, max_len: int = 41):
        sys_msg = system_msg or sources.system_msg
        self.history: deque[dict] = deque([self.serialise(sys_msg)], maxlen=max_len)

    # ––––– belső segítség függvény –––––
    def serialise(self, obj: Any) -> dict | list[dict]:
        """SDK‑objektum → dict.  Lista esetén rekurzívan serializálunk."""
        if hasattr(obj, "model_dump"):
            return obj.model_dump(mode="python", exclude_none=True)
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, Iterable) and not isinstance(obj, (str, bytes)):
            return [self.serialise(x) for x in obj]
        raise TypeError(f"{type(obj)} nem serializálható üzenettípusként")

    # ––––– nyilvános API –––––
    def add(self, item: dict | Iterable[dict]) -> None:
        ser = self.serialise(item)
        if isinstance(ser, list):
            self.history.extend(ser)
        else:
            self.history.append(ser)

    def to_list(self) -> list[dict]:
        """OpenAI kliensnek átadható lista."""
        return list(self.history)

    def get_history(self, startIdx: int = 0, endIdx: int | None = None) -> str:
        """Szelet JSON‑stringként (tool‑válaszként küldjük vissza)."""
        endIdx = len(self.history) if endIdx is None else endIdx
        slice_iter = itertools.islice(self.history, startIdx, endIdx)
        return json.dumps(list(slice_iter))

# ────────────────────────────────────────────────────────────────
#  Egyedi kivétel: regex nem egyezik a tesztstringgel
# ────────────────────────────────────────────────────────────────
class RegexNoMatchError(ValueError):
    """A regex lefordult, de a tesztstring nem passzol."""

# ────────────────────────────────────────────────────────────────
#  validateRegex – a modell által hívott fő függvény
# ────────────────────────────────────────────────────────────────

def validateRegex(pattern: str | None = None, test_str: str | None = None) -> str:
    """Regex fordítása + opcionális teszt.
    Hibák:
      * ValueError – ha nincs pattern vagy érvénytelen a regex
      * RegexNoMatchError – ha nem egyezik a tesztstringgel"""

    if not pattern:
        raise ValueError("Nincs megadva regex minta")

    try:
        compiled = re.compile(pattern)
    except re.error as e:
        raise ValueError(f"Szintaktikailag hibás regex – {e}") from None

    is_match: bool | None = None
    if test_str is not None:
        is_match = bool(compiled.search(test_str))
        if not is_match:
            raise RegexNoMatchError(f"A minta nem egyezett: '{test_str}'")

    info = RegexInfo(
        message="Regex sikeresen lefordítva.",
        flags=compiled.flags,
        groups=compiled.groups,
        is_match=is_match,
    )
    return info.to_json()