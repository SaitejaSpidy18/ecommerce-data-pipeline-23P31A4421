SELECT
    d.date_value AS order_date,
    SUM(f.total_amount) AS total_revenue
FROM warehouse.fact_sales f
JOIN warehouse.dim_date d
    ON f.date_key = d.date_key
GROUP BY d.date_value
ORDER BY d.date_value;
