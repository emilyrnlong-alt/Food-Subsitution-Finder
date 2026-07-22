import streamlit as st
from substitution_engine import SubstitutionEngine
 
# Create the engine once
engine = SubstitutionEngine()
 
# Page setup
st.set_page_config(page_title="Healthier Food Substitutes", page_icon="🥗", layout="centered")
 
st.title("🥗 Substitution Finder")
st.write("Enter a food you eat often, and get healthier alternatives with the nutrition facts to back it up.")
 
# --- User inputs ---
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("Enter a food:", placeholder="e.g. pasta, white rice, ice cream")
with col2:
    top_n = st.selectbox("How many options?", [1, 2, 3], index=2)
 
st.divider()
 
# --- Results ---
if query:
    result = engine.get_substitutes(query, top_n=top_n)
 
    if result["found"]:
        orig = result["original_nutrition"]
 
        st.subheader(f"📌 Matched: {result['matched_food'].title()}")
        st.caption(f"Category: {result['category'].title()}")
 
        # Show original nutrition facts as metrics
        st.write("**Original nutrition (per 100g):**")
        m1, m2, m3 = st.columns(3)
        m1.metric("Calories", f"{orig['calories_per_100g']:.0f} kcal")
        m2.metric("Protein", f"{orig['protein_per_100g']:.1f} g")
        m3.metric("Fiber", f"{orig['fiber_per_100g']:.1f} g")
 
        st.write("### Healthier substitutes")
 
        for sub in result["substitutes"]:
            with st.container(border=True):
                st.markdown(f"#### {sub['name']}")
                st.write(sub["reason"])
 
                # Nutrition comparison, with deltas shown automatically by st.metric
                c1, c2, c3 = st.columns(3)
                c1.metric(
                    "Calories",
                    f"{sub['calories_per_100g']:.0f} kcal",
                    delta=f"{sub['calorie_delta_vs_original']:.0f} kcal",
                    delta_color="inverse",  # fewer calories shown as "good" (green)
                )
                c2.metric(
                    "Protein",
                    f"{sub['protein_per_100g']:.1f} g",
                    delta=f"{sub['protein_per_100g'] - orig['protein_per_100g']:+.1f} g",
                )
                c3.metric(
                    "Fiber",
                    f"{sub['fiber_per_100g']:.1f} g",
                    delta=f"{sub['fiber_per_100g'] - orig['fiber_per_100g']:+.1f} g",
                )
 
    else:
        st.warning(f"No exact match found for **{query}**.")
        if result["suggestions"]:
            st.write("Did you mean one of these?")
            st.write(", ".join(result["suggestions"]))
        else:
            st.write("Try typing `list` below to see all known foods.")
 
# --- Optional: browse all foods ---
with st.expander("See all foods in the database"):
    for food in engine.list_all_foods():
        st.write("-", food.title())