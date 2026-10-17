from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# Page config for mobile and desktop responsiveness
st.set_page_config(
    page_title="Family Meal Planner",
    page_icon="🍳",
    layout="wide"
)

st.title("🍳 Family Meal Planner & Shopping List")
st.markdown("Plan your weekly meals, grow your recipe library, and generate a categorized shopping list instantly.")

# ==============================================================================
# 1. LOCAL DEVELOPMENT TOGGLE
# ==============================================================================
# Set to True if you want to bypass Google Sign-In while developing locally in VS Code!
# Set to False once you've saved your redirect URIs in Google Cloud Console or deploy to Streamlit Cloud.
BYPASS_AUTH_LOCAL = False

# ==============================================================================
# 2. GOOGLE OIDC AUTHENTICATION
# ==============================================================================
auth_settings = st.secrets.get("auth")
required_auth_settings = (
    "redirect_uri",
    "cookie_secret",
    "client_id",
    "client_secret",
    "server_metadata_url",
)

missing_auth_settings = [
    setting
    for setting in required_auth_settings
    if auth_settings is None or setting not in auth_settings
]

if missing_auth_settings and not BYPASS_AUTH_LOCAL:
    st.error(
        f"⚠️ Google sign-in is not fully configured. Missing in secrets.toml: "
        f"{', '.join(missing_auth_settings)}."
    )
    st.info("💡 Tip: You can set `BYPASS_AUTH_LOCAL = True` at the top of app.py to work offline in VS Code.")
    st.stop()

if not BYPASS_AUTH_LOCAL:
    if not st.user.is_logged_in:
        st.markdown("### Please Sign In")
        st.caption("Sign in with your family Google account to manage your meal plan.")
        if st.button("🔑 Login with Google", type="primary"):
            st.login()
        st.stop()

    # --- EMAIL ALLOWLIST (Only these family members can access) ---
    ALLOWED_FAMILY_MEMBERS = [
        "adsav987@gmail.com",
        "partner_email@gmail.com",
        "family_member@gmail.com",
    ]

    user_email = st.user.get("email")
    if user_email not in ALLOWED_FAMILY_MEMBERS:
        st.error(
            f"⛔ Access denied for {user_email}. "
            "Only approved family members can access this planner."
        )
        st.stop()

    user_name = st.user.get("name") or st.user.get("email") or "Family Member"
else:
    user_name = "Local Developer (Offline Mode)"

# ==============================================================================
# 3. GOOGLE SHEETS LIVE DATA CONNECTION (WITH FALLBACK)
# ==============================================================================
@st.cache_data(ttl=60)
def load_data_from_sheet():
    try:
        conn = st.connection("gsheets", type="gsheets")
        df = conn.read(worksheet="Meal_Library", usecols=[0, 1, 2], ttl=5)
        df = df.dropna(subset=["Meal Name"])
        return df
    except Exception as e:
        if "df_library" not in st.session_state:
            st.session_state.df_library = pd.DataFrame({
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
        return st.session_state.df_library

df_library = load_data_from_sheet()

# Sidebar
with st.sidebar:
    st.subheader(f"👤 {user_name}")
    if not BYPASS_AUTH_LOCAL:
        if st.button("Logout"):
            st.logout()
    st.divider()
    st.subheader("Database Sync")
    if st.button("🔄 Reload from Google Sheet"):
        st.cache_data.clear()
        df_library = load_data_from_sheet()
        st.success("Refreshed successfully!")
        st.rerun()

# ==============================================================================
# 4. NAVIGATION TABS
# ==============================================================================
tab_plan, tab_library, tab_shopping = st.tabs(
    ["📅 Weekly Planner", "📚 Meal Library", "🛒 Shopping List"]
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
    st.markdown("Meals loaded directly from your Google Sheet master library database.")
    st.dataframe(df_library, use_container_width=True)

with tab_shopping:
    st.subheader("🛒 Smart Categorized Shopping List")
    st.markdown("Automatically compiled from your selected weekly meals, sorted by supermarket aisle.")

    # Aggregate selected meals
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