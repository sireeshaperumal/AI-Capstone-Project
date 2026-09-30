-- a) Order totals
-- total_orders  total_revenue  avg_order_value
-- '180'          '99860.20'     '554.78'

SELECT COUNT(*) AS total_orders,
       ROUND(SUM(quantity * price * (1 - COALESCE(discount_pct,0)/100)),2) AS total_revenue,
       ROUND(AVG(quantity * price * (1 - COALESCE(discount_pct,0)/100)),2) AS avg_order_value
FROM orders o
JOIN products p ON o.product_id = p.product_id;

-- b) COUNT(*) vs COUNT(column)
-- total_orders	 rated_orders	unrated_orders
-- 180	          165	          15


SELECT COUNT(*) AS total_orders,
       COUNT(rating) AS rated_orders,
       COUNT(*) - COUNT(rating) AS unrated_orders
FROM orders;

-- c) Customers with zero orders (LEFT JOIN)

-- customer_id	name
-- C045	        Vihaan


SELECT c.customer_id, c.name
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id) = 0;

-- c) Customers with zero orders (NOT IN)

--  customer_id	name
-- C045	Vihaan


SELECT customer_id, name
FROM customers
WHERE customer_id IS NOT NULL
  AND customer_id NOT IN (
      SELECT DISTINCT customer_id
      FROM orders
      WHERE customer_id IS NOT NULL
  );
  
-- d) Return rate by city
--  city	total_orders	returned_orders	return_rate_pct
--  Jaipur  	19	               8	    42.1
--  Lucknow   	49      	      15	    30.6
--  Bangalore	33	               8	    24.2

SELECT c.city,
       COUNT(*) AS total_orders,
       SUM(o.returned) AS returned_orders,
       ROUND(SUM(o.returned)*100.0/COUNT(*),1) AS return_rate_pct
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING return_rate_pct > 20
ORDER BY return_rate_pct DESC;

-- e) Top spend orders (LIMIT 5)

-- customer_id	name	total_spend
-- C043	Reyansh	12920.00
-- C026	Isha	8371.60
-- C008	Meera	4564.60
-- C011	Arjun	4111.00
-- C042	Sanya	3785.00

-- Tie-break: ORDER BY total_spend DESC, customer_id ASC ensures accuracy in ranking in case two customers have same total spend.
SELECT c.customer_id, c.name,
       ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct,0)/100)),2) AS total_spend
FROM orders o
JOIN products p ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 5;


-- e) Top spenders subset (LIMIT 3 OFFSET 2)

-- # customer_id	name	total_spend
-- C008	Meera	4564.60
-- C011	Arjun	4111.00
-- C042	Sanya	3785.00


SELECT c.customer_id, c.name,
       round(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct,0)/100)),2) AS total_spend
FROM orders o
JOIN products p ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 3 OFFSET 2;
  
-- f) Category-wise revenue
-- # category	order_count	category_revenue
--  Haircare	54	44956.10
--  Skincare	60	27346.00
--  Babycare	30	16805.00
--  PersonalCare	36	10753.10

SELECT p.category,
       COUNT(*) AS order_count,
       round(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct,0)/100)),2) AS category_revenue
FROM orders o
JOIN products p ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY p.category
ORDER BY category_revenue DESC;

-- g) Names starting with 'A'
-- # customer_id	name	city	city_tier	signup_date	acquisition_source
-- C001         	Aarav	Mumbai  	1	   2026-01-07	Organic
-- C003         	Aditi	Mumbai	    1	   2026-06-23	Organic
-- C004         	Ananya	Lucknow	    2	   2026-01-23	Organic
-- C011         	Arjun	Bangalore	1      2026-03-13	Referral
-- C021         	Aryan	Bangalore	1	   2026-02-11	Ad
-- C030         	Anika	Bangalore	1	   2026-02-24	Organic
-- C031         	Aditya	Jaipur   	2      2026-06-14	Ad
-- C036         	Aisha	Delhi   	1	   2026-05-11	Ad
-- C041         	Ayaan	Lucknow  	2	  2026-01-03	Organic
-- C044         	Aria	Bangalore	1	  2026-04-22	Referral

SELECT *
FROM customers
WHERE name LIKE 'A%';

-- h) Distinct acquisition sources
# acquisition_source
-- Organic
-- Referral
-- Ad
-- Social

SELECT DISTINCT acquisition_source
FROM customers;

-- i) Loyalty tier update
--  loyalty_tier	COUNT(*)
-- Gold         	28
-- Silver	        17

ALTER TABLE customers ADD loyalty_tier VARCHAR(10);

UPDATE customers
SET loyalty_tier = CASE
    WHEN city_tier = 1 THEN 'Gold'
    ELSE 'Silver'
END;

SELECT loyalty_tier, COUNT(*)
FROM customers
GROUP BY loyalty_tier;