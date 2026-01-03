SELECT
    f.payment_method,
    COUNT(DISTINCT f.transaction_id) AS transaction_count,
    SUM(f.total_amount) AS total_revenue,
    100.0 * SUM(f.total_amount) / SUM(SUM(f.total_amount)) OVER () AS revenue_share_pct
FROM warehouse.fact_sales f
GROUP BY f.payment_method
ORDER BY total_revenue DESC;
