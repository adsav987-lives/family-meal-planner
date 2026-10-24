from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Page config
st.set_page_config(
    page_title="Family Meal Planner",
    page_icon="🍳",
    layout="wide"
)

st.title("🍳 Family Meal Planner & Shopping List")
st.markdown("Plan your weekly meals, grow your recipe library, and generate a categorized shopping list instantly.")

# ==============================================================================
# 1. GOOGLE SHEETS LIVE DATA CONNECTION (WITH VISIBLE STATUS)
# ==============================================================================
@st.cache_data(ttl=60)
def load_data_from_sheet():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Read worksheet 'Meal_Library'
        df = conn.read(worksheet="Meal_Library", usecols=[0, 1, 2], ttl=5)
        df = df.dropna(subset=["Meal Name"])
        return df, None
    except Exception as e:
        # Fallback dataset if connection is not yet configured
        fallback_df = pd.DataFrame({
            "Meal Name": [
                "Chicken Curry",
                "Homemade Pizza",
                "Lamb Souvlaki",
                "Chilli",
                "Filled Pasta with Salmon",
                "Roast Chook and Veggies",
            ],
            "Category / Tags": [
                "Chicken, Curry, Rice",
                "Italian, Quick",
                "Greek, Lamb",
                "Mexican, Beef, Quick",
                "Italian, Seafood",
                "Roast, Chicken",
            ],
            "Ingredients & Aisle Tags": [
                "Chicken breast | Meat & Seafood, Spinach (fresh) | Fresh Produce, Chickpeas | Pantry, Lentils | Pantry, Curry Paste | Pantry, Jasmin Rice | Pantry",
                "Pizza bases | Bakery, Passata | Pantry, Cheddar (grated) | Dairy & Eggs",
                "Lamb chops | Meat & Seafood, Flatbread | Bakery, Feta cheese | Dairy & Eggs, Cucumber | Fresh Produce, Tomatoes | Fresh Produce",
                "Mince meat | Meat & Seafood, Tinned tomatoes | Pantry, Four-bean mix | Pantry, Carrots | Fresh Produce, Onions | Fresh Produce, Garlic | Fresh Produce",
                "Filled pasta | Refrigerated Meal Components, Salmon pieces | Meat & Seafood, Fresh mixed vegetables | Fresh Produce, Cream | Dairy & Eggs, Garlic & herb sauce | Pantry",
                "Whole chicken | Meat & Seafood, Potatoes | Fresh Produce, Carrots | Fresh Produce, Pumpkin | Fresh Produce, Butter | Dairy & Eggs",
            ],
        })
        return fallback_df, str(e)

df_library, connection_error = load_data_from_sheet()

# Sidebar: Shows connection status so you know whether it's live or using fallback
with st.sidebar:
    st.subheader("Google Sheet Status")
    if connection_error:
        st.warning("⚠️ Using Fallback Data")
        st.caption(f"Reason: {connection_error}")
    else:
        st.success("✅ Connected to Google Sheet!")

    if st.button("🔄 Reload from Google Sheet"):
        st.cache_data.clear()
        df_library, connection_error = load_data_from_sheet()
        st.rerun()

# ==============================================================================
# 2. NAVIGATION TABS
# ==============================================================================
tab_plan, tab_library, tab_shopping, tab_add = st.tabs(
    ["📅 Weekly Planner", "📚 Meal Library", "🛒 Shopping List", "➕ Add Recipe"]
)

with tab_plan:
    st.subheader("Plan Your Week")

    today = datetime.today()
    default_start_of_week = today - timedelta(days=today.weekday())
    week_date = st.date_input("Select Week Starting (Monday)", default_start_of_week)

    st.markdown(f"*Planning meals for the week of **{week_date.strftime('%A, %B %d, %Y')}***")

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    meal_options = ["--- None ---"] + list(df_library["Meal Name"].dropna())

    if "weekly_selections" not in st.session_state:
        st.session_state.weekly_selections = {}

    selected_meals = {}
    cols = st.columns(2)

    for index, day in enumerate(days):
        current_day_date = week_date + timedelta(days=index)
        with cols[index % 2]:
            st.markdown(f"**{day} ({current_day_date.strftime('%b %d')})**")
            lunch = st.selectbox(f"Lunch ({day})", meal_options, key=f"lunch_{day}_{week_date}")
            dinner = st.selectbox(f"Dinner ({day})", meal_options, key=f"dinner_{day}_{week_date}")
            selected_meals[day] = {
                "Date": current_day_date.strftime("%Y-%m-%d"),
                "Lunch": lunch,
                "Dinner": dinner,
            }

    if st.button("💾 Save Weekly Plan", type="primary"):
        st.session_state.weekly_selections = selected_meals
        st.success(f"Weekly plan for the week of {week_date.strftime('%b %d, %Y')} saved successfully!")

with tab_library:
    st.subheader("Master Recipe & Meal Bank")
    st.markdown("Meals loaded from your Google Sheet (`Meal_Library` tab):")
    st.dataframe(df_library, use_container_width=True)

with tab_shopping:
    st.subheader("🛒 Smart Categorized Shopping List")
    st.markdown("Automatically compiled from your selected weekly meals, sorted by supermarket aisle.")

    active_plan = st.session_state.get("weekly_selections", selected_meals)
    all_chosen_meals = []
    for day_info in active_plan.values():
        if day_info.get("Lunch") and day_info["Lunch"] != "--- None ---":
            all_chosen_meals.append(day_info["Lunch"])
        if day_info.get("Dinner") and day_info["Dinner"] != "--- None ---":
            all_chosen_meals.append(day_info["Dinner"])

    if not all_chosen_meals:
        st.info("💡 Select your meals in the **Weekly Planner** tab, then return here to view your categorized shopping list!")
    else:
        st.success(f"Aggregating ingredients from: {', '.join(set(all_chosen_meals))}")
        aisle_buckets = {}

        for meal_name in all_chosen_meals:
            matched_rows = df_library[df_library["Meal Name"] == meal_name]
            if not matched_rows.empty:
                raw_ing = matched_rows.iloc[0]["Ingredients & Aisle Tags"]
                items = [x.strip() for x in str(raw_ing).split(",") if x.strip()]
                for itm in items:
                    if "|" in itm:
                        item_name, aisle = [p.strip() for p in itm.split("|", 1)]
                    else:
                        item_name, aisle = itm, "Pantry"
                    if aisle not in aisle_buckets:
                        aisle_buckets[aisle] = set()
                    aisle_buckets[aisle].add(item_name)

        for aisle, items_set in sorted(aisle_buckets.items()):
            st.markdown(f"#### 🏷️ {aisle}")
            for item in sorted(items_set):
                st.checkbox(f"{item}", key=f"shop_{aisle}_{item}")

# Writeback tab to add new recipes to the Google Sheet
with tab_add:
    st.subheader("➕ Add New Recipe to Library")
    with st.form("new_recipe_form"):
        new_name = st.text_input("Meal Name *", placeholder="e.g. Teriyaki Salmon Bowls")
        new_tags = st.text_input("Categories / Tags", placeholder="e.g. Seafood, Quick, Japanese")
        new_ingredients = st.text_area(
            "Ingredients & Aisle Tags *",
            placeholder="Salmon fillets | Meat & Seafood, Edamame | Frozen Foods, Sushi rice | Pantry",
            help="Format: Item | Aisle, Item | Aisle"
        )
        submitted = st.form_submit_button("Save to Google Sheet", type="primary")

        if submitted:
            if not new_name.strip() or not new_ingredients.strip():
                st.error("Please provide both a Meal Name and Ingredients.")
            else:
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    new_row = pd.DataFrame([{
                        "Meal Name": new_name.strip(),
                        "Category / Tags": new_tags.strip(),
                        "Ingredients & Aisle Tags": new_ingredients.strip(),
                    }])
                    updated_df = pd.concat([df_library, new_row], ignore_index=True)
                    conn.update(worksheet="Meal_Library", data=updated_df)
                    st.success(f"Added '{new_name}' to your Google Sheet!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as write_err:
                    st.error(f"Could not write to Google Sheet: {write_err}")