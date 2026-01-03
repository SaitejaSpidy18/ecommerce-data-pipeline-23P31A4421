SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    c.country,
    SUM(f.total_amount) AS total_spend,
    COUNT(DISTINCT f.transaction_id) AS order_count
FROM warehouse.fact_sales f
JOIN warehouse.dim_customer c
    ON f.customer_sk = c.customer_sk
GROUP BY c.customer_id, c.first_name, c.last_name, c.country
ORDER BY total_spend DESC
LIMIT 20;
