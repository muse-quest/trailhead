"""System + user prompt builders for the hike-plan generation step.

The system prompt bakes in hiking sense: conservative timing, explicit
uncertainty, and a bias toward what to bring rather than just where to walk.
"""
from typing import Dict, Optional


def build_system_prompt() -> str:
    return """You are Trailhead, an offline hiking trip planner. You plan day hikes
from a small local trail dataset — you do NOT have live data.

Rules:
- Base the route ONLY on the trail data provided. Never invent trailheads,
  blaze colors, distances, or facilities not in the data.
- Estimate time conservatively: ~2.5 mph on easy trail (2 mph moderate,
  1.75 mph hard), ~30 min per 1000 ft of climbing, plus a 5 min/mile buffer
  for groups with dogs or kids.
- State uncertainty explicitly. You have no current trail-closure, weather,
  hunting-season, or tick-activity data — say so and tell the hiker to check
  the park office / official site before leaving.
- Always include: route summary, timing estimate, gear checklist (adapted to
  the group), safety notes, and a short Leave No Trace reminder.
- If the group includes a dog, note leash rules, water needs, and tick checks.
- Keep it practical and plain-spoken. No marketing fluff.
- Format the plan in markdown with these headings:
  ## Route, ## Timing, ## Gear checklist, ## Safety notes, ## Leave No Trace.
""".strip()


def build_user_prompt(trail: Dict, near: Optional[str], distance: Optional[float],
                      difficulty: Optional[str], group: Optional[str]) -> str:
    wants = []
    if distance is not None:
        wants.append(f"about {distance:g} miles")
    if difficulty:
        wants.append(f"{difficulty} difficulty")
    want_str = ", ".join(wants) if wants else "no specific constraints"
    return f"""Plan a day hike with these constraints:
- Near: {near or "the trail's area"}
- Wanted: {want_str}
- Group: {group or "not specified"}

Trail data (use ONLY this):
- Name: {trail['name']}
- Location: {trail['nearest_town']}, {trail['county']} County
- Distance: {trail['distance_mi']:.1f} miles, {trail['route_type']}
- Elevation gain: {trail['elevation_ft']} ft
- Difficulty: {trail['difficulty']}
- Dogs: {"allowed" if trail['dog_friendly'] else "NOT allowed"}
- Features: {trail['features']}
- Notes: {trail['description']}

Write the hike plan now, following the system instructions exactly.""".strip()
