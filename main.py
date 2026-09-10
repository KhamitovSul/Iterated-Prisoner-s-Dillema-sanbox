from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

import axelrod as axl
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator


app = FastAPI(title="Axelrod Lab", version="1.1.0")
STATIC_DIR = Path(__file__).resolve().parent / "static"

# Allows the UI to be served either by FastAPI (:8000) or Live Server (:5500).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    
)


@lru_cache
def strategy_catalog() -> dict[str, type[axl.Player]]:
    """Return every built-in Axelrod strategy, keyed by its canonical class name."""
    return {strategy.__name__: strategy for strategy in sorted(axl.strategies, key=lambda item: item.__name__.casefold())}


class TournamentRequest(BaseModel):
    strategies: list[str] = Field(min_length=2, max_length=8)
    turns: int = Field(default=150, ge=5, le=500)
    repetitions: int = Field(default=20, ge=1, le=100)
    noise: float = Field(default=0, ge=0, le=0.3)

    @field_validator("strategies")
    @classmethod
    def valid_unique_strategies(cls, value: list[str]) -> list[str]:
        catalog = strategy_catalog()
        if len(value) != len(set(value)):
            raise ValueError("Choose each strategy only once.")
        unknown = set(value) - set(catalog)
        if unknown:
            raise ValueError(f"Unknown strategies: {', '.join(sorted(unknown))}")
        return value


class MatchRequest(BaseModel):
    left: str
    right: str
    turns: int = Field(default=50, ge=5, le=500)
    noise: float = Field(default=0, ge=0, le=0.3)


def build_players(names: list[str]) -> list[axl.Player]:
    catalog = strategy_catalog()
    return [catalog[name]() for name in names]


@app.get("/api/strategies")
def list_strategies():
    def description(strategy: type[axl.Player]) -> str:
        doc_lines = (strategy.__doc__ or "").strip().splitlines()
        return next((line.strip() for line in doc_lines if line.strip()), "Built-in Axelrod strategy.")

    return [
        {"name": name, "description": description(strategy)}
        for name, strategy in strategy_catalog().items()
    ]


@app.post("/api/tournament")
def run_tournament(request: TournamentRequest):
    players = build_players(request.strategies)
    tournament = axl.Tournament(
        players, turns=request.turns, repetitions=request.repetitions, noise=request.noise
    )
    results = tournament.play(progress_bar=False)
    summary = results.summarise()
    rows = []
    for item in summary:
        total_score = sum(results.scores[item.Original_index])
        rows.append({
            # `scores` stores one aggregate tournament score per repetition.
            # Sum it to show the player's total across the entire tournament.
            # Keep the API identifier equal to the value selected in the UI.
            # Some Axelrod display names contain spaces (e.g. "Tit For Tat").
            "name": request.strategies[item.Original_index],
            "total_score": int(total_score),
            "mean_wins": round(float(item.Wins), 2),
        })
    rows.sort(key=lambda row: row["total_score"], reverse=True)
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    return {
        "ranking": rows,
        "meta": {"turns": request.turns, "repetitions": request.repetitions, "noise": request.noise},
    }


@app.post("/api/match")
def run_match(request: MatchRequest):
    catalog = strategy_catalog()
    if request.left not in catalog or request.right not in catalog:
        raise HTTPException(status_code=422, detail="Unknown strategy")
    left, right = catalog[request.left](), catalog[request.right]()
    match = axl.Match((left, right), turns=request.turns, noise=request.noise)
    history = match.play()
    game = axl.Game()
    left_total = right_total = 0
    rounds = []
    for number, plays in enumerate(history, 1):
        left_points, right_points = game.score(plays)
        left_total += left_points
        right_total += right_points
        rounds.append({
            "round": number, "left": str(plays[0]), "right": str(plays[1]),
            "left_total": int(left_total), "right_total": int(right_total),
        })
    return {"left": request.left, "right": request.right, "rounds": rounds,
            "totals": {"left": int(left_total), "right": int(right_total)}}


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

# uvicorn main:app --reload
