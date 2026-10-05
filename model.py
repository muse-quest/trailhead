"""Model layer: call a local open-weight model via Ollama's HTTP API.

Ollama serves on http://localhost:11434 — no internet required, just the
daemon and a pulled model. If Ollama isn't reachable, plan generation falls
back to a deterministic offline template (clearly labeled), so the CLI still
works at the trailhead with zero infrastructure.
"""
import json
import urllib.request
import urllib.error
from typing import Dict, Optional


class OllamaClient:
    def __init__(self, model: str = "llama3.2",
                 host: str = "http://localhost:11434",
                 timeout: int = 240):
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout

    def is_available(self) -> bool:
        try:
            with urllib.request.urlopen(self.host + "/api/tags", timeout=3) as r:
                return r.status == 200
        except Exception:
            return False

    def generate(self, prompt: str, system: str = "") -> str:
        body = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
        }).encode("utf-8")
        req = urllib.request.Request(
            self.host + "/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data["response"].strip()


def estimate_time(trail: Dict, group: Optional[str]) -> str:
    """Conservative hiking-time estimate (Naismith-ish rule of thumb).

    Same formula the system prompt prescribes, so template and LLM agree.
    """
    pace = {"easy": 2.5, "moderate": 2.0, "hard": 1.75}.get(
        trail["difficulty"].strip().lower(), 2.0)
    miles = trail["distance_mi"]
    elev = trail["elevation_ft"]
    hours = miles / pace + (elev / 1000.0) * 0.5
    if group and any(k in group.lower() for k in ("dog", "kid", "child")):
        hours += miles * (5 / 60.0)  # 5 min/mile buffer
    h, m = divmod(int(round(hours * 60)), 60)
    return f"{h}h {m:02d}m (conservative; add breaks)"


def offline_plan(trail: Dict, near: Optional[str], distance: Optional[float],
                 difficulty: Optional[str], group: Optional[str]) -> str:
    """Deterministic offline plan template — used when no LLM is available.

    Grounded strictly in the trail row + the same conservative timing math
    the system prompt prescribes. Never invents trailheads or blazes.
    """
    has_dog = bool(group and "dog" in group.lower())
    route_kind = trail["route_type"]
    if route_kind == "loop":
        route_advice = ("Walk the loop in whichever direction the blazes suggest at "
                        "the trailhead; loops need no shuttle and you finish at your car.")
    else:
        route_advice = ("This is an out-and-back: hike half your target distance, then turn "
                        "around. You finish at your car with no shuttle needed.")

    gear = [
        "Water: at least 0.5 L per person per hour of hiking (more in heat)",
        "Sturdy closed-toe shoes — some sections have roots and rocks",
        "Tick protection: long pants, repellent, full tick check after",
        "Charged phone + a downloaded offline map (this planner works offline; maps should too)",
        "Snacks, small first-aid kit, rain layer",
    ]
    if has_dog:
        gear += [
            "Dog: leash (required), water + collapsible bowl, poop bags, tick preventative",
        ]
    if trail["elevation_ft"] >= 200:
        gear.append("Trekking poles if you have cranky knees — the climbs are short but real")

    lines = [
        f"## Your hike: {trail['name']}",
        f"**Distance:** {trail['distance_mi']:.1f} mi {route_kind} · "
        f"**Elevation:** ~{trail['elevation_ft']} ft · **Est. time:** {estimate_time(trail, group)}",
        "",
        "## Route",
        f"1. Start at the {trail['nearest_town']} trailhead — arrive before 9 AM on weekends; lots fill.",
        f"2. {route_advice}",
        f"3. Features along the way: {trail['features']}.",
        f"4. Note: {trail['description']}",
        "",
        "## Timing",
        f"- Moving estimate: {estimate_time(trail, group)} at a conservative pace.",
        "- Start early enough to finish with 1 hour of daylight to spare.",
        "- I don't have current trail-closure or hunting-season data — check the park office before you go.",
        "",
        "## Gear checklist",
    ]
    lines += [f"- [ ] {g}" for g in gear]
    safety = [
        "- Tell someone your route and expected return time.",
        "- Long Island trails mean ticks: check yourself (and the dog) thoroughly after.",
        "- If thunderheads build, turn back — no summit is worth lightning.",
        "- Carry more water than you think you need; there is no potable water on-trail.",
    ]
    if not trail["dog_friendly"]:
        if has_dog:
            safety.append("- Heads up: this trail does NOT allow dogs — pick a dog-friendly one from the list instead.")
        else:
            safety.append("- Dogs are NOT allowed on this trail.")
    lines += ["", "## Safety notes"] + safety
    lines += [
        "",
        "## Leave No Trace",
        "- Pack out everything, including dog waste bags — don't leave them 'for later'.",
        "- Stay on marked trail; the pine barrens and wetlands recover slowly.",
        "",
        "_Generated offline with the built-in template (no LLM reachable). "
        "Install Ollama and pull a model for AI-generated plans._",
    ]
    return "\n".join(lines)
