import pandas as pd

# Load combine_pro_day.csv
df_main = pd.read_csv("combine_pro_day.csv")

# Load combine_pro_day_added.csv
# Since it has an extra comma, we can read it and drop the empty column before Wingspan if any
lines = open("combine_pro_day_added.csv").read().splitlines()
cleaned_lines = []
for line in lines:
    parts = line.split(",")
    if len(parts) == 20: 
        # Check where the extra empty column is
        # Usually it's right before Wingspan
        # e.g., parts[18] is Wingspan, parts[19] is id
        # Let's remove parts[17] if it's empty
        if parts[17] == "":
            parts.pop(17)
    elif len(parts) == 19:
        pass
    else:
        print(f"Warning: line has {len(parts)} columns")
    cleaned_lines.append(",".join(parts))

with open("combine_pro_day_added_cleaned.csv", "w") as f:
    f.write("\n".join(cleaned_lines))

df_added = pd.read_csv("combine_pro_day_added_cleaned.csv", header=None)
df_added.columns = df_main.columns

# Now concatenate. If a player exists, we update? Or just append?
# User said "combine_pro_day_added.csv に加えることで"
# Let's drop duplicates based on player and year.
df_combined = pd.concat([df_main, df_added], ignore_index=True)
df_combined = df_combined.drop_duplicates(subset=["Year", "player"], keep="last")
df_combined.to_csv("combine_pro_day.csv", index=False)

print(f"Main rows: {len(df_main)}, Added rows: {len(df_added)}, Combined rows: {len(df_combined)}")

