-- Simple churn logic: customer is "churned" if no orders in the last 60 days
WITH last_order AS (
    SELECT
        c.customer_sk,
        MAX(d.date_value) AS last_order_date
    FROM warehouse.fact_sales f
    JOIN warehouse.dim_customer c
        ON f.customer_sk = c.customer_sk
    JOIN warehouse.dim_date d
        ON f.date_key = d.date_key
    GROUP BY c.customer_sk
)
SELECT
    CASE
        WHEN last_order_date < CURRENT_DATE - INTERVAL '60 days'
            THEN 'Churned'
        ELSE 'Active'
    END AS customer_status,
    COUNT(*) AS customer_count
FROM last_order
GROUP BY customer_status
ORDER BY customer_status;
