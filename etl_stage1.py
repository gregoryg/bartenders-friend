#!/usr/bin/env python3
"""
Stage 1 ETL: Load raw data into simplified tables without foreign key constraints.
This allows us to get all data in first, then clean it up later.
"""

import pandas as pd
from sqlalchemy import create_engine
import os
from pathlib import Path

# Database configuration
DB_URI = 'postgresql://localhost/bartenders_friend'
engine = create_engine(DB_URI)

def load_boston_cocktails(file_path: str):
    """Load boston_cocktails.csv into the database."""
    print(f"Loading {file_path}...")
    df = pd.read_csv(file_path)
    
    # Load unique cocktails
    cocktails_df = df[['name', 'category']].drop_duplicates()
    cocktails_df['source'] = 'boston_cocktails'
    cocktails_df.to_sql('cocktails', engine, if_exists='append', index=False)
    print(f"  Loaded {len(cocktails_df)} unique cocktails")
    
    # Load unique ingredients
    ingredients_df = df[['ingredient']].drop_duplicates()
    ingredients_df.columns = ['name']
    ingredients_df.to_sql('ingredients', engine, if_exists='append', index=False)
    print(f"  Loaded {len(ingredients_df)} unique ingredients")
    
    # Load measurements
    measurements_df = df[['name', 'ingredient', 'measure']].copy()
    measurements_df.columns = ['cocktail_name', 'ingredient_name', 'quantity']
    measurements_df['source'] = 'boston_cocktails'
    measurements_df.to_sql('measurements', engine, if_exists='append', index=False)
    print(f"  Loaded {len(measurements_df)} measurements")

def load_all_drinks(file_path: str):
    """Load all_drinks.csv (denormalized format) into the database."""
    print(f"Loading {file_path}...")
    df = pd.read_csv(file_path)
    
    # Load cocktails
    cocktail_cols = ['strDrink', 'strCategory', 'strInstructions', 'strGlass']
    cocktails_df = df[cocktail_cols].drop_duplicates()
    cocktails_df.columns = ['name', 'category', 'instructions', 'glass_type']
    cocktails_df['source'] = 'all_drinks'
    cocktails_df.to_sql('cocktails', engine, if_exists='append', index=False)
    print(f"  Loaded {len(cocktails_df)} unique cocktails")
    
    # Extract and load ingredients/measurements from ingredient columns
    measurements_list = []
    for index, row in df.iterrows():
        cocktail_name = row['strDrink']
        for i in range(1, 16):  # Ingredient1 through Ingredient15
            ingredient_col = f'strIngredient{i}'
            measure_col = f'strMeasure{i}'
            
            if ingredient_col in df.columns and pd.notna(row[ingredient_col]):
                ingredient = row[ingredient_col]
                measure = row[measure_col] if measure_col in df.columns else ''
                
                measurements_list.append({
                    'cocktail_name': cocktail_name,
                    'ingredient_name': ingredient,
                    'quantity': str(measure) if pd.notna(measure) else '',
                    'source': 'all_drinks'
                })
    
    if measurements_list:
        measurements_df = pd.DataFrame(measurements_list)
        measurements_df.to_sql('measurements', engine, if_exists='append', index=False)
        print(f"  Loaded {len(measurements_df)} measurements")
        
        # Extract unique ingredients
        ingredients_df = measurements_df[['ingredient_name']].drop_duplicates()
        ingredients_df.columns = ['name']
        ingredients_df.to_sql('ingredients', engine, if_exists='append', index=False)
        print(f"  Loaded {len(ingredients_df)} unique ingredients")

def main():
    """Run the Stage 1 ETL process."""
    raw_data_dir = Path('/home/gregj/projects/coding/bartenders-friend/raw-data')
    
    print("=== Stage 1 ETL: Loading Raw Data ===")
    
    # Load boston_cocktails.csv
    boston_file = raw_data_dir / 'boston_cocktails.csv'
    if boston_file.exists():
        load_boston_cocktails(str(boston_file))
    else:
        print(f"Warning: {boston_file} not found")
    
    # Load all_drinks.csv
    all_drinks_file = raw_data_dir / 'all_drinks.csv'
    if all_drinks_file.exists():
        load_all_drinks(str(all_drinks_file))
    else:
        print(f"Warning: {all_drinks_file} not found")
    
    print("\n=== Stage 1 ETL Complete ===")
    print("Next steps:")
    print("1. Review loaded data for quality issues")
    print("2. Run cleanup scripts to deduplicate and normalize")
    print("3. Create relationships and add foreign key constraints")

if __name__ == "__main__":
    main()