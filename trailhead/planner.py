"""Offline trail retrieval: load the bundled CSV and filter it against constraints.

No network calls here — everything is local, which is the whole point.
"""
import csv
from pathlib import Path
from typing import List, Dict, Optional

DEFAULT_CSV = Path(__file__).resolve().parent.parent / "data" / "trails.csv"

DIFFICULTIES = ("easy", "moderate", "hard")


def load_trails(csv_path: Optional[str] = None) -> List[Dict]:
    path = Path(csv_path) if csv_path else DEFAULT_CSV
    trails: List[Dict] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["distance_mi"] = float(row["distance_mi"])
            row["elevation_ft"] = int(row["elevation_ft"])
            row["dog_friendly"] = row["dog_friendly"].strip().lower() in ("yes", "y", "true", "1")
            row["nearby_towns"] = [t.strip() for t in row.get("nearby_towns", "").split(",") if t.strip()]
            trails.append(row)
    return trails


def _matches_near(trail: Dict, near: str) -> bool:
    q = near.strip().lower().rstrip(", ny").strip()
    haystacks = [
        trail["name"].lower(),
        trail["nearest_town"].lower(),
        trail["county"].lower(),
    ] + [t.lower() for t in trail["nearby_towns"]]
    return any(q in h for h in haystacks)


def filter_trails(
    trails: List[Dict],
    near: Optional[str] = None,
    distance: Optional[float] = None,
    difficulty: Optional[str] = None,
    wants_dog: bool = False,
    tolerance: float = 1.5,
) -> List[Dict]:
    """Filter trails by constraints, ranked by distance closeness then elevation."""
    out = []
    for t in trails:
        if near and not _matches_near(t, near):
            continue
        if distance is not None and abs(t["distance_mi"] - distance) > tolerance:
            continue
        if difficulty and t["difficulty"].strip().lower() != difficulty.strip().lower():
            continue
        if wants_dog and not t["dog_friendly"]:
            continue
        out.append(t)

    def rank(t: Dict):
        dist_gap = abs(t["distance_mi"] - distance) if distance is not None else 0.0
        return (dist_gap, -t["elevation_ft"])

    return sorted(out, key=rank)


def format_trail_line(i: int, t: Dict) -> str:
    dog = "🐕" if t["dog_friendly"] else "🚫🐕"
    return (
        f"{i}. {t['name']} — {t['nearest_town']} ({t['county']} Co.)\n"
        f"   {t['distance_mi']:.1f} mi {t['route_type']}, {t['elevation_ft']} ft gain, "
        f"{t['difficulty']} {dog}\n"
        f"   {t['description']}"
    )
