#!/usr/bin/env python3
"""
Bartender's Friend - Source data migration

Goals:
- Import cocktails and ingredients from staging tables into normalized schema.
- Preserve ingredient order and free-form quantities.
- Be idempotent (safe to re-run). Uses ON CONFLICT upserts where appropriate.
- Preserve source attribution at the recipe level (cocktail.source).
  Optionally populate cocktail_ingredient.source_dataset for audit; can be disabled.

Datasets handled:
- the_cocktail_db (columns: drink, category, glass, iba, ingredient_order, ingredient, measure, ...)
- boston_cocktails (columns: name, category, ingredient_number, ingredient, measure)

Usage:
  python3 scripts/migration/migrate_sources.py --source both [--limit N] [--dry-run]

Env overrides (optional):
  BF_DB_NAME, BF_DB_USER, BF_DB_PASSWORD, BF_DB_HOST, BF_DB_PORT

Notes:
  - Measurements are stored free-form in cocktail_ingredient.quantity
  - Ingredient order preserved via cocktail_ingredient.ingredient_order
  - Glass names are title-cased and inserted lazily in glass_type

# Reason: Keep migration logic explicit, avoid ORM overhead, and ensure
# predictable SQL-level conflict handling for idempotency.
"""
from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import psycopg2
import psycopg2.extras


@dataclass
class DBConfig:
    name: str = os.getenv("BF_DB_NAME", "bartenders_friend")
    user: str = os.getenv("BF_DB_USER", os.getenv("USER", "postgres"))
    password: Optional[str] = os.getenv("BF_DB_PASSWORD")
    host: str = os.getenv("BF_DB_HOST", "localhost")
    port: int = int(os.getenv("BF_DB_PORT", "5432"))


def connect(cfg: DBConfig):
    conn = psycopg2.connect(
        dbname=cfg.name,
        user=cfg.user,
        password=cfg.password,
        host=cfg.host,
        port=cfg.port,
    )
    conn.autocommit = False
    return conn


def title_case(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.strip()
    return s.title() if s else None


def get_or_create_glass(cur, name: Optional[str]) -> Optional[int]:
    if not name:
        return None
    norm = title_case(name)
    cur.execute("SELECT id FROM glass_type WHERE name = %s", (norm,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO glass_type(name) VALUES (%s) RETURNING id", (norm,))
    return cur.fetchone()[0]


def get_or_create_ingredient(cur, name: str) -> int:
    key = name.strip()
    if not key:
        raise ValueError("ingredient name cannot be empty")
    cur.execute("SELECT id FROM ingredient WHERE name = %s", (key,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO ingredient(name) VALUES (%s) RETURNING id", (key,))
    return cur.fetchone()[0]


def upsert_cocktail(
    cur,
    *,
    name: str,
    source: str,
    category: Optional[str],
    glass: Optional[str],
    description: Optional[str] = None,
    instructions: Optional[str] = None,
) -> int:
    glass_id = get_or_create_glass(cur, glass)
    # Use ON CONFLICT on (name, source)
    cur.execute(
        """
        INSERT INTO cocktail(name, source, category, glass_type_id, description, instructions)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (name, source)
        DO UPDATE SET
            category = EXCLUDED.category,
            glass_type_id = COALESCE(EXCLUDED.glass_type_id, cocktail.glass_type_id),
            description = COALESCE(EXCLUDED.description, cocktail.description),
            instructions = COALESCE(EXCLUDED.instructions, cocktail.instructions)
        RETURNING id
        """,
        (name, source, category, glass_id, description, instructions),
    )
    return cur.fetchone()[0]


def upsert_cocktail_ingredient(
    cur,
    *,
    cocktail_id: int,
    ingredient_id: int,
    quantity: Optional[str],
    order_index: Optional[int],
    source_dataset: Optional[str],
):
    cur.execute(
        """
        INSERT INTO cocktail_ingredient(
            cocktail_id, ingredient_id, quantity, ingredient_order, source_dataset
        ) VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (cocktail_id, ingredient_id)
        DO UPDATE SET
            quantity = EXCLUDED.quantity,
            ingredient_order = EXCLUDED.ingredient_order,
            source_dataset = EXCLUDED.source_dataset
        """,
        (cocktail_id, ingredient_id, quantity, order_index, source_dataset),
    )


# --- Importers ----------------------------------------------------------

def import_the_cocktail_db(cur, *, limit: Optional[int] = None) -> Tuple[int, int, int, int]:
    """
    Import cocktails from the_cocktail_db staging table.

    Returns:
        (cocktails_created_or_upserted, cocktails_skipped, relations_upserted, name_conflicts)
    """
    # Fetch distinct drinks with basic attributes
    cur.execute(
        (
            "SELECT drink, MAX(glass) AS glass, MAX(category) AS category "
            "FROM the_cocktail_db GROUP BY drink ORDER BY drink"
            + (" LIMIT %s" if limit else "")
        ),
        ((limit,) if limit else None),
    )
    drinks = cur.fetchall()

    created = 0
    skipped = 0
    rels = 0
    conflicts = 0  # retained for parity in summary

    for (drink_name, glass, category) in drinks:
        cocktail_id = upsert_cocktail(
            cur,
            name=drink_name,
            source="the_cocktail_db",
            category=category,
            glass=glass,
        )
        created += 1
        # Load ingredients for this drink ordered by ingredient_order
        cur.execute(
            """
            SELECT ingredient_order, ingredient, measure
            FROM the_cocktail_db
            WHERE drink = %s AND ingredient IS NOT NULL
            ORDER BY ingredient_order NULLS LAST
            """,
            (drink_name,),
        )
        for order_idx, ingredient_name, measure in cur.fetchall():
            try:
                ing_id = get_or_create_ingredient(cur, ingredient_name)
            except ValueError:
                continue
            upsert_cocktail_ingredient(
                cur,
                cocktail_id=cocktail_id,
                ingredient_id=ing_id,
                quantity=measure,
                order_index=order_idx,
                source_dataset="the_cocktail_db",
            )
            rels += 1

    return created, skipped, rels, conflicts


def import_boston_cocktails(cur, *, limit: Optional[int] = None) -> Tuple[int, int, int, int]:
    """
    Import cocktails from boston_cocktails staging table.

    Returns:
        (cocktails_created_or_upserted, cocktails_skipped, relations_upserted, name_conflicts)
    """
    # Fetch distinct names
    cur.execute(
        (
            "SELECT name, MAX(category) AS category "
            "FROM boston_cocktails GROUP BY name ORDER BY name"
            + (" LIMIT %s" if limit else "")
        ),
        ((limit,) if limit else None),
    )
    names = cur.fetchall()

    created = 0
    skipped = 0
    rels = 0
    conflicts = 0

    for (name, category) in names:
        cocktail_id = upsert_cocktail(
            cur,
            name=name,
            source="boston_cocktails",
            category=category,
            glass=None,  # not provided in this dataset
        )
        created += 1
        # Ingredients ordered by ingredient_number (text -> int where possible)
        cur.execute(
            """
            SELECT CASE WHEN ingredient_number ~ '^\\d+$' THEN ingredient_number::int ELSE NULL END AS order_idx,
                   ingredient,
                   measure
            FROM boston_cocktails
            WHERE name = %s AND ingredient IS NOT NULL
            ORDER BY order_idx NULLS LAST
            """,
            (name,),
        )
        for order_idx, ingredient_name, measure in cur.fetchall():
            try:
                ing_id = get_or_create_ingredient(cur, ingredient_name)
            except ValueError:
                continue
            upsert_cocktail_ingredient(
                cur,
                cocktail_id=cocktail_id,
                ingredient_id=ing_id,
                quantity=measure,
                order_index=order_idx,
                source_dataset="boston_cocktails",
            )
            rels += 1

    return created, skipped, rels, conflicts


# --- CLI ----------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="Migrate staging sources into normalized schema")
    p.add_argument(
        "--source",
        choices=["the_cocktail_db", "boston_cocktails", "both"],
        default="both",
        help="Which source to import",
    )
    p.add_argument("--limit", type=int, default=None, help="Limit cocktails per source (for testing)")
    p.add_argument("--dry-run", action="store_true", help="Run inside a transaction and roll back")
    return p.parse_args()


def main():
    args = parse_args()
    cfg = DBConfig()
    conn = connect(cfg)
    cur = conn.cursor()

    try:
        totals: Dict[str, Tuple[int, int, int, int]] = {}

        if args.source in ("the_cocktail_db", "both"):
            print("=== Importing from the_cocktail_db ===")
            cur.execute("SELECT COUNT(DISTINCT drink) FROM the_cocktail_db")
            total = cur.fetchone()[0]
            if args.limit:
                print(f"[the_cocktail_db] cocktails to process: {args.limit} (limit {args.limit})")
            else:
                print(f"[the_cocktail_db] cocktails to process: {total}")
            totals["the_cocktail_db"] = import_the_cocktail_db(cur, limit=args.limit)

        if args.source in ("boston_cocktails", "both"):
            print("\n=== Importing from boston_cocktails ===")
            cur.execute("SELECT COUNT(DISTINCT name) FROM boston_cocktails")
            total = cur.fetchone()[0]
            if args.limit:
                print(f"[boston_cocktails] cocktails to process: {args.limit} (limit {args.limit})")
            else:
                print(f"[boston_cocktails] cocktails to process: {total}")
            totals["boston_cocktails"] = import_boston_cocktails(cur, limit=args.limit)

        if args.dry_run:
            print("\nDRY RUN: rolling back changes")
            conn.rollback()
        else:
            conn.commit()
            print("\nCommitted changes")

        print("\nSummary:")
        for src, (created, skipped, rels, conflicts) in totals.items():
            print(
                f"  [{src}] cocktails_created_or_upserted={created}, cocktails_skipped={skipped}, "
                f"relations_upserted={rels}, name_conflicts={conflicts}"
            )

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
