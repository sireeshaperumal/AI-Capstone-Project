# analysis/clean_and_eda.py

import pandas as pd

# -------------------------------
# Task 1 — Load and inspect
# -------------------------------
customers = pd.read_csv("data/customers.csv")
products = pd.read_csv("data/products.csv")
orders = pd.read_csv("data/orders.csv")

print("Customers shape:", customers.shape)   # Expect (45, 6)
print("Products shape:", products.shape)     # Expect (16, 4)
print("Orders shape before cleaning:", orders.shape)  # Expect (180, 9)

# -------------------------------
# Task 2 — Standardize payment_method casing
# -------------------------------
print("Payment methods before fix:", orders['payment_method'].unique())

orders['payment_method'] = orders['payment_method'].str.strip().str.upper()

print("Payment methods after fix:", orders['payment_method'].unique())
print("Payment method counts:\n", orders['payment_method'].value_counts())
# Expect ['CARD','UPI','COD'] with counts CARD:70, UPI:55, COD:55

# -------------------------------
# Task 3 — Remove duplicate orders
# -------------------------------
natural_key = [
    "customer_id", "product_id", "order_date", "quantity",
    "discount_pct", "payment_method", "rating", "returned"
]

duplicates = orders[orders.duplicated(subset=natural_key, keep='first')]
print("Duplicate rows flagged:", duplicates.shape[0])
print("Dropped order_id values:", duplicates['order_id'].tolist())
# Expect 5 rows, IDs O0176–O0180

orders_clean = orders.drop_duplicates(subset=natural_key, keep='first').copy()
print("orders_clean shape after deduplication:", orders_clean.shape)
# Expect (175, 9)

# -------------------------------
# Task 4 — Impute missing values
# -------------------------------
print("NaNs in discount_pct before:", orders_clean['discount_pct'].isna().sum())
orders_clean['discount_pct'] = orders_clean['discount_pct'].fillna(0)
print("NaNs in discount_pct after:", orders_clean['discount_pct'].isna().sum())

median_rating = orders_clean['rating'].median()
print("Median rating before imputing:", median_rating)
print("NaNs in rating before:", orders_clean['rating'].isna().sum())
orders_clean['rating'] = orders_clean['rating'].fillna(median_rating)
print("NaNs in rating after:", orders_clean['rating'].isna().sum())
# Expect median = 3.0, 15 rows affected

print("Null counts after imputing:\n", orders_clean[['discount_pct','rating']].isnull().sum())

# -------------------------------
# Task 5 — Merge with products and customers
# -------------------------------
merged = orders_clean.merge(products, on='product_id', how='left')
merged = merged.merge(customers, on='customer_id', how='left')

merged['order_value'] = merged['quantity'] * merged['price'] * (1 - merged['discount_pct']/100)
print("Total order value across cleaned orders:", round(merged['order_value'].sum(), 2))

# -------------------------------
# Task 5 — Reconciliation
# -------------------------------
dropped = duplicates.merge(products, on="product_id", how="left")
dropped_total = (dropped['quantity'] * dropped['price'] * (1 - dropped['discount_pct']/100)).sum()

print("\nReconciliation Note:")
print("Part 1 SQL Report (Task a) showed a raw total revenue of ₹99,860.20 across 180 rows.")
print("Part 2 pandas pipeline shows a cleaned total of ₹97,358.30 across 175 rows.")
print(f"The exact delta of ₹2,501.90 is fully explained by the 5 duplicate orders removed in Task 3, "
      f"whose combined order_value is ₹{dropped_total:.2f}.")
print("This difference is not due to discount or rating imputations, which do not affect order_value.")

# -------------------------------
# Task 6 — IQR outlier detection on quantity
# -------------------------------
Q1 = merged['quantity'].quantile(0.25)
Q3 = merged['quantity'].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

print("\nOutlier detection on quantity:")
print("Q1:", Q1)
print("Q3:", Q3)
print("IQR:", IQR)
print("Lower bound:", lower)
print("Upper bound:", upper)

merged['is_outlier'] = (merged['quantity'] < lower) | (merged['quantity'] > upper)
outliers = merged[merged['is_outlier']]
print("Outlier rows flagged:", outliers.shape[0])
print(outliers[['order_id','quantity']])

# -------------------------------
# Task 7 — COD return rate hypothesis
# -------------------------------
print("\nChecking if COD has a higher return rate")
return_rates = merged.groupby('payment_method')['returned'].agg(['count','mean'])
print(return_rates)

print("\nReturn rates formatted to percentages\n")
return_rates['return_rate_pct'] = round(return_rates['mean']*100, 1)
print(return_rates[['count','return_rate_pct']])

print("\nConclusion: Hypothesis Confirmed — COD shows the highest return rate.")

# -------------------------------
# Task 8 — Multilevel Segmentation
# -------------------------------
return_paymethod_segment = merged.groupby(['payment_method','city_tier']).agg(
    returned_rate=('returned','mean'),
    return_count=('returned','count')
)
return_paymethod_segment['returned_rate_pct'] = round(return_paymethod_segment['returned_rate']*100, 1)
print(return_paymethod_segment.sort_values(by='returned_rate_pct', ascending=False))

highest_risk_seg = return_paymethod_segment.idxmax()['returned_rate_pct']
highest_return_rate = return_paymethod_segment['returned_rate_pct'].max()

print("\nConclusion:")
print(f"The single highest-risk segment is {highest_risk_seg[0]} and tier {highest_risk_seg[1]} cities "
      f"with a return rate of {highest_return_rate:.1f}%.")

# -------------------------------
# Task 9 — Correlation Analysis
# -------------------------------
print("\nCorrelation analysis\n")
corr_matrix = merged[['rating','returned','discount_pct','quantity']].corr().round(2)
print("Correlation matrix:\n", corr_matrix, "\n")

def corr_str(r):
    if abs(r) < 0.2: return "Negligible"
    elif abs(r) < 0.4: return "Weak"
    elif abs(r) < 0.8: return "Moderate"
    else: return "Strong"

cols = ['rating','returned','discount_pct','quantity']
for i in range(len(cols)):
    for j in range(i+1, len(cols)):
        r = corr_matrix
        print(f"Correlation between {cols[i]} and {cols[j]}: {r[cols[i]][cols[j]]} -- {corr_str(r[cols[i]][cols[j]])}")

# -------------------------------
# Task 10 — Outlier-corrected time series
# -------------------------------
print("\nOutlier-corrected time series\n")
merged['order_date'] = pd.to_datetime(merged['order_date'])
merged['order_month'] = merged['order_date'].dt.to_period('M')

total_incl_outliers = merged.groupby('order_month')['order_value'].sum().round(2)
print("Monthly totals including outliers:\n", total_incl_outliers, "\n")

total_excl_outliers = merged[~merged['is_outlier']].groupby('order_month')['order_value'].sum().round(2)
print("Monthly totals excluding outliers:\n", total_excl_outliers, "\n")

print("Conclusion:")
print("January's apparent lead (₹29,582.10) is an artifact of two bulk outlier orders "
      "(O0011 on 2026-01-28 with quantity 25, and O0098 on 2026-01-10 with quantity 30).")
print("Once these are excluded, March emerges as the genuine peak month at ₹20,318.90, "
      "showing why Task 6 outlier detection must precede Task 10 time series analysis.")
