def get_glass_type_counts():
   conn = get_connection()
   curr = conn.cursor()
   curr.execute("SELECT GlassTypes.name, COUNT(*) FROM Cocktails JOIN GlassTypes ON Cocktails.glass_id = GlassTypes.glass_id GROUP BY GlassTypes.name ORDER BY COUNT(*) DESC")
   result = curr.fetchall()
   conn.close()
   return result 

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

   