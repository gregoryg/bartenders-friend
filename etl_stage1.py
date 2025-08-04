#!/usr/bin/env python3
"""
Enhanced Stage 1 ETL: Load raw data with proper ingredient cross-reference
"""
import pandas as pd
from sqlalchemy import create_engine, text
import sys
from pathlib import Path

# Database configuration
DB_URI = 'postgresql://localhost/bartenders_friend'

def load_boston_cocktails(engine, file_path):
    """Load boston_cocktails.csv - already loaded, but include for completeness"""
    print(f"Boston cocktails already loaded from previous run")

def load_all_drinks_to_xref(engine, file_path):
    """Load all_drinks.csv data into cocktail_ingredients cross-reference table"""
    print(f"Loading {file_path} into cocktail_ingredients cross-reference...")

    df = pd.read_csv(file_path)

    # Prepare cross-reference data
    xref_data = []

    for _, row in df.iterrows():
        cocktail_name = row['strDrink']

        # Process ingredients 1-15
        for i in range(1, 16):
            ingredient_col = f'strIngredient{i}'
            measure_col = f'strMeasure{i}'

            if pd.notna(row.get(ingredient_col)) and row.get(ingredient_col).strip():
                ingredient = row[ingredient_col].strip()
                measure = row.get(measure_col, '').strip() if pd.notna(row.get(measure_col)) else ''

                xref_data.append({
                    'cocktail_name': cocktail_name,
                    'ingredient_name': ingredient,
                    'quantity': measure,
                    'ingredient_order': i,
                    'source_dataset': 'all_drinks'
                })

    # Convert to DataFrame and load
    if xref_data:
        xref_df = pd.DataFrame(xref_data)
        xref_df.to_sql('cocktail_ingredients', engine, if_exists='append', index=False)
        print(f"  Loaded {len(xref_data)} ingredient relationships from all_drinks")

    return len(xref_data)

def show_summary(engine):
    """Show summary of loaded data"""
    print("\n=== Data Summary ===")

    # Cocktails summary
    result = engine.execute(text("""
        SELECT
            COUNT(*) as total_cocktails,
            COUNT(instructions) as with_instructions,
            COUNT(*) - COUNT(instructions) as without_instructions
        FROM cocktails
    """))
    cocktails_stats = result.fetchone()
    print(f"Cocktails: {cocktails_stats[0]} total ({cocktails_stats[1]} with instructions, {cocktails_stats[2]} without)")

    # Ingredients summary
    result = engine.execute(text("SELECT COUNT(*) FROM ingredients"))
    ingredients_count = result.fetchone()[0]
    print(f"Unique ingredients: {ingredients_count}")

    # Cross-reference summary
    result = engine.execute(text("""
        SELECT
            source_dataset,
            COUNT(*) as relationships,
            COUNT(DISTINCT cocktail_name) as cocktails,
            COUNT(DISTINCT ingredient_name) as ingredients
        FROM cocktail_ingredients
        GROUP BY source_dataset
        ORDER BY source_dataset
    """))

    print("\nIngredient relationships by source:")
    for row in result:
        print(f"  {row[0]}: {row[1]} relationships ({row[2]} cocktails, {row[3]} ingredients)")

def main():
    print("=== Enhanced Stage 1 ETL: Cross-Reference Loading ===")

    engine = create_engine(DB_URI)

    # Load all_drinks data into cross-reference table
    all_drinks_path = "/home/gregj/projects/coding/bartenders-friend/raw-data/all_drinks.csv"
    relationships_loaded = load_all_drinks_to_xref(engine, all_drinks_path)

    # Show final summary
    show_summary(engine)

    print("\n=== Stage 1 ETL Complete ===")
    print("Next steps:")
    print("1. Review ingredient relationship quality")
    print("2. Normalize quantities and units")
    print("3. Create proper foreign key relationships")
    print("4. Implement search and API endpoints")

if __name__ == "__main__":
    main()
