-- Create proper cross-reference table for cocktail-ingredient relationships
-- This replaces the simplified measurements table approach

CREATE TABLE cocktail_ingredients (
    id SERIAL PRIMARY KEY,
    cocktail_name VARCHAR(255) NOT NULL,
    ingredient_name VARCHAR(255) NOT NULL,
    quantity VARCHAR(100),        -- Keep as text for now (e.g., "1 1/2 oz", "splash", "to taste")
    unit VARCHAR(50),            -- Will normalize later (oz, ml, dash, etc.)
    ingredient_order INTEGER,    -- Order of ingredient in recipe (1st, 2nd, etc.)
    optional BOOLEAN DEFAULT FALSE,
    notes TEXT,                  -- For garnish notes, preparation hints, etc.
    source_dataset VARCHAR(100), -- Track which dataset this came from
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_cocktail_ingredients_cocktail ON cocktail_ingredients(cocktail_name);
CREATE INDEX idx_cocktail_ingredients_ingredient ON cocktail_ingredients(ingredient_name);

-- Migrate data from measurements table
INSERT INTO cocktail_ingredients (cocktail_name, ingredient_name, quantity, source_dataset)
SELECT 
    cocktail_name,
    ingredient_name,
    quantity,
    'boston_cocktails' as source_dataset
FROM measurements
WHERE cocktail_name IN (
    SELECT name FROM cocktails WHERE instructions IS NULL
);

-- Add the all_drinks data with source tracking
-- (This will be handled by an updated ETL script)

-- Show what we have
SELECT 
    source_dataset,
    COUNT(*) as ingredient_entries,
    COUNT(DISTINCT cocktail_name) as unique_cocktails,
    COUNT(DISTINCT ingredient_name) as unique_ingredients
FROM cocktail_ingredients 
GROUP BY source_dataset;