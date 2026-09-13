from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import axelrod as axl
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator


app = FastAPI(
    title="Axelrod Lab",
    version="1.1.0"
)

STATIC_DIR = Path(__file__).resolve().parent / "static"


# Разрешаем запросы от Live Server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)


# Получаем список всех стратегий Axelrod.
# lru_cache нужен, чтобы не строить этот список заново
# при каждом запросе.
@lru_cache
def strategy_catalog() -> dict[str, type[axl.Player]]:
    strategies = axl.strategies

    sorted_strategies = sorted(
        strategies,
        key=lambda strategy: strategy.__name__.casefold()
    )

    catalog = {}

    for strategy in sorted_strategies:
        name = strategy.__name__
        catalog[name] = strategy

    return catalog


class TournamentRequest(BaseModel):
    strategies: list[str] = Field(
        min_length=2,
        max_length=8
    )

    turns: int = Field(
        default=150,
        ge=5,
        le=500
    )

    repetitions: int = Field(
        default=20,
        ge=1,
        le=100
    )

    noise: float = Field(
        default=0,
        ge=0,
        le=0.3
    )

    @field_validator("strategies")
    @classmethod
    def valid_unique_strategies(
        cls,
        value: list[str]
    ) -> list[str]:

        catalog = strategy_catalog()

        # Нельзя выбрать одну стратегию несколько раз.
        if len(value) != len(set(value)):
            raise ValueError(
                "Choose each strategy only once."
            )

        # Проверяем, что все стратегии существуют.
        unknown_strategies = set(value) - set(catalog)

        if unknown_strategies:
            unknown_names = ", ".join(
                sorted(unknown_strategies)
            )

            raise ValueError(
                f"Unknown strategies: {unknown_names}"
            )

        return value


class MatchRequest(BaseModel):
    left: str

    right: str

    turns: int = Field(
        default=50,
        ge=5,
        le=500
    )

    noise: float = Field(
        default=0,
        ge=0,
        le=0.3
    )


def build_players(
    names: list[str]
) -> list[axl.Player]:

    catalog = strategy_catalog()

    players = []

    for name in names:
        strategy_class = catalog[name]
        strategy = strategy_class()

        players.append(strategy)

    return players


@app.get("/api/strategies")
def list_strategies():

    def get_description(
        strategy: type[axl.Player]
    ) -> str:

        documentation = strategy.__doc__

        if documentation is None:
            return "Built-in Axelrod strategy."

        documentation = documentation.strip()

        lines = documentation.splitlines()

        for line in lines:
            line = line.strip()

            if line:
                return line

        return "Built-in Axelrod strategy."

    catalog = strategy_catalog()

    result = []

    for name, strategy in catalog.items():

        description = get_description(strategy)

        result.append({
            "name": name,
            "description": description
        })

    return result


@app.post("/api/tournament")
def run_tournament(
    request: TournamentRequest
):

    players = build_players(request.strategies)

    # Axelrod сам использует кэширование для
    # детерминированных матчей внутри турнира.
    #
    # Поэтому НЕ передаём сюда deterministic_cache.
    tournament = axl.Tournament(
        players,
        turns=request.turns,
        repetitions=request.repetitions,
        noise=request.noise
    )

    results = tournament.play(
        progress_bar=False
    )

    summary = results.summarise()

    rows = []

    for item in summary:

        strategy_index = item.Original_index

        strategy_scores = results.scores[
            strategy_index
        ]

        total_score = sum(strategy_scores)

        row = {
            "name": request.strategies[strategy_index],
            "total_score": int(total_score),
            "mean_wins": round(
                float(item.Wins),
                2
            )
        }

        rows.append(row)

    # Сортируем стратегии по общему количеству очков.
    rows.sort(
        key=lambda row: row["total_score"],
        reverse=True
    )

    # Добавляем место в рейтинге.
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank

    return {
        "ranking": rows,

        "meta": {
            "turns": request.turns,
            "repetitions": request.repetitions,
            "noise": request.noise
        }
    }


@app.post("/api/match")
def run_match(
    request: MatchRequest
):

    catalog = strategy_catalog()

    # Проверяем левую стратегию.
    if request.left not in catalog:
        raise HTTPException(
            status_code=422,
            detail="Unknown strategy"
        )

    # Проверяем правую стратегию.
    if request.right not in catalog:
        raise HTTPException(
            status_code=422,
            detail="Unknown strategy"
        )

    left_class = catalog[request.left]
    right_class = catalog[request.right]

    left = left_class()
    right = right_class()

    # Для отдельного Match можно использовать
    # DeterministicCache.
    #
    # Если один и тот же детерминированный матч
    # будет запускаться повторно, результат можно
    # взять из cache вместо повторного вычисления.
    cache = axl.DeterministicCache()

    match = axl.Match(
        (left, right),
        turns=request.turns,
        noise=request.noise,
        deterministic_cache=cache
    )

    history = match.play()

    game = axl.Game()

    left_total = 0
    right_total = 0

    rounds = []

    for number, plays in enumerate(history, 1):

        left_action = plays[0]
        right_action = plays[1]

        left_points, right_points = game.score(
            plays
        )

        left_total += left_points
        right_total += right_points

        round_data = {
            "round": number,
            "left": str(left_action),
            "right": str(right_action),
            "left_total": int(left_total),
            "right_total": int(right_total)
        }

        rounds.append(round_data)

    return {
        "left": request.left,
        "right": request.right,

        "rounds": rounds,

        "totals": {
            "left": int(left_total),
            "right": int(right_total)
        }
    }


# Отдаём frontend через FastAPI.
app.mount(
    "/",
    StaticFiles(
        directory=STATIC_DIR,
        html=True
    ),
    name="static"
)