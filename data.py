import sqlite3
import requests

DB_NAME = "taste_trackers.db"
MEALDB_API = "https://www.themealdb.com/api/json/v1/1/"
COCKTAILDB_API = "https://www.thecocktaildb.com/api/json/v1/1/"
BREWERY_API = "https://api.openbrewerydb.org/v1/breweries"

def get_connection():
   return sqlite3.connect(DB_NAME)

def normalize_string(value):
   if value is None:
       return ""
   cleaned = value.strip()
   if not cleaned:
       return ""
   return " ".join(cleaned.split()).title()

def create_database():
   conn = get_connection()
   curr = conn.cursor()
   curr.execute("CREATE TABLE IF NOT EXISTS Ingredients (ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
   curr.execute("CREATE TABLE IF NOT EXISTS MealCategories (category_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
   curr.execute("CREATE TABLE IF NOT EXISTS MealAreas (area_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
   curr.execute("CREATE TABLE IF NOT EXISTS Meals (meal_id INTEGER PRIMARY KEY, name TEXT, category_id INTEGER, area_id INTEGER, instructions TEXT, UNIQUE(name, category_id, area_id, instructions))")
   curr.execute("CREATE TABLE IF NOT EXISTS MealIngredients (id INTEGER PRIMARY KEY AUTOINCREMENT, meal_id INTEGER, ingredient_id INTEGER, UNIQUE(meal_id, ingredient_id))")
   curr.execute("CREATE TABLE IF NOT EXISTS CocktailCategories (category_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
   curr.execute("CREATE TABLE IF NOT EXISTS GlassTypes (glass_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
   curr.execute("CREATE TABLE IF NOT EXISTS Cocktails (cocktail_id INTEGER PRIMARY KEY, name TEXT, category_id INTEGER, glass_id INTEGER, UNIQUE(name, category_id, glass_id))")
   curr.execute("CREATE TABLE IF NOT EXISTS BreweryNames (name_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
   curr.execute("CREATE TABLE IF NOT EXISTS BreweryTypes (type_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
   curr.execute("CREATE TABLE IF NOT EXISTS Cities (city_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
   curr.execute("CREATE TABLE IF NOT EXISTS States (state_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
   curr.execute("CREATE TABLE IF NOT EXISTS Countries (country_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
   curr.execute("CREATE TABLE IF NOT EXISTS Breweries (brewery_id INTEGER PRIMARY KEY AUTOINCREMENT, api_id TEXT UNIQUE, name_id INTEGER, type_id INTEGER, city_id INTEGER, state_id INTEGER, country_id INTEGER, UNIQUE(name_id, type_id, city_id, state_id, country_id))")
   curr.execute("CREATE TABLE IF NOT EXISTS RunState (api_name TEXT PRIMARY KEY, last_offset INTEGER)")
   conn.commit()
   conn.close()

def fetch_json(url, params=None):
   response = requests.get(url, params=params, timeout=15)
   response.raise_for_status()
   return response.json()

def enforce_api_limit(curr, table_name, limit=150):
   curr.execute(f"SELECT COUNT(*) FROM {table_name}")
   count = curr.fetchone()[0]
   if count >= limit:
       print("All data uploaded to DB")
       return False
   return limit - count

def get_offset(curr, api_name):
   curr.execute("SELECT last_offset FROM RunState WHERE api_name=?", (api_name,))
   row = curr.fetchone()
   return row[0] if row else 0

def set_offset(curr, api_name, value):
   curr.execute("INSERT OR REPLACE INTO RunState (api_name, last_offset) VALUES (?, ?)", (api_name, value))

def get_or_create_lookup(curr, table_name, id_column, name_column, raw_value, default="Unknown"):
   cleaned_value = normalize_string(raw_value) or default
   curr.execute(f"INSERT OR IGNORE INTO {table_name} ({name_column}) VALUES (?)", (cleaned_value,))
   curr.execute(f"SELECT {id_column} FROM {table_name} WHERE {name_column} = ?", (cleaned_value,))
   row = curr.fetchone()
   return int(row[0]) if row else None 

def get_or_create_ingredient(curr, raw_value):
   cleaned_name = normalize_string(raw_value)
   if not cleaned_name:
       return None
   curr.execute("INSERT OR IGNORE INTO Ingredients (name) VALUES (?)", (cleaned_name,))
   curr.execute("SELECT ingredient_id FROM Ingredients WHERE name = ?", (cleaned_name,))
   row = curr.fetchone()
   return int(row[0]) if row else None

def get_or_create_brewery_name(curr, raw_value):
   cleaned = normalize_string(raw_value)
   curr.execute("INSERT OR IGNORE INTO BreweryNames (name) VALUES (?)", (cleaned,))
   curr.execute("SELECT name_id FROM BreweryNames WHERE name = ?", (cleaned,))
   row = curr.fetchone()
   return int(row[0]) if row else None

def load_meals(limit=25):
   create_database()
   conn = get_connection()
   curr = conn.cursor()


   remaining_allowed = enforce_api_limit(curr, "Meals", 150)
   if remaining_allowed is False:
       conn.close()
       return
   limit = min(limit, remaining_allowed)


   letters = "abcdefghijklmnopqrstuvwxyz"
   offset = get_offset(curr, "meals")
   added_meals = 0


   for index in range(offset, len(letters)):
       if added_meals >= limit:
           break
       letter = letters[index]
       data = fetch_json(MEALDB_API + "search.php", {"f": letter})
       for meal in (data.get("meals") or []):
           if added_meals >= limit:
               break
           meal_id_text = meal.get("idMeal")
           if not meal_id_text:
               continue
           try:
               meal_id = int(meal_id_text)
           except:
               continue
           meal_name = normalize_string(meal.get("strMeal"))
           category_id = get_or_create_lookup(curr, "MealCategories", "category_id", "name", meal.get("strCategory"))
           area_id = get_or_create_lookup(curr, "MealAreas", "area_id", "name", meal.get("strArea"))
           instructions = (meal.get("strInstructions") or "").strip()
           curr.execute("INSERT OR IGNORE INTO Meals (meal_id, name, category_id, area_id, instructions) VALUES (?, ?, ?, ?, ?)", (meal_id, meal_name, category_id, area_id, instructions))
           curr.execute("SELECT 1 FROM Meals WHERE meal_id=?", (meal_id,))
           if not curr.fetchone():
               continue
           for ingredient_index in range(1, 21):
               ingredient_name = meal.get(f"strIngredient{ingredient_index}")
               if ingredient_name:
                   ingredient_id = get_or_create_ingredient(curr, ingredient_name)
                   if ingredient_id:
                       curr.execute("INSERT OR IGNORE INTO MealIngredients (meal_id, ingredient_id) VALUES (?, ?)", (meal_id, ingredient_id))
           added_meals += 1
       offset = index + 1


   set_offset(curr, "meals", offset)
   conn.commit()
   conn.close()

def load_cocktails(limit=25):
   create_database()
   conn = get_connection()
   curr = conn.cursor()

   remaining_allowed = enforce_api_limit(curr, "Cocktails", 150)
   if remaining_allowed is False:
       conn.close()
       return
   limit = min(limit, remaining_allowed)

   letters = "abcdefghijklmnopqrstuvwxyz"
   offset = get_offset(curr, "cocktails")
   added_cocktails = 0

   for index in range(offset, len(letters)):
       if added_cocktails >= limit:
           break
       letter = letters[index]
       data = fetch_json(COCKTAILDB_API + "search.php", {"f": letter})
       for cocktail_record in (data.get("drinks") or []):
           if added_cocktails >= limit:
               break
           cocktail_id_text = cocktail_record.get("idDrink")
           if not cocktail_id_text:
               continue
           try:
               cocktail_id = int(cocktail_id_text)
           except:
               continue
           cocktail_name = normalize_string(cocktail_record.get("strDrink"))
           category_id = get_or_create_lookup(curr, "CocktailCategories", "category_id", "name", cocktail_record.get("strCategory"))
           glass_id = get_or_create_lookup(curr, "GlassTypes", "glass_id", "name", cocktail_record.get("strGlass"))
           curr.execute("INSERT OR IGNORE INTO Cocktails (cocktail_id, name, category_id, glass_id) VALUES (?, ?, ?, ?)", (cocktail_id, cocktail_name, category_id, glass_id))
           curr.execute("SELECT 1 FROM Cocktails WHERE cocktail_id=?", (cocktail_id,))
           if curr.fetchone():
               added_cocktails += 1
       offset = index + 1


   set_offset(curr, "cocktails", offset)
   conn.commit()
   conn.close() 
def load_breweries(limit=25):
   create_database()
   conn = get_connection()
   curr = conn.cursor()


   remaining_allowed = enforce_api_limit(curr, "Breweries", 150)
   if remaining_allowed is False:
       conn.close()
       return
   limit = min(limit, remaining_allowed)


   page_number = get_offset(curr, "breweries") or 1
   added = 0


   while added < limit:
       data = fetch_json(BREWERY_API, {"per_page": 50, "page": page_number})
       if not data:
           break
       for brewery_record in data:
           if added >= limit:
               break
           api_id = brewery_record.get("id")
           if not api_id:
               continue
           name_id = get_or_create_brewery_name(curr, brewery_record.get("name"))
           type_id = get_or_create_lookup(curr, "BreweryTypes", "type_id", "name", brewery_record.get("brewery_type"))
           city_id = get_or_create_lookup(curr, "Cities", "city_id", "name", brewery_record.get("city"))
           state_id = get_or_create_lookup(curr, "States", "state_id", "name", brewery_record.get("state"))
           country_id = get_or_create_lookup(curr, "Countries", "country_id", "name", brewery_record.get("country"))
           curr.execute("INSERT OR IGNORE INTO Breweries (api_id, name_id, type_id, city_id, state_id, country_id) VALUES (?, ?, ?, ?, ?, ?)", (api_id, name_id, type_id, city_id, state_id, country_id))
           curr.execute("SELECT 1 FROM Breweries WHERE api_id=?", (api_id,))
           if curr.fetchone():
               added += 1
       page_number += 1


   set_offset(curr, "breweries", page_number)
   conn.commit()
   conn.close()

def main():
   create_database()
   load_meals()
   load_cocktails()
   load_breweries()

if __name__ == "__main__":
   main()

   