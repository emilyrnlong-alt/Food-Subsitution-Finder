"""
main.py

Simple command-line interface for testing the SubstitutionEngine.
Run this to try it out before you build your own UI on top of
`substitution_engine.py`.

Usage:
    python main.py
"""

from substitution_engine import SubstitutionEngine


def print_result(result: dict) -> None:
    if not result["found"]:
        print(f"\nNo exact match found for '{result['query']}'.")
        if result["suggestions"]:
            print("Did you mean:", ", ".join(result["suggestions"]))
        else:
            print("Try one of the known foods (type 'list' to see all).")
        return

    orig = result["original_nutrition"]
    print(f"\nMatched: {result['matched_food'].title()}  ({result['category']})")
    print(
        f"  Original — {orig['calories_per_100g']} kcal, "
        f"{orig['protein_per_100g']}g protein, {orig['fiber_per_100g']}g fiber (per 100g)"
    )
    print("\n  Healthier substitutes:")
    for i, sub in enumerate(result["substitutes"], start=1):
        delta = sub["calorie_delta_vs_original"]
        delta_str = f"{delta:+.0f} kcal vs original"
        print(f"   {i}. {sub['name']}  ({delta_str})")
        print(f"      {sub['reason']}")
        print(
            f"      -> {sub['calories_per_100g']} kcal, "
            f"{sub['protein_per_100g']}g protein, {sub['fiber_per_100g']}g fiber (per 100g)"
        )


def main() -> None:
    engine = SubstitutionEngine()

    print("Healthier Food Substitution Finder")
    print("Type a food (e.g. 'pasta', 'white rice', 'ice cream').")
    print("Type 'list' to see all known foods, or 'quit' to exit.\n")

    while True:
        query = input("Food> ").strip()
        if not query:
            continue
        if query.lower() in {"quit", "exit", "q"}:
            break
        if query.lower() == "list":
            for food in engine.list_all_foods():
                print(" -", food)
            continue

        result = engine.get_substitutes(query)
        print_result(result)


if __name__ == "__main__":
    main()
