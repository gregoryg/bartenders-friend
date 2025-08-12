
CREATE TABLE glass_type (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE -- Standardized glass types
);

CREATE TABLE ingredient (
    id               BIGSERIAL PRIMARY KEY,
    name             TEXT NOT NULL UNIQUE,
    type             TEXT,
    category         TEXT,
    alcohol_content  NUMERIC CHECK (alcohol_content BETWEEN 0 AND 100),
    description      TEXT
);

-- 2.  Core recipe table -----------------------------------------------
CREATE TABLE cocktail (
    id                 BIGSERIAL PRIMARY KEY,
    name               TEXT NOT NULL UNIQUE,
    description        TEXT,
    instructions       TEXT,
    glass_type_id      BIGINT REFERENCES glass_type(id) ON DELETE RESTRICT,
    category           TEXT,
    timing             TEXT,
    taste_profile      TEXT,
    iba_classification TEXT,
    aliases            TEXT[],     -- alternative names
    source             TEXT -- attribute source of origin
);

-- Create proper cross-reference table for cocktail-ingredient relationships
-- This replaces the simplified measurements table approach

CREATE TABLE cocktail_ingredient (
    cocktail_id      BIGINT NOT NULL REFERENCES cocktail(id) ON DELETE CASCADE,
    ingredient_id    BIGINT NOT NULL REFERENCES ingredient(id) ON DELETE CASCADE,
    quantity         TEXT,       -- free‑form for now (e.g. “1 1/2 oz”)
    unit             TEXT,       -- Will normalize later (oz, ml, dash, etc.)
    ingredient_order INTEGER,    -- Order of ingredient in recipe (1st, 2nd, etc.)
    optional         BOOLEAN DEFAULT FALSE,
    notes            TEXT,       -- For garnish notes, preparation hints, etc.
    source_dataset   TEXT, -- Track which dataset this came from
    created_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cocktail_id, ingredient_id)
);

CREATE TABLE measurements (
    id SERIAL PRIMARY KEY,
    cocktail_id INT REFERENCES cocktail(id), -- Foreign key to cocktail
    ingredient_id INT REFERENCES ingredient(id), -- Foreign key to ingredient
    quantity NUMERIC,
    unit VARCHAR(50),
    optional BOOLEAN DEFAULT FALSE
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
    cocktail_id INT REFERENCES cocktail(id), -- Foreign key to cocktail
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    private BOOLEAN DEFAULT TRUE  -- Indicate if a rating is private
);

CREATE TABLE cocktail_images (
    id SERIAL PRIMARY KEY,
    cocktail_id INT REFERENCES cocktail(id), -- Foreign key to cocktail
    image_path TEXT,
    alt_text VARCHAR(255)
);
