-- Stage 1: Simple tables without foreign key constraints
-- For initial data loading and exploration

DROP TABLE IF EXISTS measurements;
DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS cocktail_images;
DROP TABLE IF EXISTS cocktails;
DROP TABLE IF EXISTS ingredients;
DROP TABLE IF EXISTS glass_type;
DROP TABLE IF EXISTS users;

-- Basic cocktails table - no FK constraints
CREATE TABLE cocktails (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(100),
    description TEXT,
    instructions TEXT,
    glass_type VARCHAR(100),  -- Just text for now
    iba_classification VARCHAR(50),
    aliases TEXT[],
    source VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Basic ingredients table - no FK constraints
CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    type VARCHAR(50),
    category VARCHAR(50),
    alcohol_content NUMERIC,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Basic measurements table - no FK constraints, just text references
CREATE TABLE measurements (
    id SERIAL PRIMARY KEY,
    cocktail_name VARCHAR(255),  -- Text reference for now
    ingredient_name VARCHAR(255), -- Text reference for now
    quantity VARCHAR(100),        -- Keep as text to handle varied formats
    unit VARCHAR(50),
    optional BOOLEAN DEFAULT FALSE,
    source VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Glass types as simple lookup
CREATE TABLE glass_type (
    id SERIAL PRIMARY KEY,
    type_name VARCHAR(100) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Users table (can stay as-is)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Ratings without FK constraints for now
CREATE TABLE ratings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,              -- Just integer for now
    cocktail_name VARCHAR(255),   -- Text reference for now
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    notes TEXT,
    private BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Images without FK constraints
CREATE TABLE cocktail_images (
    id SERIAL PRIMARY KEY,
    cocktail_name VARCHAR(255),   -- Text reference for now
    image_path TEXT,
    alt_text VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);