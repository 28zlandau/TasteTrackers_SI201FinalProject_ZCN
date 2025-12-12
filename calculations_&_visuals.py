import os
import sqlite3
import matplotlib.pyplot as plt
import unittest
from data import DB_NAME, create_database

def get_connection():
   return sqlite3.connect(DB_NAME)


def get_brewery_type_counts():
   conn = get_connection()
   curr = conn.cursor()
   curr.execute("SELECT BreweryTypes.name, COUNT(*) FROM Breweries JOIN BreweryTypes ON Breweries.type_id = BreweryTypes.type_id JOIN BreweryNames ON Breweries.name_id = BreweryNames.name_id GROUP BY BreweryTypes.name ORDER BY COUNT(*) DESC")
   result = curr.fetchall()
   conn.close()
   return result


def get_glass_type_counts():
   conn = get_connection()
   curr = conn.cursor()
   curr.execute("SELECT GlassTypes.name, COUNT(*) FROM Cocktails JOIN GlassTypes ON Cocktails.glass_id = GlassTypes.glass_id GROUP BY GlassTypes.name ORDER BY COUNT(*) DESC")
   result = curr.fetchall()
   conn.close()
   return result 

def get_brewery_counts_by_state(limit=10):
   conn = get_connection()
   curr = conn.cursor()
   curr.execute("SELECT States.name, COUNT(*) FROM Breweries JOIN States ON Breweries.state_id = States.state_id JOIN BreweryNames ON Breweries.name_id = BreweryNames.name_id GROUP BY States.name ORDER BY COUNT(*) DESC LIMIT ?", (limit,))
   result = curr.fetchall()
   conn.close()
   return result

def get_brewery_counts_by_country(limit=10):
   conn = get_connection()
   curr = conn.cursor()
   curr.execute("SELECT Countries.name, COUNT(*) FROM Breweries JOIN Countries ON Breweries.country_id = Countries.country_id JOIN BreweryNames ON Breweries.name_id = BreweryNames.name_id GROUP BY Countries.name ORDER BY COUNT(*) DESC LIMIT ?", (limit,))
   result = curr.fetchall()
   conn.close()
   return result


def write_calculations_to_file(path="results_summary.txt"):
   brewery_types = get_brewery_type_counts()
   glass_types = get_glass_type_counts()
   top_ingredients = get_top_ingredients()
   state_counts = get_brewery_counts_by_state()
   country_counts = get_brewery_counts_by_country()
   summary = get_meal_ingredient_summary()
   lines = []
   lines.append("Brewery Types by Count\n")
   for label, count in brewery_types:
       lines.append(f"  {label}: {count}\n")
   lines.append("\n")
   lines.append("Cocktail Glass Types by Count\n")
   for label, count in glass_types:
       lines.append(f"  {label}: {count}\n")
   lines.append("\n")
   lines.append("Top Ingredients in Meals\n")
   for label, count in top_ingredients:
       lines.append(f"  {label}: {count}\n")
   lines.append("\n")
   lines.append("Top States by Number of Breweries\n")
   for label, count in state_counts:
       lines.append(f"  {label}: {count}\n")
   lines.append("\n")
   lines.append("Top Countries by Number of Breweries\n")
   for label, count in country_counts:
       lines.append(f"  {label}: {count}\n")
   lines.append("\n")
   lines.append("Meal and Ingredient Summary\n")
   lines.append(f"  Total meals: {int(summary['total_meals'])}\n")
   lines.append(f"  Average ingredients per meal: {summary['avg_ingredients_per_meal']:.2f}\n")
   with open(path, "w", encoding="utf-8") as f:
       f.writelines(lines)


def ensure_folder(filepath):
   folder = os.path.dirname(filepath)
   if folder and not os.path.exists(folder):
       os.makedirs(folder)

def plot_brewery_types_pie(out="brewery_distribution.png"):
   data = get_brewery_type_counts()
   if not data: return
   labels, values = zip(*data)
   total = sum(values)
   explode = [0.08 if v == max(values) else 0.02 for v in values]
   fig, ax = plt.subplots(figsize=(8, 8))
   wedges, texts, autotexts = ax.pie(values, labels=None, explode=explode, colors=plt.cm.tab20c(range(len(values))), startangle=90, pctdistance=0.7, autopct=lambda p: f"{p:.1f}%\n({int(round(p * total / 100))})")
   ax.legend(wedges, labels, title="Brewery Types", loc="center left", bbox_to_anchor=(1.05, 0.5))
   ax.set_title("Distribution of Brewery Types", pad=30)
   ax.axis("equal")
   plt.tight_layout()
   fig.savefig(out, bbox_inches="tight")
   plt.close(fig) 

def plot_glass_types_bar(out="glass_types.png"):
   data = get_glass_type_counts()
   if not data:
       return
   data = data[:15]
   labels, counts = zip(*data)
   pos = range(len(labels))
   fig, ax = plt.subplots(figsize=(12, 6))
   colors = plt.cm.Blues([i/len(labels) for i in pos])
   ax.bar(pos, counts, color=colors)
   ax.set_xticks(pos)
   ax.set_xticklabels(labels, rotation=45, ha="right")
   ax.set_xlabel("Glass Type")
   ax.set_ylabel("Number of Cocktails")
   ax.set_title("Top 15 Cocktail Glass Types")
   ax.grid(axis="y", linestyle="--", alpha=0.3)
   for p, c in zip(pos, counts):
       ax.text(p, c + 0.3, str(c), ha="center", fontsize=8)
   ensure_folder(out)
   fig.tight_layout()
   fig.savefig(out, bbox_inches="tight")
   plt.close(fig) 

def run_all_analysis():
    write_calculations_to_file("results_summary.txt")
    plot_brewery_types_pie("brewery_distribution.png")
    plot_glass_types_bar("glass_types.png")
    plot_top_ingredients_scatter("ingredients_top12.png")
    plot_top_states_for_breweries("brewery_states_top10.png")

class TestProject(unittest.TestCase):
    def setUp(self):
        create_database()

    def test_cocktails_at_least_100(self):
        conn = get_connection()
        curr = conn.cursor()
        curr.execute("SELECT COUNT(*) FROM Cocktails")
        cocktail_count = curr.fetchone()[0]
        conn.close()
        self.assertGreaterEqual(cocktail_count, 100)


if __name__ == "__main__":
    create_database()
    unittest.main(exit=False, verbosity=2)
    run_all_analysis()