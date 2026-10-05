"""Trailhead CLI — offline-first hiking trip planner.

Retrieval (planner.py) filters the bundled CSV; generation (model.py) calls a
local Ollama model or falls back to a deterministic offline template.
"""
import time
from pathlib import Path
from typing import Optional

import typer

from .planner import load_trails, filter_trails, format_trail_line
from .model import OllamaClient, offline_plan, estimate_time
from .prompts import build_system_prompt, build_user_prompt

app = typer.Typer(
    help="Trailhead — a hiking trip planner that works with zero bars of signal.",
    no_args_is_help=True,
)


@app.command()
def plan(
    near: Optional[str] = typer.Option(None, "--near", help="Town/area to search near, e.g. 'Centereach, NY'"),
    distance: Optional[float] = typer.Option(None, "--distance", help="Target distance in miles"),
    difficulty: Optional[str] = typer.Option(None, "--difficulty", help="easy | moderate | hard"),
    group: Optional[str] = typer.Option(None, "--group", help="Who's coming, e.g. '2 adults, 1 dog'"),
    model: str = typer.Option("llama3.2", "--model", help="Ollama model to use for plan generation"),
    offline: bool = typer.Option(False, "--offline", help="Skip the LLM; use the built-in offline template"),
    trails_csv: Optional[Path] = typer.Option(None, "--trails-csv", help="Use a different trails CSV"),
):
    """Plan a day hike from the offline trail dataset."""
    trails = load_trails(str(trails_csv) if trails_csv else None)
    wants_dog = bool(group and "dog" in group.lower())
    matches = filter_trails(
        trails, near=near, distance=distance,
        difficulty=difficulty, wants_dog=wants_dog,
    )
    if not matches:
        typer.echo("✗ No matching trails in the offline dataset. Try widening --distance or dropping --difficulty.")
        raise typer.Exit(code=1)

    typer.echo(f"✓ Found {len(matches)} matching trail(s) (offline dataset)")
    trail = matches[0]
    typer.echo(f"✓ Selected: {trail['name']} ({trail['distance_mi']:.1f} mi, {trail['difficulty']})")
    typer.echo("")

    params = dict(near=near, distance=distance, difficulty=difficulty, group=group)
    engine = "offline-template"

    if not offline:
        client = OllamaClient(model=model)
        if client.is_available():
            typer.echo(f"✓ Generating plan with {model} (local, no network)…")
            start = time.time()
            try:
                text = client.generate(
                    build_user_prompt(trail, near, distance, difficulty, group),
                    system=build_system_prompt(),
                )
                elapsed = time.time() - start
                engine = f"ollama/{model}"
                typer.echo(f"✓ Plan generated locally in {elapsed:.1f}s (engine: {engine})")
                typer.echo("")
                typer.echo(text)
                return
            except Exception as e:  # fail soft to the template, never to a traceback
                typer.echo(f"⚠ LLM call failed ({e}) — using offline template.")
        else:
            typer.echo("⚠ Ollama not reachable at localhost:11434 — using offline template (no LLM).")

    start = time.time()
    text = offline_plan(trail, near, distance, difficulty, group)
    elapsed = time.time() - start
    typer.echo(f"✓ Plan generated in {elapsed:.2f}s (engine: {engine})")
    typer.echo("")
    typer.echo(text)


@app.command("list")
def list_trails(
    region: Optional[str] = typer.Option(None, "--region", help="Filter by town/county text"),
    difficulty: Optional[str] = typer.Option(None, "--difficulty", help="easy | moderate | hard"),
    max_distance: Optional[float] = typer.Option(None, "--max-distance", help="Max distance in miles"),
    trails_csv: Optional[Path] = typer.Option(None, "--trails-csv", help="Use a different trails CSV"),
):
    """List trails in the offline dataset."""
    trails = load_trails(str(trails_csv) if trails_csv else None)
    rows = [t for t in trails
            if (not region or region.lower() in (t["name"] + t["nearest_town"] + t["county"]).lower())
            and (not difficulty or t["difficulty"].lower() == difficulty.lower())
            and (max_distance is None or t["distance_mi"] <= max_distance)]
    if not rows:
        typer.echo("No trails match.")
        raise typer.Exit(code=1)
    typer.echo(f"{len(rows)} trail(s) in offline dataset:\n")
    for i, t in enumerate(rows, 1):
        typer.echo(format_trail_line(i, t))
        typer.echo("")


if __name__ == "__main__":
    app()
