WITH order_totals AS (
    SELECT
        f.transaction_id,
        f.customer_sk,
        SUM(f.total_amount) AS order_amount
    FROM warehouse.fact_sales f
    GROUP BY f.transaction_id, f.customer_sk
)
SELECT
    c.country,
    AVG(ot.order_amount) AS avg_order_value
FROM order_totals ot
JOIN warehouse.dim_customer c
    ON ot.customer_sk = c.customer_sk
GROUP BY c.country
ORDER BY avg_order_value DESC;
