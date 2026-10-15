
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "briel.db"


def connect():
    return sqlite3.connect(DB_PATH, timeout=10)


def initialize_database():
    with connect() as conn:
        cursor = conn.cursor()

        # Create inventory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                price REAL NOT NULL DEFAULT 0,
                cost REAL NOT NULL DEFAULT 0
            )
        """)

        # Add cost column if upgrading an older database
        cursor.execute("PRAGMA table_info(inventory)")
        columns = [column[1] for column in cursor.fetchall()]

        if "cost" not in columns:
            cursor.execute("""
                ALTER TABLE inventory
                ADD COLUMN cost REAL NOT NULL DEFAULT 0
            """)

        # Add starting product if it doesn't already exist
        cursor.execute("""
            INSERT OR IGNORE INTO inventory
            (id, product_name, quantity, price, cost)
            VALUES (?, ?, ?, ?, ?)
        """, (
            1,
            "BRIEL Shampoo",
            100,
            49.99,
            11.99
        ))

        # Create sales table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                sale_date TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                revenue REAL NOT NULL,
                cost_of_goods REAL NOT NULL,
                FOREIGN KEY (product_id)
                    REFERENCES inventory(id)
            )
        """)

        conn.commit()

    print("Sales & Inventory database initialized successfully!")


if __name__ == "__main__":
    initialize_database()
