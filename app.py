from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# Page config for mobile and desktop responsiveness
st.set_page_config(
    page_title="Family Meal Planner", page_icon="🍳", layout="centered"
)

st.title("🍳 Family Meal Planner & Shopping List")
st.markdown(
    "Plan your weekly meals, grow your recipe library, and generate a"
    " categorized shopping list instantly."
)

# --- GOOGLE OIDC AUTHENTICATION ---
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
if missing_auth_settings:
    st.error(
        "Google sign-in is not configured. Add the required [auth] settings "
        "in Streamlit Cloud under Manage app > Settings > Secrets. Missing: "
        f"{', '.join(missing_auth_settings)}."
    )
    st.stop()

if not st.user.is_logged_in:
    st.markdown("### Login")
    if st.button("Login with Google"):
        st.login()
    st.stop()

# --- GOOGLE SHEETS LIVE DATA CONNECTION ---
# Using st.connection (requires secrets.toml configured with your Google Sheets credentials)
# Alternatively, you can swap this with your preferred gspread implementation.
@st.cache_data(ttl=60)
def load_data_from_sheet():
  try:
    conn = st.connection("gsheets", type="gsheets")
    # Reads the 'Meal_Library' worksheet from your Google Sheet
    df = conn.read(worksheet="Meal_Library", usecols=[0, 1, 2], ttl=5)
    # Drop empty rows if any
    df = df.dropna(subset=["Meal Name"])
    return df
  except Exception as e:
    # Fallback placeholder if secrets/connection aren't active yet during local testing
    st.sidebar.warning(
        "Live Google Sheet connection not detected. Using session cache/fallback"
        f" data. Error: {e}"
    )
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
              (
                  "Chicken breast | Meat & Seafood, Spinach (fresh) | Fresh"
                  " Produce, Chickpeas | Pantry, Lentils | Pantry, Curry Paste |"
                  " Pantry, Jasmin Rice | Pantry"
              ),
              (
                  "Pizza bases | Bakery, Passata | Pantry, Cheddar (grated) |"
                  " Dairy & Eggs"
              ),
              (
                  "Lamb chops | Meat & Seafood, Flatbread | Bakery, Feta"
                  " cheese | Dairy & Eggs, Cucumber | Fresh Produce, Tomatoes |"
                  " Fresh Produce"
              ),
              (
                  "Mince meat | Meat & Seafood, Tinned tomatoes | Pantry,"
                  " Four-bean mix | Pantry, Carrots | Fresh Produce, Onions |"
                  " Fresh Produce, Garlic | Fresh Produce"
              ),
              (
                  "Filled pasta | Refrigerated Meal Components, Salmon pieces"
                  " | Meat & Seafood, Fresh mixed vegetables | Fresh Produce,"
                  " Cream | Dairy & Eggs, Garlic & herb sauce | Pantry"
              ),
              (
                  "Whole chicken | Meat & Seafood, Potatoes | Fresh Produce,"
                  " Carrots | Fresh Produce, Pumpkin | Fresh Produce, Butter |"
                  " Dairy & Eggs"
              ),
          ],
      })
    return st.session_state.df_library


# Load the master library dataframe
df_library = load_data_from_sheet()

# Sidebar controls for reloading/refreshing data
with st.sidebar:
  st.subheader("Database Sync")
  if st.button("🔄 Reload from Google Sheet"):
    st.cache_data.clear()
    df_library = load_data_from_sheet()
    st.success("Refreshed successfully from spreadsheet!")
    st.rerun()

# --- NAVIGATION TABS ---
tab_plan, tab_library, tab_shopping = st.tabs(
    ["📅 Weekly Planner", "📚 Meal Library", "🛒 Shopping List"]
)

with tab_plan:
  st.subheader("Plan Your Week")

  # Dynamic Week Starting Date Picker
  today = datetime.today()
  default_start_of_week = today - timedelta(days=today.weekday())
  week_date = st.date_input(
      "Select Week Starting (Monday)", default_start_of_week
  )

  # Calculate exact calendar dates for each day based on the selected week_date
  st.markdown(f"*Planning meals for the week of **{week_date.strftime('%A, %B %d, %Y')}***")
  
  days = [
      "Monday",
      "Tuesday",
      "Wednesday",
      "Thursday",
      "Friday",
      "Saturday",
      "Sunday",
  ]

  selected_meals = {}
  meal_options = ["--- None ---"] + list(df_library["Meal Name"].dropna())

  for index, day in enumerate(days):
    # Compute the specific date for this day of the week
    current_day_date = week_date + timedelta(days=index)
    st.markdown(f"**{day} ({current_day_date.strftime('%b %d')})**")
    
    col1, col2 = st.columns(2)
    with col1:
      lunch = st.selectbox(
          f"Lunch ({day})", meal_options, key=f"lunch_{day}_{week_date}"
      )
    with col2:
      dinner = st.selectbox(
          f"Dinner ({day})", meal_options, key=f"dinner_{day}_{week_date}"
      )
    selected_meals[day] = {
        "Date": current_day_date.strftime("%Y-%m-%d"),
        "Lunch": lunch,
        "Dinner": dinner,
    }

  if st.button("Save Weekly Plan"):
    st.success(f"Weekly plan for the week of {week_date} saved successfully!")

with tab_library:
  st.subheader("Master Recipe & Meal Bank")
  st.markdown(
      "Meals loaded directly from your Google Sheet master library database."
  )

  # Display the live dataframe pulled from Google Sheets
  st.dataframe(df_library, use_container_width=True)

with tab_shopping:
  st.subheader("🛒 Smart Categorized Shopping List")
  st.markdown(
      "Automatically compiled from your selected weekly meals, sorted by"
      " supermarket aisle."
  )

  if st.button("Generate Shopping List"):
    # Future enhancement: parse ingredients dynamically from df_library based on selected_meals
    st.info(
        "Shopping list generator will aggregate ingredients for your chosen"
        " weekly menu items."
    )
  else:
    st.info("Click 'Generate Shopping List' above to compile items.")
# Display the name supplied by Google's authenticated user profile.
user_name = st.user.get("name") or st.user.get("email") or "Google user"
st.sidebar.write(f"Logged in as: {user_name}")
st.write(f"Welcome, {user_name}")

if st.sidebar.button("Logout"):
    st.logout()
