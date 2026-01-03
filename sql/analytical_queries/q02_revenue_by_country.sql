SELECT
    c.country,
    SUM(f.total_amount) AS total_revenue
FROM warehouse.fact_sales f
JOIN warehouse.dim_customer c
    ON f.customer_sk = c.customer_sk
GROUP BY c.country
ORDER BY total_revenue DESC;
