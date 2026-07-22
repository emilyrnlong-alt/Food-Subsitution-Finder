"""
substitution_engine.py

Core logic for the Healthier Food Substitution project.

This module loads a curated JSON database of foods and their healthier
substitutes, then lets you look up substitutes for whatever a user types
in (even if it's not an exact match, e.g. "spaghetti" -> "pasta").

Designed to be UI-agnostic: import `SubstitutionEngine` into a Flask app,
a Streamlit app, a CLI, whatever you build next.
"""

from __future__ import annotations

import json
import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


DEFAULT_DB_PATH = Path(__file__).parent / "data" / "substitutions.json"


@dataclass
class Substitute:
    name: str
    reason: str
    calories_per_100g: float
    protein_per_100g: float
    fiber_per_100g: float

    def calorie_delta(self, original_calories: float) -> float:
        """Negative number = fewer calories than the original food."""
        return round(self.calories_per_100g - original_calories, 1)


@dataclass
class FoodEntry:
    key: str
    category: str
    calories_per_100g: float
    protein_per_100g: float
    fiber_per_100g: float
    aliases: list[str] = field(default_factory=list)
    substitutes: list[Substitute] = field(default_factory=list)


class SubstitutionEngine:
    """Loads the substitution database and answers lookup queries."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.entries: dict[str, FoodEntry] = {}
        # Maps every alias/name (lowercased) -> canonical key, for fast lookup
        self._alias_index: dict[str, str] = {}
        self._load()

    # ------------------------------------------------------------------ #
    # Loading
    # ------------------------------------------------------------------ #
    def _load(self) -> None:
        with open(self.db_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        for key, data in raw.items():
            substitutes = [
                Substitute(
                    name=s["name"],
                    reason=s["reason"],
                    calories_per_100g=s["calories_per_100g"],
                    protein_per_100g=s["protein_per_100g"],
                    fiber_per_100g=s["fiber_per_100g"],
                )
                for s in data.get("substitutes", [])
            ]
            entry = FoodEntry(
                key=key,
                category=data.get("category", "uncategorized"),
                calories_per_100g=data["calories_per_100g"],
                protein_per_100g=data["protein_per_100g"],
                fiber_per_100g=data["fiber_per_100g"],
                aliases=data.get("aliases", []),
                substitutes=substitutes,
            )
            self.entries[key] = entry

            # Index the canonical key and all aliases (lowercased)
            self._alias_index[key.lower()] = key
            for alias in entry.aliases:
                self._alias_index[alias.lower()] = key

    # ------------------------------------------------------------------ #
    # Lookup
    # ------------------------------------------------------------------ #
    def _normalize(self, text: str) -> str:
        return text.strip().lower()

    def find_entry(self, query: str) -> Optional[FoodEntry]:
        """
        Try to resolve a free-text query (e.g. "Spaghetti", "white rice ")
        to a FoodEntry. Falls back to fuzzy matching against known
        names/aliases if there's no exact hit.
        """
        norm = self._normalize(query)

        # 1. Exact match against a name or alias
        if norm in self._alias_index:
            return self.entries[self._alias_index[norm]]

        # 2. Fuzzy match (handles typos / near-misses)
        close = difflib.get_close_matches(
            norm, self._alias_index.keys(), n=1, cutoff=0.72
        )
        if close:
            return self.entries[self._alias_index[close[0]]]

        # 3. Substring match as a last resort (e.g. "cream" matches "sour cream")
        for alias, key in self._alias_index.items():
            if norm in alias or alias in norm:
                return self.entries[key]

        return None

    def get_substitutes(self, query: str, top_n: int = 3) -> dict:
        """
        Main public method. Returns a dict describing the matched food
        and its healthier substitutes, ranked by fiber-per-calorie
        (a simple proxy for "more nutrient-dense per calorie").

        Returns {"found": False, "suggestions": [...]} if nothing matches,
        with `suggestions` being the closest known food names to help
        the UI prompt the user.
        """
        entry = self.find_entry(query)

        if entry is None:
            suggestions = difflib.get_close_matches(
                self._normalize(query), self._alias_index.keys(), n=5, cutoff=0.4
            )
            return {
                "found": False,
                "query": query,
                "suggestions": sorted(set(suggestions)),
            }

        def score(sub: Substitute) -> float:
            # Higher fiber and lower calories relative to the original = better score
            calorie_score = entry.calories_per_100g - sub.calories_per_100g
            fiber_score = (sub.fiber_per_100g - entry.fiber_per_100g) * 10
            protein_score = (sub.protein_per_100g - entry.protein_per_100g) * 2
            return calorie_score + fiber_score + protein_score

        ranked = sorted(entry.substitutes, key=score, reverse=True)[:top_n]

        return {
            "found": True,
            "query": query,
            "matched_food": entry.key,
            "category": entry.category,
            "original_nutrition": {
                "calories_per_100g": entry.calories_per_100g,
                "protein_per_100g": entry.protein_per_100g,
                "fiber_per_100g": entry.fiber_per_100g,
            },
            "substitutes": [
                {
                    "name": sub.name,
                    "reason": sub.reason,
                    "calories_per_100g": sub.calories_per_100g,
                    "protein_per_100g": sub.protein_per_100g,
                    "fiber_per_100g": sub.fiber_per_100g,
                    "calorie_delta_vs_original": sub.calorie_delta(
                        entry.calories_per_100g
                    ),
                }
                for sub in ranked
            ],
        }

    def list_all_foods(self) -> list[str]:
        """Handy for building an autocomplete dropdown in your future UI."""
        return sorted(self.entries.keys())


# ---------------------------------------------------------------------- #
# Optional: real-time nutrition lookup via USDA FoodData Central API
# ---------------------------------------------------------------------- #
# The curated JSON above is enough to run the whole project offline.
# If you later want live nutrition data (e.g. for foods not in the
# database, or to double check numbers), USDA's FoodData Central API
# is free and simple to use:
#
#   1. Get a free API key: https://fdc.nal.usda.gov/api-key-signup.html
#   2. pip install requests
#   3. Uncomment and use the function below.
#
# import requests
#
# def fetch_nutrition_from_usda(food_name: str, api_key: str) -> dict | None:
#     url = "https://api.nal.usda.gov/fdc/v1/foods/search"
#     params = {"query": food_name, "pageSize": 1, "api_key": api_key}
#     resp = requests.get(url, params=params, timeout=10)
#     resp.raise_for_status()
#     results = resp.json().get("foods", [])
#     return results[0] if results else None
