# analysis/visualize.py

import os
import pandas as pd
import matplotlib.pyplot as plt

# Ensure visualizations folder exists
os.makedirs("visualizations", exist_ok=True)

# -------------------------------
# Load raw data and run cleaning pipeline
# -------------------------------
customers = pd.read_csv("data/customers.csv")
products = pd.read_csv("data/products.csv")
orders = pd.read_csv("data/orders.csv")

# Standardize payment_method casing
orders['payment_method'] = orders['payment_method'].str.strip().str.upper()

# Deduplicate
natural_key = [
    "customer_id", "product_id", "order_date", "quantity",
    "discount_pct", "payment_method", "rating", "returned"
]
orders_clean = orders.drop_duplicates(subset=natural_key, keep='first').copy()

# Impute missing values
orders_clean['discount_pct'] = orders_clean['discount_pct'].fillna(0)
orders_clean['rating'] = orders_clean['rating'].fillna(orders_clean['rating'].median())

# Merge with products/customers
merged = orders_clean.merge(products, on="product_id", how="left")
merged = merged.merge(customers, on="customer_id", how="left")

# Compute order_value
merged['order_value'] = merged['quantity'] * merged['price'] * (1 - merged['discount_pct']/100)

# Flag outliers (Task 6)
Q1 = merged['quantity'].quantile(0.25)
Q3 = merged['quantity'].quantile(0.75)
IQR = Q3 - Q1
lower, upper = Q1 - 1.5*IQR, Q3 + 1.5*IQR
merged['is_outlier'] = (merged['quantity'] < lower) | (merged['quantity'] > upper)

# -------------------------------
# Visualization 1: Return rate by payment method
# -------------------------------
return_stats = merged.groupby('payment_method')['returned'].mean().sort_values(ascending=False)
return_stats_pct = (return_stats * 100).round(1)

plt.figure(figsize=(6,4))
bars = plt.bar(return_stats_pct.index, return_stats_pct.values, color=['green','gold','orange'])
plt.title("COD Returns at 44.4% — 3x Card")
plt.ylabel("Return Rate (%)")

for bar, pct in zip(bars, return_stats_pct.values):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{pct:.1f}%", 
             ha='center', va='bottom')

plt.tight_layout()
plt.savefig("visualizations/return_rate_by_payment.png")
plt.close()

# -------------------------------
# Visualization 2: Outlier-corrected monthly revenue trend
# -------------------------------
merged['order_date'] = pd.to_datetime(merged['order_date'])
merged['year_month'] = merged['order_date'].dt.to_period('M').astype(str)

monthly_excl = merged.loc[~merged['is_outlier']].groupby('year_month')['order_value'].sum().round(2)

plt.figure(figsize=(7,4))
plt.plot(monthly_excl.index, monthly_excl.values, marker='o', linestyle='-')
plt.title("Monthly Revenue Trend — March Peak at ₹20,318.90")
plt.xlabel("Year-Month")
plt.ylabel("Revenue (₹)")
plt.grid(True)

plt.tight_layout()
plt.savefig("visualizations/monthly_revenue_trend.png")
plt.close()

print("✅ Saved visualizations to visualizations/")
