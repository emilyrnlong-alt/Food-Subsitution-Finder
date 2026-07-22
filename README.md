# Food-Subsitution-Finder
# Healthier Food Substitution Finder

A small, UI Python project that takes a food name (e.g. `"pasta"`)
and returns healthier substitutes (e.g. chickpea pasta, lentil pasta,
zucchini noodles) along with a nutrition comparison and the reasoning
behind each suggestion.

## Project structure

```
food_sub_project/
├── data/
│   └── substitutions.json   # curated database: foods -> healthier substitutes
├── substitution_engine.py   # core logic (import this into any UI)
├── main.py                  # CLI for testing
├── app.py
├── requirements.txt
└── README.md
```

## Running it

No installs needed as everything runs on the standard library.

```bash
cd food_sub_project
python main.py
```

Then type a food name, e.g.:

```
Food> pasta
Food> spaghetti      <- also works, matched via aliases/fuzzy match
Food> rice
Food> list           <- shows every food currently in the database
Food> quit
```

## How it works

- **`data/substitutions.json`** is the "existing database" — a curated
  set of ~25 common foods, each with baseline nutrition (calories,
  protein, fiber per 100g), a category, aliases (so "spaghetti" resolves
  to "pasta"), and a list of substitute foods with their own nutrition
  and a plain-English reason they're healthier.

- **`substitution_engine.py`** exposes one main class, `SubstitutionEngine`:
  - `find_entry(query)` — resolves free text to a database entry using
    exact match → fuzzy match (`difflib`) → substring match, in that order.
  - `get_substitutes(query, top_n=3)` — the main function you'll call
    from your UI. Returns a dict with the matched food, its nutrition,
    and ranked substitutes (ranked by a simple "more fiber/protein per
    calorie" score).
  - `list_all_foods()` — useful for an autocomplete dropdown later.

- **`main.py`** is just a CLI wrapper for testing — swap this out for
  your Flask/Streamlit/whatever UI without touching the engine.

## Example return value

```python
from substitution_engine import SubstitutionEngine

engine = SubstitutionEngine()
result = engine.get_substitutes("pasta")
```

```json
{
  "found": true,
  "query": "pasta",
  "matched_food": "pasta",
  "category": "grains",
  "original_nutrition": {
    "calories_per_100g": 131,
    "protein_per_100g": 5.0,
    "fiber_per_100g": 1.8
  },
  "substitutes": [
    {
      "name": "Lentil pasta",
      "reason": "High in plant protein and fiber, lower glycemic impact...",
      "calories_per_100g": 155,
      "protein_per_100g": 13.0,
      "fiber_per_100g": 7.0,
      "calorie_delta_vs_original": 24.0
    }
  ]
}
```

## Extending it

1. **Add more foods**: just add entries to `data/substitutions.json`
   following the existing shape. No code changes needed.
2. **Hook up your UI**: import `SubstitutionEngine`, call
   `get_substitutes(user_input)`, and render the returned dict.
3. **Optional live nutrition data**: there's a commented-out helper at
   the bottom of `substitution_engine.py` for pulling real-time nutrition
   facts from USDA's free FoodData Central API — useful if a user enters
   a food that isn't in the curated database yet.
4. **Handling "not found"**: `get_substitutes` returns
   `{"found": False, "suggestions": [...]}` when nothing matches well,
   so your UI can show "did you mean...?" prompts.
