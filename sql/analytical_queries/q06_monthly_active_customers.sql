SELECT
    d.year,
    d.month,
    d.month_name,
    COUNT(DISTINCT f.customer_sk) AS monthly_active_customers
FROM warehouse.fact_sales f
JOIN warehouse.dim_date d
    ON f.date_key = d.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;
