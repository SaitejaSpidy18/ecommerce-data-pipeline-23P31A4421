SELECT
    p.product_name,
    p.category,
    SUM(f.total_amount) AS revenue
FROM warehouse.fact_sales f
JOIN warehouse.dim_product p
    ON f.product_sk = p.product_sk
GROUP BY p.product_name, p.category
ORDER BY revenue DESC
LIMIT 20;
