# Trailhead 🌿

A hiking trip planner that works where the internet doesn't. Trailhead is a
small Python CLI that filters a bundled offline trail dataset against your
constraints, then generates a hike plan — route, timing, gear checklist,
safety notes — using a **local open-weight model via Ollama**. No API key,
no signal required, no per-query meter.

```
$ trailhead plan --near "Centereach, NY" --distance 6 --group "2 adults, 1 dog"

✓ Found 1 matching trail(s) (offline dataset)
✓ Selected: Blydenburgh County Park - Stump Pond Loop (6.1 mi, easy)

✓ Plan generated in 0.00s (engine: offline-template)
...
```

## Why local?

A hiking planner is needed exactly where cloud AI is unavailable: the
trailhead with no bars. Trailhead runs inference on your own machine, so
"no signal" is the normal operating condition, not a failure mode. Your
location data never crosses a network boundary, re-planning is free, and
the model is swappable with one flag.

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) with any chat model pulled (e.g. `ollama pull llama3.2`)
  — **only needed for AI-generated plans**. Without Ollama, Trailhead still
  works: it falls back to a built-in deterministic offline template that
  produces a complete plan from the trail data (clearly labeled as such).

## Install & run (offline)

```bash
git clone https://github.com/muse-quest/trailhead
cd trailhead
python -m venv .venv && .venv/bin/pip install -r requirements.txt

# List trails
.venv/bin/python -m trailhead.cli list --region Suffolk --max-distance 3

# Plan a hike (tries local Ollama model first, falls back to offline template)
.venv/bin/python -m trailhead.cli plan --near "Centereach, NY" --distance 6 \
    --group "2 adults, 1 dog"

# Force the offline template (no LLM attempt)
.venv/bin/python -m trailhead.cli plan --near "Centereach, NY" --distance 6 --offline

# Use a different local model
.venv/bin/python -m trailhead.cli plan --near "Centereach, NY" --distance 6 \
    --model qwen2.5
```

Once installed, everything runs with zero network access — the whole point.

## How it works

- **`trailhead/planner.py`** — loads `data/trails.csv` and filters by
  area, distance (±1.5 mi), difficulty, and dog-friendliness. Ranks by
  closest distance match. Pure stdlib, no network.
- **`trailhead/model.py`** — `OllamaClient` talks to Ollama's local HTTP
  API (`POST /api/generate` on `localhost:11434`). If the daemon isn't
  reachable (or the call fails), it falls back to `offline_plan()`, a
  deterministic template grounded strictly in the trail row plus the same
  conservative timing math the system prompt prescribes.
- **`trailhead/prompts.py`** — system prompt with hiking sense:
  conservative timing (2.5 mph easy / 2 mph moderate / 1.75 mph hard,
  +30 min per 1000 ft, +5 min/mi for dogs/kids), explicit uncertainty
  about closures/weather, gear-first advice.
- **`data/trails.csv`** — 22 Suffolk/Nassau County (Long Island, NY)
  day-hike trails. Extend it with your own region: same columns, point
  `--trails-csv` at it.

## Trail data

Distances and elevation figures are compiled from park publications and
public trail guides (AllTrails community data, Suffolk County Parks,
NYS Parks, USFWS, Long Island Greenbelt Trail Conference) and marked
`(approx.)` where not cross-checked. **Verify conditions, closures, and
distances with the park before hiking** — this dataset is a starting
point, not a survey.

## Honesty notes

- Timing estimates are deliberately conservative; experienced hikers will
  beat them.
- The planner has no live data: no closures, weather, hunting seasons, or
  tick reports. It says so in every plan.
- The offline template never invents trailheads, blaze colors, or
  facilities — if the CSV doesn't say it, the plan doesn't claim it.

## License

MIT — do what you want, hike safe.
