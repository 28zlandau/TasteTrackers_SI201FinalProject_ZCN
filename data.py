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

   