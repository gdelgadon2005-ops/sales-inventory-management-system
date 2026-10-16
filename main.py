# Sales, Inventory & Profitability Management System

import sqlite3
from datetime import datetime
from pathlib import Path

from database import initialize_database

DATABASE = str(Path(__file__).resolve().parent / "inventory.db")
PRODUCT_ID = 1


# ==========================================
# DATABASE FUNCTIONS
# ==========================================

def connect_database():
    return sqlite3.connect(DATABASE)


def setup_sales_database():
    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            sale_date TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            revenue REAL NOT NULL,
            cost_of_goods REAL NOT NULL,
            FOREIGN KEY (product_id) REFERENCES inventory(id)
        )
    """)

    connection.commit()
    connection.close()


def get_product():
    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT product_name, quantity, price, cost
        FROM inventory
        WHERE id = ?
    """, (PRODUCT_ID,))

    product = cursor.fetchone()
    connection.close()

    if product is None:
        raise ValueError("Product not found in database.")

    return product


def save_inventory():
    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE inventory
        SET quantity = ?
        WHERE id = ?
    """, (inventory, PRODUCT_ID))

    connection.commit()
    connection.close()


# ==========================================
# INITIALIZE DATABASE
# ==========================================

initialize_database()
setup_sales_database()

product_name, inventory, price, cost = get_product()


# ==========================================
# INPUT VALIDATION
# ==========================================

def get_integer(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value >= 0:
                return value
            print("Please enter a non-negative number.")
        except ValueError:
            print("Invalid input. Please enter a whole number.")


def get_decimal(prompt):
    while True:
        try:
            value = float(input(prompt))
            if 0 <= value < float("inf"):
                return value
            print("Please enter a valid non-negative amount.")
        except ValueError:
            print("Invalid input. Please enter a number.")


# ==========================================
# STARTUP INVENTORY CHECK
# ==========================================

print("\n=== INVENTORY CHECK ===")
print("Current inventory:", inventory, "units")

update = input("Does inventory need to be updated? (yes/no): ").lower().strip()

if update == "yes":
    print("\n1. ADD to existing inventory")
    print("2. UPDATE inventory")

    choice_update = input("Choose an option (1-2): ")

    if choice_update == "1":
        new_stock = get_integer("How many units arrived? ")

        inventory += new_stock
        save_inventory()

        print("Updated inventory:", inventory)

    elif choice_update == "2":
        updated_stock = get_integer("What is the new inventory? ")

        inventory = updated_stock
        save_inventory()

        print("Updated inventory:", inventory)

    else:
        print("Invalid choice.")

elif update == "no":
    print("Inventory will remain the same.")

else:
    print("Invalid choice.")


# ==========================================
# MAIN MENU
# ==========================================

def display_menu():
    print("\n=== SALES & INVENTORY MANAGEMENT SYSTEM ===")
    print("1. View Inventory")
    print("2. Record a Sale")
    print("3. View Total Revenue")
    print("4. View Actual Profitability")
    print("5. Profitability Simulator")
    print("6. View Sales History")
    print("7. Sales Analytics Dashboard")
    print("8. Exit")


# ==========================================
# 1. VIEW INVENTORY
# ==========================================

def view_inventory():
    print("\n=== INVENTORY ===")
    print("Product:", product_name)
    print(f"Selling Price: ${price:.2f}")
    print(f"Cost Per Unit: ${cost:.2f}")
    print("Units in Stock:", inventory)


# ==========================================
# 2. RECORD A SALE
# ==========================================

def sale():
    global inventory

    print("\n=== RECORD A SALE ===")

    units_sold = get_integer("How many units were sold? ")

    if units_sold == 0:
        print("Sale quantity must be greater than zero.")
        return

    if units_sold > inventory:
        print("Insufficient inventory.")
        return

    revenue = round(units_sold * price, 2)
    cost_of_goods = round(units_sold * cost, 2)
    gross_profit = revenue - cost_of_goods

    connection = connect_database()
    cursor = connection.cursor()

    try:
        # Update inventory
        cursor.execute("""
            UPDATE inventory
            SET quantity = quantity - ?
            WHERE id = ? AND quantity >= ?
        """, (units_sold, PRODUCT_ID, units_sold))

        if cursor.rowcount != 1:
            connection.rollback()
            print("Insufficient stock or product unavailable.")
            return

        # Save transaction
        cursor.execute("""
            INSERT INTO sales
            (product_id, sale_date, quantity, revenue, cost_of_goods)
            VALUES (?, ?, ?, ?, ?)
        """, (
            PRODUCT_ID,
            datetime.now().isoformat(timespec="seconds"),
            units_sold,
            revenue,
            cost_of_goods
        ))

        connection.commit()
        inventory -= units_sold

        print("\nSale recorded successfully!")
        print(f"Revenue: ${revenue:.2f}")
        print(f"Cost of Goods Sold: ${cost_of_goods:.2f}")
        print(f"Gross Profit: ${gross_profit:.2f}")
        print("Remaining Inventory:", inventory)

    except sqlite3.Error as error:
        connection.rollback()
        print("Database error:", error)

    finally:
        connection.close()


# ==========================================
# SALES TOTALS HELPER
# ==========================================

def get_sales_totals():
    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(quantity), 0),
            COALESCE(SUM(revenue), 0),
            COALESCE(SUM(cost_of_goods), 0)
        FROM sales
        WHERE product_id = ?
    """, (PRODUCT_ID,))

    totals = cursor.fetchone()
    connection.close()

    return totals


# ==========================================
# 3. VIEW TOTAL REVENUE
# ==========================================

def view_revenue():
    transactions, units, revenue, costs = get_sales_totals()

    print("\n=== TOTAL REVENUE ===")
    print("Total Transactions:", transactions)
    print("Total Units Sold:", units)
    print(f"Total Revenue: ${revenue:.2f}")


# ==========================================
# 4. VIEW ACTUAL PROFITABILITY
# ==========================================

def actual_profitability():
    transactions, units, revenue, costs = get_sales_totals()

    gross_profit = revenue - costs

    print("\n=== ACTUAL SALES PROFITABILITY ===")
    print("Total Units Sold:", units)
    print(f"Total Revenue: ${revenue:.2f}")
    print(f"Cost of Goods Sold: ${costs:.2f}")
    print(f"Gross Profit: ${gross_profit:.2f}")

    expenses = get_decimal(
        "Enter total operating expenses for these sales: $"
    )

    estimated_profit = gross_profit - expenses

    if revenue > 0:
        margin = (estimated_profit / revenue) * 100
    else:
        margin = 0

    print("\n=== PROFITABILITY REPORT ===")
    print(f"Operating Expenses: ${expenses:.2f}")
    print(f"Estimated Net Profit Before Taxes: ${estimated_profit:.2f}")
    print(f"Estimated Profit Margin: {margin:.2f}%")


# ==========================================
# 5. PROFITABILITY SIMULATOR
# ==========================================

def profitability_simulator():
    print("\n=== PROFITABILITY SIMULATOR ===")

    selling_price = get_decimal("Enter selling price per unit: $")
    unit_cost = get_decimal("Enter cost per unit: $")
    units = get_integer("Enter projected units sold: ")
    expenses = get_decimal("Enter projected operating expenses: $")

    revenue = selling_price * units
    cost_of_goods = unit_cost * units
    gross_profit = revenue - cost_of_goods
    estimated_profit = gross_profit - expenses

    if revenue > 0:
        gross_margin = (gross_profit / revenue) * 100
        net_margin = (estimated_profit / revenue) * 100
    else:
        gross_margin = 0
        net_margin = 0

    print("\n=== PROJECTED PROFITABILITY ===")
    print(f"Projected Revenue: ${revenue:.2f}")
    print(f"Cost of Goods Sold: ${cost_of_goods:.2f}")
    print(f"Gross Profit: ${gross_profit:.2f}")
    print(f"Gross Profit Margin: {gross_margin:.2f}%")
    print(f"Operating Expenses: ${expenses:.2f}")
    print(f"Estimated Net Profit Before Taxes: ${estimated_profit:.2f}")
    print(f"Estimated Net Profit Margin: {net_margin:.2f}%")


# ==========================================
# 6. SALES TRANSACTION HISTORY
# ==========================================

def view_sales_history():
    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            sale_date,
            quantity,
            revenue,
            cost_of_goods,
            revenue - cost_of_goods AS gross_profit
        FROM sales
        WHERE product_id = ?
        ORDER BY sale_date DESC, id DESC
    """, (PRODUCT_ID,))

    sales = cursor.fetchall()
    connection.close()

    print("\n=== SALES TRANSACTION HISTORY ===")

    if not sales:
        print("No sales have been recorded yet.")
        return

    print(f"{'ID':<5} {'Date':<20} {'Qty':<6} "
          f"{'Revenue':<12} {'COGS':<12} {'Gross Profit':<12}")

    print("-" * 75)

    for transaction in sales:
        sale_id, date, quantity, revenue, costs, profit = transaction

        print(
            f"{sale_id:<5} {date:<20} {quantity:<6} "
            f"${revenue:<11.2f} ${costs:<11.2f} "
            f"${profit:<11.2f}"
        )


# ==========================================
# 7. SALES ANALYTICS DASHBOARD
# ==========================================

def sales_analytics():
    connection = connect_database()
    cursor = connection.cursor()

    # Overall performance
    cursor.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(quantity), 0),
            COALESCE(SUM(revenue), 0),
            COALESCE(SUM(cost_of_goods), 0)
        FROM sales
        WHERE product_id = ?
    """, (PRODUCT_ID,))

    transactions, units, revenue, costs = cursor.fetchone()

    gross_profit = revenue - costs

    if revenue > 0:
        gross_margin = (gross_profit / revenue) * 100
    else:
        gross_margin = 0

    print("\n=== SALES ANALYTICS DASHBOARD ===")

    print("\n--- OVERALL PERFORMANCE ---")
    print("Total Transactions:", transactions)
    print("Total Units Sold:", units)
    print(f"Total Revenue: ${revenue:.2f}")
    print(f"Cost of Goods Sold: ${costs:.2f}")
    print(f"Gross Profit: ${gross_profit:.2f}")
    print(f"Gross Profit Margin: {gross_margin:.2f}%")

    # Monthly sales trends
    cursor.execute("""
        SELECT
            strftime('%Y-%m', sale_date) AS month,
            SUM(quantity),
            SUM(revenue),
            SUM(revenue - cost_of_goods)
        FROM sales
        WHERE product_id = ?
        GROUP BY strftime('%Y-%m', sale_date)
        ORDER BY month
    """, (PRODUCT_ID,))

    monthly_sales = cursor.fetchall()
    connection.close()

    print("\n--- MONTHLY SALES TRENDS ---")

    if not monthly_sales:
        print("No monthly sales data available.")
        return

    for month, quantity, monthly_revenue, monthly_profit in monthly_sales:
        print(f"\nMonth: {month}")
        print("Units Sold:", quantity)
        print(f"Revenue: ${monthly_revenue:.2f}")
        print(f"Gross Profit: ${monthly_profit:.2f}")


# ==========================================
# MAIN PROGRAM
# ==========================================

while True:
    display_menu()

    choice = input("Choose an option (1-8): ").strip()

    if choice == "1":
        view_inventory()

    elif choice == "2":
        sale()

    elif choice == "3":
        view_revenue()

    elif choice == "4":
        actual_profitability()

    elif choice == "5":
        profitability_simulator()

    elif choice == "6":
        view_sales_history()

    elif choice == "7":
        sales_analytics()

    elif choice == "8":
        print("Goodbye! Thanks for using the Sales & Inventory Tracker.")
        break

    else:
        print("Invalid option. Please try again.")

