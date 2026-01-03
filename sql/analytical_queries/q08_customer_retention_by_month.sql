WITH first_purchase AS (
    SELECT
        c.customer_sk,
        MIN(d.date_value) AS first_order_date
    FROM warehouse.fact_sales f
    JOIN warehouse.dim_customer c
        ON f.customer_sk = c.customer_sk
    JOIN warehouse.dim_date d
        ON f.date_key = d.date_key
    GROUP BY c.customer_sk
),
orders_by_month AS (
    SELECT
        c.customer_sk,
        DATE_TRUNC('month', d.date_value) AS order_month
    FROM warehouse.fact_sales f
    JOIN warehouse.dim_customer c
        ON f.customer_sk = c.customer_sk
    JOIN warehouse.dim_date d
        ON f.date_key = d.date_key
)
SELECT
    DATE_TRUNC('month', fp.first_order_date) AS cohort_month,
    obm.order_month,
    COUNT(DISTINCT obm.customer_sk) AS retained_customers
FROM first_purchase fp
JOIN orders_by_month obm
    ON fp.customer_sk = obm.customer_sk
GROUP BY cohort_month, obm.order_month
ORDER BY cohort_month, obm.order_month;
