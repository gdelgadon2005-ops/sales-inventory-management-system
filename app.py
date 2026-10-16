import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sales & Inventory Tracker", page_icon="📊", layout="wide")
DB_PATH = Path(__file__).resolve().parent / "inventory.db"
PRODUCT_ID = 1
DISPLAY_PRODUCT_NAME = "Sample Product"


def connect():
    return sqlite3.connect(DB_PATH, timeout=10)


def load_data():
    with connect() as conn:
        product = pd.read_sql_query(
            "SELECT id, product_name, quantity, price, cost FROM inventory WHERE id = ?",
            conn, params=(PRODUCT_ID,)
        )
        sales = pd.read_sql_query(
            "SELECT id, sale_date, quantity, revenue, cost_of_goods FROM sales WHERE product_id = ? ORDER BY id DESC",
            conn, params=(PRODUCT_ID,)
        )
    return product, sales


def record_sale(quantity):
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT quantity, price, cost FROM inventory WHERE id = ?", (PRODUCT_ID,)
        ).fetchone()
        if row is None:
            raise ValueError("The product was not found in inventory.")
        available, price, cost = row
        if quantity > available:
            raise ValueError(f"Only {available} units are available.")
        conn.execute("UPDATE inventory SET quantity = quantity - ? WHERE id = ?", (quantity, PRODUCT_ID))
        conn.execute(
            "INSERT INTO sales (product_id, sale_date, quantity, revenue, cost_of_goods) "
            "VALUES (?, datetime('now', 'localtime'), ?, ?, ?)",
            (PRODUCT_ID, quantity, round(quantity * price, 2), round(quantity * cost, 2))
        )


def change_inventory(amount):
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        result = conn.execute(
            "UPDATE inventory SET quantity = quantity + ? WHERE id = ? AND quantity + ? >= 0",
            (amount, PRODUCT_ID, amount)
        )
        if result.rowcount != 1:
            raise ValueError("Inventory cannot become negative or the product was not found.")


st.title("Sales & Inventory Tracker")
st.caption("Simple sales, inventory, and profitability management")

if not DB_PATH.exists():
    from database import initialize_database
    initialize_database()

try:
    inventory, sales = load_data()
except (sqlite3.Error, pd.errors.DatabaseError) as error:
    st.error(f"Could not load database: {error}. Check that database.py created the inventory and sales tables.")
    st.stop()

if inventory.empty:
    st.error("The sample product is missing from the inventory table.")
    st.stop()

product = inventory.iloc[0]
stock = int(product["quantity"])
price = float(product["price"])
cost = float(product["cost"])
revenue = float(sales["revenue"].sum())
gross_profit = revenue - float(sales["cost_of_goods"].sum())
margin = (gross_profit / revenue * 100) if revenue else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", f"${revenue:,.2f}")
c2.metric("Gross Profit", f"${gross_profit:,.2f}")
c3.metric("Inventory", f"{stock} units")
c4.metric("Gross Margin", f"{margin:.1f}%")

st.divider()
tab_sale, tab_inventory, tab_profit, tab_history, tab_analytics = st.tabs([
    "Record Sale", "Manage Inventory", "Profitability Calculator", "Sales History", "Analytics"
])

with tab_sale:
    st.subheader("Record a New Sale")
    st.write(f"**Product:** {DISPLAY_PRODUCT_NAME}")
    st.write(f"**Price:** ${price:.2f} per unit")
    st.write(f"**Available:** {stock} units")
    with st.form("record_sale"):
        quantity = st.number_input("Quantity sold", min_value=1, step=1, value=1)
        st.write(f"**Sale total:** ${quantity * price:,.2f}")
        submit_sale = st.form_submit_button("Record Sale", type="primary")
    if submit_sale:
        try:
            record_sale(int(quantity))
            st.success("Sale recorded!")
            st.rerun()
        except (ValueError, sqlite3.Error) as error:
            st.error(str(error))

with tab_inventory:
    st.subheader("Manage Inventory")
    st.metric("Current Inventory", f"{stock} units")
    with st.form("adjust_inventory"):
        adjustment = st.number_input("Units to add (use a negative number to remove)", value=0, step=1)
        submit_inventory = st.form_submit_button("Update Inventory")
    if submit_inventory:
        try:
            change_inventory(int(adjustment))
            st.success("Inventory updated!")
            st.rerun()
        except (ValueError, sqlite3.Error) as error:
            st.error(str(error))

with tab_profit:
    st.subheader("Profitability Calculator")
    expenses = st.number_input("Estimated operating expenses ($)", min_value=0.0, value=0.0, step=10.0)
    st.metric("Gross Profit", f"${gross_profit:,.2f}")
    st.metric("Estimated Profit Before Tax", f"${gross_profit - expenses:,.2f}")
    st.caption("Operating expenses entered here are for this calculation only and are not saved.")
    st.divider()
    st.subheader("What-if Simulator")
    sim_price = st.number_input("Selling price per unit ($)", min_value=0.0, value=price)
    sim_cost = st.number_input("Cost per unit ($)", min_value=0.0, value=cost)
    sim_units = st.number_input("Projected units sold", min_value=0, value=100, step=1)
    sim_expenses = st.number_input("Projected expenses ($)", min_value=0.0, value=0.0)
    st.metric("Projected Revenue", f"${sim_price * sim_units:,.2f}")
    st.metric("Projected Profit Before Tax", f"${(sim_price - sim_cost) * sim_units - sim_expenses:,.2f}")

with tab_history:
    st.subheader("Sales History")
    if sales.empty:
        st.info("No sales recorded yet.")
    else:
        history = sales.copy()
        history["gross_profit"] = history["revenue"] - history["cost_of_goods"]
        st.dataframe(history, use_container_width=True, hide_index=True)

with tab_analytics:
    st.subheader("Sales Analytics")
    if sales.empty:
        st.info("Record your first sale to see analytics.")
    else:
        st.metric("Transactions", len(sales))
        st.metric("Units Sold", int(sales["quantity"].sum()))
        monthly = sales.copy()
        monthly["month"] = pd.to_datetime(monthly["sale_date"]).dt.to_period("M").astype(str)
        summary = monthly.groupby("month", as_index=False)[["revenue", "cost_of_goods"]].sum()
        summary["gross_profit"] = summary["revenue"] - summary["cost_of_goods"]
        st.line_chart(summary.set_index("month")[["revenue", "gross_profit"]])
