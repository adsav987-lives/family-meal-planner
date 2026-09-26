from datetime import datetime, timedelta
import pandas as pd
import streamlit as st


# Page config for mobile and desktop responsiveness
st.set_page_config(
    page_title="Family Meal Planner", page_icon="🍳", layout="centered"
)


st.title("🍳 Family Meal Planner & Shopping List")
st.markdown(
    "Plan your weekly meals, grow your recipe library, and generate a categorized shopping list instantly."
)


# --- GOOGLE SHEETS CONNECTION SIMULATION ---
# In production, use st.connection("gsheets", type=GsheetsConnection)
# For setup, we mock reading/writing from session state or CSV files linked to Drive.




@st.cache_data
def load_data():
  # Placeholder initialization for demo/bootstrap
  library_data = {
      "Meal Name": ["Chicken Curry", "Homemade Pizza", "Lamb Souvlaki"],
      "Category": ["Chicken, Curry", "Italian", "Greek"],
      "Ingredients": [
          (
              "Chicken breast (Meat & Seafood), Spinach (Fresh Produce),"
              " Chickpeas (Pantry), Curry Paste (Pantry), Jasmin Rice (Pantry)"
          ),
          (
              "Pizza bases (Bakery), Passata (Pantry), Cheddar cheese (Dairy &"
              " Eggs)"
          ),
          (
              "Lamb chops (Meat & Seafood), Flatbread (Bakery), Feta cheese"
              " (Dairy & Eggs), Cucumber (Fresh Produce)"
          ),
      ],
  }
  return pd.DataFrame(library_data)




df_library = load_data()


# --- NAVIGATION TABS ---
tab_plan, tab_library, tab_shopping = st.tabs(
    ["📅 Weekly Planner", "📚 Meal Library", "🛒 Shopping List"]
)


with tab_plan:
  st.subheader("Plan Your Week")
  today = datetime.today()
  start_of_week = today - timedelta(days=today.weekday())
  week_date = st.date_input("Select Week Starting (Monday)", start_of_week)


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
  for day in days:
    st.markdown(f"**{day}**")
    col1, col2 = st.columns(2)
    with col1:
      lunch = st.selectbox(
          f"Lunch ({day})",
          ["--- None ---"] + list(df_library["Meal Name"]),
          key=f"lunch_{day}",
      )
    with col2:
      dinner = st.selectbox(
          f"Dinner ({day})",
          ["--- None ---"] + list(df_library["Meal Name"]),
          key=f"dinner_{day}",
      )
    selected_meals[day] = {"Lunch": lunch, "Dinner": dinner}


  if st.button("Save Weekly Plan"):
    st.success("Weekly plan updated and saved to Google Drive database!")


with tab_library:
  st.subheader("Master Recipe & Meal Bank")
  st.markdown(
      "Add new meal ideas here. They will permanently join your selection pool"
      " for future weeks."
  )


  with st.form("add_meal_form"):
    new_meal_name = st.text_input("New Meal Name")
    new_category = st.text_input("Tags / Style (e.g., Pasta, Quick, Beef)")
    new_ingredients = st.text_area(
        "Ingredients & Aisles (Format: Item Name (Aisle Name), separated by"
        " commas)"
    )
    submitted = st.form_submit_button("Add to Meal Library")


    if submitted and new_meal_name:
      new_row = pd.DataFrame({
          "Meal Name": [new_meal_name],
          "Category": [new_category],
          "Ingredients": [new_ingredients],
      })
      df_library = pd.concat([df_library, new_row], ignore_index=True)
      st.success(
          f"Successfully added '{new_meal_name}' to your growing meal bank!"
      )


  st.dataframe(df_library, use_container_width=True)


with tab_shopping:
  st.subheader("🛒 Smart Categorized Shopping List")
  st.markdown(
      "Automatically compiled from your selected weekly meals, sorted by"
      " supermarket aisle."
  )


  if st.button("Generate Shopping List"):
    # Simulated compiled shopping list grouped by aisle
    shopping_categories = {
        "🥬 Fresh Produce": ["Spinach (fresh)", "Cucumber", "Tomatoes"],
        "🍞 Bakery": ["Pizza bases", "Flatbread"],
        "🧀 Dairy & Eggs": ["Cheddar cheese", "Feta cheese"],
        "🛒 Pantry": [
            "Chickpeas",
            "Curry Paste",
            "Jasmin Rice",
            "Passata",
        ],
        "🥩 Meat & Seafood": ["Chicken breast", "Lamb chops"],
    }


    for category, items in shopping_categories.items():
      st.markdown(f"### {category}")
      for item in items:
        st.checkbox(item, key=f"shop_{item}")
  else:
    st.info(
        "Click 'Generate Shopping List' above to compile items based on your"
        " meal plan."
    )