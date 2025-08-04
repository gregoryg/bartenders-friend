-- Core entities
CREATE TABLE cocktails (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    instructions TEXT,
    glass_type_id INT REFERENCES glass_type(id),
    category VARCHAR(50),
    timing VARCHAR(50),
    taste_profile VARCHAR(50),
    iba_classification VARCHAR(50),
    aliases TEXT[], -- For alternative names
    source VARCHAR(255) -- Attributing source of origin
);

CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    type VARCHAR(50),
    category VARCHAR(50), -- Category for grouping
    alcohol_content NUMERIC CHECK (alcohol_content BETWEEN 0 AND 100),
    description TEXT
);

CREATE TABLE measurements (
    id SERIAL PRIMARY KEY,
    cocktail_id INT REFERENCES cocktails(id), -- Foreign key to cocktails
    ingredient_id INT REFERENCES ingredients(id), -- Foreign key to ingredients
    quantity NUMERIC,
    unit VARCHAR(50),
    optional BOOLEAN DEFAULT FALSE
);

CREATE TABLE glass_type (
    id SERIAL PRIMARY KEY,
    type_name VARCHAR(50) -- Standardized glass types
);

-- Enhancement tables
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ratings (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id), -- Foreign key to users
    cocktail_id INT REFERENCES cocktails(id), -- Foreign key to cocktails
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    private BOOLEAN DEFAULT TRUE  -- Indicate if a rating is private
);

CREATE TABLE cocktail_images (
    id SERIAL PRIMARY KEY,
    cocktail_id INT REFERENCES cocktails(id), -- Foreign key to cocktails
    image_path TEXT,
    alt_text VARCHAR(255)
);
