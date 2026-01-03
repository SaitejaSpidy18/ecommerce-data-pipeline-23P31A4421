SELECT
    p.category,
    SUM(f.total_amount) AS total_revenue,
    SUM(f.quantity) AS total_quantity,
    AVG(f.unit_price) AS avg_unit_price
FROM warehouse.fact_sales f
JOIN warehouse.dim_product p
    ON f.product_sk = p.product_sk
GROUP BY p.category
ORDER BY total_revenue DESC;
