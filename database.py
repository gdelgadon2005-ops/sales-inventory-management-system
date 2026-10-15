
import sqlite3
from pathlib import Path

# Database location
DB_PATH = Path(__file__).resolve().parent / "briel.db"


def connect():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with connect() as connection:
        cursor = connection.cursor()

        # Businesses
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                industry TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Products
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                sku TEXT,
                price REAL NOT NULL DEFAULT 0,
                cost REAL NOT NULL DEFAULT 0,
                quantity INTEGER NOT NULL DEFAULT 0,
                reorder_level INTEGER NOT NULL DEFAULT 10,
                FOREIGN KEY (business_id)
                    REFERENCES businesses(id),
                UNIQUE (business_id, sku)
            )
        """)

        # Customers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                FOREIGN KEY (business_id)
                    REFERENCES businesses(id)
            )
        """)

        # Suppliers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                FOREIGN KEY (business_id)
                    REFERENCES businesses(id)
            )
        """)

        # Orders
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                customer_id INTEGER,
                order_date TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'Pending',
                FOREIGN KEY (business_id)
                    REFERENCES businesses(id),
                FOREIGN KEY (customer_id)
                    REFERENCES customers(id)
            )
        """)

        # Products within each order
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL,
                unit_cost REAL NOT NULL,
                FOREIGN KEY (order_id)
                    REFERENCES orders(id),
                FOREIGN KEY (product_id)
                    REFERENCES products(id)
            )
        """)

        # Inventory change history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                quantity_change INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id)
                    REFERENCES products(id)
            )
        """)

        # Business expenses
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL CHECK(amount >= 0),
                expense_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id)
                    REFERENCES businesses(id)
            )
        """)

        # Create BRIEL as the first business
        cursor.execute("""
            SELECT id FROM businesses WHERE name = ?
        """, ("BRIEL",))

        business = cursor.fetchone()

        if business is None:
            cursor.execute("""
                INSERT INTO businesses (name, industry)
                VALUES (?, ?)
            """, ("BRIEL", "Beauty & Personal Care"))

            business_id = cursor.lastrowid
        else:
            business_id = business[0]

        # Import existing BRIEL inventory, if available
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'inventory'
        """)

        if cursor.fetchone():
            cursor.execute("""
                PRAGMA table_info(inventory)
            """)

            columns = [
                column[1] for column in cursor.fetchall()
            ]

            if "cost" not in columns:
                cursor.execute("""
                    ALTER TABLE inventory
                    ADD COLUMN cost REAL NOT NULL DEFAULT 0
                """)

            cursor.execute("""
                SELECT product_name, quantity, price, cost
                FROM inventory
                WHERE id = 1
            """)

            old_product = cursor.fetchone()

            if old_product:
                name, quantity, price, cost = old_product

                cursor.execute("""
                    INSERT OR IGNORE INTO products
                    (business_id, name, sku, price, cost, quantity)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    business_id,
                    name,
                    "BRIEL-001",
                    price,
                    cost,
                    quantity
                ))

        connection.commit()

    print("BusinessOS database initialized successfully!")


if __name__ == "__main__":
    initialize_database()
