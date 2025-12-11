def get_glass_type_counts():
   conn = get_connection()
   curr = conn.cursor()
   curr.execute("SELECT GlassTypes.name, COUNT(*) FROM Cocktails JOIN GlassTypes ON Cocktails.glass_id = GlassTypes.glass_id GROUP BY GlassTypes.name ORDER BY COUNT(*) DESC")
   result = curr.fetchall()
   conn.close()
   return result 