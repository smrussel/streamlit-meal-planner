import streamlit as st
import requests
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize Session State
session_state = st.session_state

if 'selected_labels' not in session_state:
    session_state.selected_labels = []

# Edamam API credentials
APP_ID = os.getenv("EDAMAM_API_ID")
APP_KEY = os.getenv("EDAMAM_API_KEY")

# Edamam api endpoint URL
API_BASE_URL = 'https://api.edamam.com/api/recipes/v2'

def mifflin_st_jeor(weight, height, age, gender):
    """
    Calculate Basal Metabolic Rate (BMR) using Mifflin-St Jeor Equation.

    Args:
    weight (float): Weight in kilograms.
    height (float): Height in centimeters.
    age (int): Age in years.
    gender (str): 'male' or 'female'.

    Returns:
    float: Basal Metabolic Rate (BMR) in calories per day.
    """
    if gender.lower() == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    elif gender.lower() == 'female':
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        raise ValueError("Invalid gender. Gender must be 'male' or 'female'.")
    return bmr

def calorie_calculator(weight, height, age, gender, activity_level):
    """
    Calculate daily calorie needs based on Basal Metabolic Rate (BMR) and activity level.

    Args:
    weight (float): Weight in kilograms.
    height (float): Height in centimeters.
    age (int): Age in years.
    gender (str): 'male' or 'female'.
    activity_level (float): Activity level factor (1.2 for sedentary, 1.375 for lightly active,
                            1.55 for moderately active, 1.725 for very active, 1.9 for extra active).

    Returns:
    float: Daily calorie needs in calories per day.
    """
    bmr = mifflin_st_jeor(weight, height, age, gender)
    calorie_needs = bmr * activity_level
    return calorie_needs

def get_activity_value(activity):
    if activity == 'Basal Metabolic Rate (BMR)':
        return 1
    elif activity == 'Sedentary: little or no exercise':
        return 1.2
    elif activity == 'Light: exercise 1-3 times/week':
        return 1.375
    elif activity == 'Moderate: exercise 4-5 times/week':
        return 1.465
    elif activity == 'Active: daily exercise or intense exercise 3-4 times/week':
        return 1.55
    elif activity == 'Very Active: intense exercise 6-7 times/week':
        return 1.725
    elif activity == 'Extra Active: very intense exercise daily, or physical job':
        return 1.9

def get_user_action_value(value):
    if value == 'Maintain Weight':
        return 1
    elif value == 'Loose Weight':
        return 0.79
    elif value == 'Gain Weight':
        return 1.11

def get_meal_count_value(value):
    if value == 'Lunch, Dinner':
        return 2
    elif value == 'Breakfast, Lunch, Dinner':
        return 3


def get_recipe_from_api(preferred_cal=827, meal_type='Breakfast', session_state=None):

    total_calories = 0
    recipes = []
    max_allowed_overage = 50  # Adjust as needed
    
    # Parameters for the API request
    params = {
        'type': 'public',
        'diet':'high-protein',
        'random':'true',
        'app_id': APP_ID,
        'app_key': APP_KEY,
        'mealType': meal_type,
        'dishType': 'Main course',
    }
    
    selected_urls =  session_state.selected_labels

    response = requests.get(API_BASE_URL, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        # Iterate through the hits to find recipes
        for hit in data.get('hits', []):
            recipe = hit.get('recipe', {})
            # Check if recipe label is not in selected labels list
            if recipe['label'] not in selected_urls:
                
                # Calculate the remaining calorie range needed to reach the preferred calorie count
                remaining_calories_needed = preferred_cal - total_calories
                # Check if adding the current recipe's calorie count would exceed the preferred calorie count
                if recipe.get('calories', 0) <= remaining_calories_needed + max_allowed_overage:
                    # Add the recipe's calorie count to the total
                    total_calories += recipe.get('calories', 0)
                    # Add the recipe to the list of recipes
                    selected_urls.append(recipe['label'])# Add label to selected labels list
                    recipes.append(recipe)
                    # If total calories exceed preferred calorie count, break the loop
                    if total_calories >= preferred_cal:
                        break
    else:
        st.error("Failed to retrieve recipes. Status code:", response.status_code)
    session_state.selected_labels = session_state.selected_labels +selected_urls
    return recipes, total_calories



def display_recipe(provided_meals):
    fat_total, carbs_total, protein_total = 0.0, 0.0, 0.0
    for lunch_meal in provided_meals:
        st.write("Recipe Title:", lunch_meal['label'])
        
        st.subheader("Recipe Details")
        st.markdown(f"**Title:** {lunch_meal['label']}")
        st.markdown(f"**URL:** [{lunch_meal['label']}]({lunch_meal['url']})")
        st.markdown(f"**Calories:** {round(lunch_meal['calories'])}")
        st.subheader("Ingredients")
        for ingredient in lunch_meal['ingredientLines']:
            st.write("- " + ingredient)

        st.subheader("Nutrition Information")
        for digest in lunch_meal['digest']:
            if digest['label'] == 'Fat':
                fat_total += digest['total']
            elif digest['label'] == 'Carbs':
                carbs_total += digest['total']
            elif digest['label'] == 'Protein':
                protein_total += digest['total']
            if digest['label'] in ['Fat', 'Carbs', 'Protein']:
                st.write(f"- {digest['label']}: {round(digest['total'])} {digest['unit']}")  
    if len(provided_meals) >0:
        fig, ax = plt.subplots()
        labels = ['Fat', 'Carbs', 'Protein']
        values = [fat_total, carbs_total, protein_total]
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        st.pyplot(fig)

def validate_inputs(age, weight, height):
    # Add your validation logic here
    if age is None or age < 0 or age > 120:
        st.error("Invalid input. Please enter valid values for age is between 0-120.")
        return False
    if weight is None or weight < 0 or weight > 650:
        st.error("Invalid input. Please enter valid values for weight is between 0-650.")
        return False
    if height is None or height < 0 or height > 280:
        st.error("Invalid input. Please enter valid values for height is between 0-280.")
        return False
    return True


st.title("Calorie Calculator")

st.write("### Input Data")

age = st.number_input('Age',value=25,step=1)
weight = st.number_input('Weight (kg)',value=65,step=1)
height = st.number_input('Height (cm)',value=180,step=1)

gender = st.selectbox(
    'Gender',
    ('Male', 'Female'))

activity = st.selectbox(
    'Activity',
    (
        'Basal Metabolic Rate (BMR)', 
        'Sedentary: little or no exercise',
        'Light: exercise 1-3 times/week',
        'Moderate: exercise 4-5 times/week',
        'Active: daily exercise or intense exercise 3-4 times/week',
        'Very Active: intense exercise 6-7 times/week',
        'Extra Active: very intense exercise daily, or physical job'
    ))



activity_level = get_activity_value(activity)
calorie_needs = calorie_calculator(weight, height, age, gender, activity_level)
calorie_needs = round(calorie_needs)
st.write(f"### Calorie needed: {calorie_needs}")


user_action_selected = st.selectbox(
'What do you want to do?',
(
    'Maintain Weight', 
    'Loose Weight',
    'Gain Weight',
))

user_action_value = get_user_action_value(user_action_selected)
calorie_required = round(calorie_needs * user_action_value)

meal_count_choice = st.selectbox(
'Meal?',
(
    'Lunch, Dinner', 
    'Breakfast, Lunch, Dinner',
))

meal_count = get_meal_count_value(meal_count_choice)

st.write(f"### Calorie required: {calorie_required}")
per_meal_calorie = calorie_required / meal_count

is_valid = validate_inputs(age, weight, height)

if st.button("Generate Meal Plan") and is_valid:
    if 'selected_labels' in session_state:
        session_state.selected_labels = []
    for i in range(7):
        st.write("# Meal Plan")
        st.write(f"## Day: {i+1}")
        if meal_count == 2:
            st.write("### Lunch")
            lunch_meals,lunch_calories = get_recipe_from_api(preferred_cal=per_meal_calorie,meal_type='Lunch',session_state=session_state)
            display_recipe(lunch_meals)
            st.write("### Dinner")
            dinner_meals,dinner_calories = get_recipe_from_api(preferred_cal=per_meal_calorie,meal_type='Dinner',session_state=session_state)
            display_recipe(dinner_meals)
            st.write("# total calories:",round(lunch_calories+dinner_calories))
        if meal_count == 3:
            st.write("### Breakfast")
            breakfast_meals,breakfast_calories = get_recipe_from_api(preferred_cal=per_meal_calorie,meal_type='Breakfast',session_state=session_state)
            display_recipe(breakfast_meals)
            st.write("### Lunch")
            lunch_meals,lunch_calories = get_recipe_from_api(preferred_cal=per_meal_calorie,meal_type='Lunch',session_state=session_state)
            display_recipe(lunch_meals)
            st.write("### Dinner")
            dinner_meals,dinner_calories = get_recipe_from_api(preferred_cal=per_meal_calorie,meal_type='Dinner',session_state=session_state)
            display_recipe(dinner_meals)
            st.write("# total calories:",round(breakfast_calories+lunch_calories+dinner_calories))

