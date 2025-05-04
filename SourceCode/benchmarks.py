"""
Benchmarkok futtatására szolgáló script
SZámláló:   compile hibák                   → stats['errors']
            példa sstringben nincs egyezés  → stats['mismatches']
            sikeres                         → stats['ok']
"""

import json, re
from collections import Counter
from functools import wraps

from regexp_main import client as chatClient
import tools, sources

# ──────────────────────────────────────────────────────────
# 1.  Statisztikák tárolása.
# ──────────────────────────────────────────────────────────
stats      = Counter()        # számláló a hibákra
error_log  = []               # részletes leírás a tesztekről

# ──────────────────────────────────────────────────────────
# 2.  validateRegex dekorátora, ami számolja az errorokat.
# ──────────────────────────────────────────────────────────
from tools import RegexNoMatchError   

def track_validate(func):
    @wraps(func)
    def wrapper(pattern: str, *args, **kwargs) -> str:
        stats["calls"] += 1
        try:
            result = func(pattern, *args, **kwargs)
            stats["ok"] += 1
            return result

        except RegexNoMatchError as exc:        # compile-olva, de nincs egyezés a teszt stringben
            stats["mismatches"] += 1
            error_log.append({"regex": pattern, "exc": repr(exc)})
            raise

        except re.error as exc:                 # compile hiba
            stats["errors"] += 1
            error_log.append({"regex": pattern, "exc": repr(exc)})
            raise
    return wrapper

tools.validateRegex = track_validate(tools.validateRegex)

# ─────────────────────────────────────────────────────────────────
# 3.  Modelhívó függvény, ami a benchmarkokhoz meghívja a modellt.
# ─────────────────────────────────────────────────────────────────
def call_model(prompt: str) -> str:
    chat = chatClient.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a regex generator. "
                    "Respond ONLY by calling validateRegex with the regex you propose."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        tools=sources.benchmark_tool,          
        tool_choice={"type": "function", "function": {"name": "validateRegex"}},
    )

    # Kiszedi a modellből a paramétereket a validateRegex függvényhez
    try:
        args = json.loads(chat.choices[0].message.tool_calls[0].function.arguments)
        pattern = args["pattern"]
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise ValueError(f"Model response did not contain a pattern: {exc}")

    # kiszedett értékkel függvény meghívása
    tools.validateRegex(pattern)
    return pattern

# ──────────────────────────────────────────────────────────
# 4. Benchmark futtatása.
# ──────────────────────────────────────────────────────────
def run_bench(prompts):
    results = []
    for prompt in prompts:
        try:
            regex = call_model(prompt)
            results.append({"prompt": prompt, "regex": regex, "status": "ok"})
        except Exception as exc:
            results.append({
                "prompt": prompt,
                "regex": globals().get("regex"),   # may be None
                "status": "error",
                "exc": repr(exc),
            })
    return results

bench_results = run_bench(sources.benchmark_prompts)

# ──────────────────────────────────────────────────────────
# 5.  Statok kiszedése JSON file-ba.
# ──────────────────────────────────────────────────────────
print(f"validateRegex calls : {stats['calls']}")
print(f"successful (ok)      : {stats['ok']}")
print(f"compile errors       : {stats['errors']}")
print(f"no‑match mismatches  : {stats['mismatches']}")

with open("bench_stats.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "summary": stats,
            "per_prompt": bench_results,
            "errors": error_log,
        },
        f,
        indent=2,
        ensure_ascii=False,
    )

print("Wrote detailed log to bench_stats.json")
