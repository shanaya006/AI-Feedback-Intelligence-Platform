"""
Step 3: Build SQLite Database
Loads reviews_enriched.csv into a proper SQL database (reviews.db)
with a `reviews` table you can query.

SETUP: just needs pandas (already installed if you ran the extraction script)

Run: python3 build_database.py
"""

import pandas as pd
import sqlite3

INPUT_FILE = "reviews_enriched.csv"
DB_FILE = "reviews.db"
TABLE_NAME = "reviews"

def main():
    # 1. Load your enriched CSV
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} rows from {INPUT_FILE}")
    print(f"Columns: {list(df.columns)}\n")

    # 2. Connect to (or create) the SQLite database file
    conn = sqlite3.connect(DB_FILE)

    # 3. Write the dataframe into a SQL table
    # if_exists="replace" means re-running this script rebuilds the table fresh
    # from the current CSV — safe to run again anytime you update the CSV.
    df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)

    # 4. Quick sanity check: count rows and preview
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    count = cursor.fetchone()[0]
    print(f"'{TABLE_NAME}' table created in {DB_FILE} with {count} rows.\n")

    cursor.execute(f"SELECT review_id, topic, sentiment, churn_risk FROM {TABLE_NAME} LIMIT 5")
    print("Preview (first 5 rows):")
    for row in cursor.fetchall():
        print(" ", row)

    conn.close()
    print(f"\nDone. You can now query {DB_FILE} using SQL.")

if __name__ == "__main__":
    main()