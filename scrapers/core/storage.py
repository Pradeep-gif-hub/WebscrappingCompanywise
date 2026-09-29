"""
Data storage layer supporting JSON, CSV, SQLite database, and Pandas DataFrames.
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd


class DataStorage:
    """Manages saving and loading scraped data across multiple formats."""

    def __init__(self, output_dir: str = "data/output", db_name: str = "scraped_data.db"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.output_dir / db_name
        self._init_sqlite()

    def _init_sqlite(self) -> None:
        """Initialize SQLite database schemas for each scraper type."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Companies Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    domain TEXT,
                    industry TEXT,
                    employees TEXT,
                    headquarters TEXT,
                    founded_year TEXT,
                    tech_stack TEXT,
                    job_openings_count INTEGER,
                    description TEXT,
                    scraped_at TEXT,
                    raw_json TEXT
                )
            """)
            
            # 2. Restaurants Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS restaurants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    cuisine TEXT,
                    rating REAL,
                    review_count INTEGER,
                    price_tier TEXT,
                    city TEXT,
                    address TEXT,
                    phone TEXT,
                    opening_hours TEXT,
                    menu_items_count INTEGER,
                    scraped_at TEXT,
                    raw_json TEXT
                )
            """)
            
            # 3. Games Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    app_id TEXT,
                    price REAL,
                    currency TEXT,
                    is_free INTEGER,
                    release_date TEXT,
                    developer TEXT,
                    publisher TEXT,
                    genres TEXT,
                    metacritic_score INTEGER,
                    user_rating_text TEXT,
                    scraped_at TEXT,
                    raw_json TEXT
                )
            """)
            
            # 4. Wikipedia Articles Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wikipedia_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT UNIQUE,
                    page_id TEXT,
                    language TEXT,
                    url TEXT,
                    summary TEXT,
                    sections_count INTEGER,
                    tables_count INTEGER,
                    references_count INTEGER,
                    scraped_at TEXT,
                    raw_json TEXT
                )
            """)
            
            # 5. E-Commerce Products Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ecommerce_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    category TEXT,
                    price REAL,
                    currency TEXT,
                    availability TEXT,
                    rating REAL,
                    upc TEXT,
                    url TEXT,
                    scraped_at TEXT,
                    raw_json TEXT
                )
            """)
            conn.commit()

    def save_json(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        filename: str,
        add_metadata: bool = True,
    ) -> Path:
        """Save data to formatted JSON file."""
        if not filename.endswith(".json"):
            filename += ".json"
        target_path = self.output_dir / filename
        
        output_payload: Dict[str, Any] = {}
        if add_metadata:
            count = len(data) if isinstance(data, list) else 1
            output_payload = {
                "metadata": {
                    "scraped_at": datetime.now().isoformat(),
                    "record_count": count,
                    "target_file": filename,
                },
                "data": data,
            }
        else:
            output_payload = data  # type: ignore

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2, ensure_ascii=False)
            
        return target_path

    def save_csv(self, data: List[Dict[str, Any]], filename: str) -> Path:
        """Save list of dictionaries as CSV file."""
        if not filename.endswith(".csv"):
            filename += ".csv"
        target_path = self.output_dir / filename
        df = pd.DataFrame(data)
        df.to_csv(target_path, index=False, encoding="utf-8")
        return target_path

    def save_to_db(self, table_name: str, records: Union[Dict[str, Any], List[Dict[str, Any]]]) -> int:
        """Insert records into SQLite database table with raw JSON backup."""
        if isinstance(records, dict):
            records = [records]
            
        if not records:
            return 0

        inserted = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for r in records:
                now_str = datetime.now().isoformat()
                raw_json = json.dumps(r, ensure_ascii=False)
                
                if table_name == "companies":
                    tech = ",".join(r.get("tech_stack", [])) if isinstance(r.get("tech_stack"), list) else str(r.get("tech_stack", ""))
                    jobs = len(r.get("job_openings", [])) if isinstance(r.get("job_openings"), list) else int(r.get("job_openings_count", 0) or 0)
                    cursor.execute("""
                        INSERT INTO companies (name, domain, industry, employees, headquarters, founded_year, tech_stack, job_openings_count, description, scraped_at, raw_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        r.get("name"), r.get("domain"), r.get("industry"), r.get("employees"),
                        r.get("headquarters"), r.get("founded_year"), tech, jobs,
                        r.get("description"), now_str, raw_json
                    ))
                    inserted += 1

                elif table_name == "restaurants":
                    cuisines = ",".join(r.get("cuisine", [])) if isinstance(r.get("cuisine"), list) else str(r.get("cuisine", ""))
                    menu_cnt = len(r.get("menu_items", [])) if isinstance(r.get("menu_items"), list) else 0
                    cursor.execute("""
                        INSERT INTO restaurants (name, cuisine, rating, review_count, price_tier, city, address, phone, opening_hours, menu_items_count, scraped_at, raw_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        r.get("name"), cuisines, r.get("rating"), r.get("review_count"),
                        r.get("price_tier"), r.get("city"), r.get("address"), r.get("phone"),
                        str(r.get("opening_hours")), menu_cnt, now_str, raw_json
                    ))
                    inserted += 1

                elif table_name == "games":
                    genres = ",".join(r.get("genres", [])) if isinstance(r.get("genres"), list) else str(r.get("genres", ""))
                    price_val = r.get("price", {}).get("amount", 0.0) if isinstance(r.get("price"), dict) else float(r.get("price", 0.0) or 0.0)
                    currency_val = r.get("price", {}).get("currency", "USD") if isinstance(r.get("price"), dict) else "USD"
                    is_free_val = 1 if r.get("is_free") or price_val == 0.0 else 0
                    cursor.execute("""
                        INSERT INTO games (title, app_id, price, currency, is_free, release_date, developer, publisher, genres, metacritic_score, user_rating_text, scraped_at, raw_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        r.get("title"), str(r.get("app_id")), price_val, currency_val,
                        is_free_val, r.get("release_date"), r.get("developer"), r.get("publisher"),
                        genres, r.get("metacritic_score"), r.get("user_rating_text"),
                        now_str, raw_json
                    ))
                    inserted += 1

                elif table_name == "wikipedia_articles":
                    cursor.execute("""
                        INSERT OR REPLACE INTO wikipedia_articles (title, page_id, language, url, summary, sections_count, tables_count, references_count, scraped_at, raw_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        r.get("title"), str(r.get("page_id")), r.get("language", "en"),
                        r.get("url"), r.get("summary"), len(r.get("sections", [])),
                        len(r.get("tables", [])), len(r.get("references", [])),
                        now_str, raw_json
                    ))
                    inserted += 1

                elif table_name == "ecommerce_products":
                    price_val = r.get("price", {}).get("amount", 0.0) if isinstance(r.get("price"), dict) else float(r.get("price", 0.0) or 0.0)
                    currency_val = r.get("price", {}).get("currency", "USD") if isinstance(r.get("price"), dict) else "USD"
                    cursor.execute("""
                        INSERT INTO ecommerce_products (title, category, price, currency, availability, rating, upc, url, scraped_at, raw_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        r.get("title"), r.get("category"), price_val, currency_val,
                        r.get("availability"), r.get("rating"), r.get("upc"),
                        r.get("url"), now_str, raw_json
                    ))
                    inserted += 1

            conn.commit()
        return inserted

    def query_db(self, query: str, params: tuple = ()) -> pd.DataFrame:
        """Run SQL query on SQLite database and return DataFrame."""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)

    def to_dataframe(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> pd.DataFrame:
        """Convert data list or dict to Pandas DataFrame."""
        if isinstance(data, dict):
            return pd.DataFrame([data])
        return pd.DataFrame(data)
