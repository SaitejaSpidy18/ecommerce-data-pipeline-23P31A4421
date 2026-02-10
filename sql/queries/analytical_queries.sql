-- sql/queries/analytical_queries.sql
-- Analytical Queries for Business Intelligence (Warehouse Schema)
-- ============================================
-- 1. SALES OVERVIEW BY DATE
-- ============================================
-- Query: Daily sales trends, transaction counts, and customer activity
SELECT 
    d.date_value,
    d.year,
    d.month,
    d.day_of_week,
    COUNT(DISTINCT fs.transaction_id) as num_transactions,
    COUNT(DISTINCT fs.customer_key) as num_customers,
    SUM(fs.line_total) as total_sales,
    SUM(fs.quantity) as total_quantity,
    ROUND(AVG(fs.line_total), 2) as avg_transaction_value,
    ROUND(SUM(fs.line_total) / NULLIF(COUNT(DISTINCT fs.transaction_id), 0), 2) as avg_order_value
FROM warehouse.fact_sales fs
JOIN warehouse.dim_date d ON fs.date_key = d.date_key
GROUP BY d.date_value, d.year, d.month, d.day_of_week
ORDER BY d.date_value DESC;
-- ============================================
-- 2. TOP 10 PRODUCTS BY REVENUE
-- ============================================
-- Query: Best-performing products by total revenue
SELECT 
    p.product_key,
    p.product_id,
    p.product_name,
    p.category,
    ROUND(p.price, 2) as product_price,
    SUM(fs.quantity) as total_quantity_sold,
    COUNT(DISTINCT fs.transaction_id) as num_sales,
    ROUND(SUM(fs.line_total), 2) as total_revenue,
    ROUND(AVG(fs.line_total), 2) as avg_sale_value,
    ROUND((SUM(fs.line_total) / (SELECT SUM(line_total) FROM warehouse.fact_sales)) * 100, 2) as revenue_percentage
FROM warehouse.fact_sales fs
JOIN warehouse.dim_products p ON fs.product_key = p.product_key
WHERE p.is_current = TRUE
GROUP BY p.product_key, p.product_id, p.product_name, p.category, p.price
ORDER BY total_revenue DESC
LIMIT 10;
-- ============================================
-- 3. CUSTOMER SEGMENTATION BY SPENDING
-- ============================================
-- Query: Segment customers into tiers based on lifetime value
WITH customer_spending AS (
    SELECT 
        c.customer_key,
        c.customer_id,
        c.first_name,
        c.last_name,
        c.city,
        SUM(fs.line_total) as lifetime_value,
        COUNT(DISTINCT fs.transaction_id) as purchase_count,
        MAX(d.date_value) as last_purchase_date,
        ROUND(AVG(fs.line_total), 2) as avg_order_value
    FROM warehouse.fact_sales fs
    JOIN warehouse.dim_customers c ON fs.customer_key = c.customer_key
    JOIN warehouse.dim_date d ON fs.date_key = d.date_key
    WHERE c.is_current = TRUE
    GROUP BY c.customer_key, c.customer_id, c.first_name, c.last_name, c.city
)
SELECT 
    customer_key,
    customer_id,
    CONCAT(first_name, ' ', last_name) as customer_name,
    city,
    lifetime_value,
    purchase_count,
    last_purchase_date,
    avg_order_value,
    CASE 
        WHEN lifetime_value >= (SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY lifetime_value) FROM customer_spending) THEN 'Premium'
        WHEN lifetime_value >= (SELECT PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY lifetime_value) FROM customer_spending) THEN 'Gold'
        WHEN lifetime_value >= (SELECT PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY lifetime_value) FROM customer_spending) THEN 'Silver'
        ELSE 'Bronze'
    END as customer_segment
FROM customer_spending
ORDER BY lifetime_value DESC;
-- ============================================
-- 4. SALES BY PAYMENT METHOD
-- ============================================
-- Query: Revenue and transaction analysis by payment method
SELECT 
    pm.payment_method_name,
    COUNT(DISTINCT fs.transaction_id) as num_transactions,
    COUNT(DISTINCT fs.customer_key) as num_customers,
    SUM(fs.quantity) as total_items_sold,
    ROUND(SUM(fs.line_total), 2) as total_revenue,
    ROUND(AVG(fs.line_total), 2) as avg_transaction_value,
    ROUND((SUM(fs.line_total) / (SELECT SUM(line_total) FROM warehouse.fact_sales)) * 100, 2) as revenue_share,
    ROUND(SUM(fs.line_total) / COUNT(DISTINCT fs.transaction_id), 2) as revenue_per_transaction
FROM warehouse.fact_sales fs
JOIN warehouse.dim_payment_method pm ON fs.payment_method_key = pm.payment_method_key
GROUP BY pm.payment_method_name
ORDER BY total_revenue DESC;
-- ============================================
-- 5. MONTHLY SALES TREND
-- ============================================
-- Query: Month-over-month sales trend analysis
SELECT 
    d.year,
    d.month,
    TO_CHAR(d.date_value, 'Mon-YYYY') as month_year,
    COUNT(DISTINCT fs.transaction_id) as num_transactions,
    COUNT(DISTINCT fs.customer_key) as num_customers,
    SUM(fs.quantity) as total_quantity,
    ROUND(SUM(fs.line_total), 2) as total_sales,
    ROUND(AVG(fs.line_total), 2) as avg_transaction_value,
    ROUND(
        (SUM(fs.line_total) / LAG(SUM(fs.line_total)) OVER (ORDER BY d.year, d.month) - 1) * 100,
        2
    ) as mom_growth_percentage
FROM warehouse.fact_sales fs
JOIN warehouse.dim_date d ON fs.date_key = d.date_key
GROUP BY d.year, d.month, TO_CHAR(d.date_value, 'Mon-YYYY')
ORDER BY d.year, d.month;
-- ============================================
-- 6. PRODUCT CATEGORY PERFORMANCE
-- ============================================
-- Query: Revenue and unit analysis by product category
SELECT 
    p.category,
    COUNT(DISTINCT p.product_key) as num_products,
    COUNT(DISTINCT fs.transaction_id) as num_transactions,
    COUNT(DISTINCT fs.customer_key) as num_customers,
    SUM(fs.quantity) as total_units_sold,
    ROUND(SUM(fs.line_total), 2) as total_revenue,
    ROUND(AVG(fs.line_total), 2) as avg_transaction_value,
    ROUND(SUM(fs.line_total) / SUM(fs.quantity), 2) as revenue_per_unit,
    ROUND((SUM(fs.line_total) / (SELECT SUM(line_total) FROM warehouse.fact_sales)) * 100, 2) as revenue_percentage
FROM warehouse.fact_sales fs
JOIN warehouse.dim_products p ON fs.product_key = p.product_key
WHERE p.is_current = TRUE
GROUP BY p.category
ORDER BY total_revenue DESC;
-- ============================================
-- 7. TRANSACTION STATUS ANALYSIS
-- ============================================
-- Query: Success rate and revenue impact of transaction statuses
SELECT 
    ts.status_name,
    COUNT(DISTINCT fs.transaction_id) as num_transactions,
    COUNT(DISTINCT fs.customer_key) as num_customers,
    SUM(fs.quantity) as total_quantity,
    ROUND(SUM(fs.line_total), 2) as total_amount,
    ROUND(
        (COUNT(DISTINCT fs.transaction_id) / (SELECT COUNT(DISTINCT transaction_id) FROM warehouse.fact_sales)) * 100,
        2
    ) as transaction_percentage,
    ROUND(
        (SUM(fs.line_total) / (SELECT SUM(line_total) FROM warehouse.fact_sales)) * 100,
        2
    ) as revenue_percentage,
    ROUND(AVG(fs.line_total), 2) as avg_transaction_value
FROM warehouse.fact_sales fs
JOIN warehouse.dim_transaction_status ts ON fs.status_key = ts.status_key
GROUP BY ts.status_name
ORDER BY num_transactions DESC;
-- ============================================
-- 8. CUSTOMER ACQUISITION AND RETENTION
-- ============================================
-- Query: New customer metrics and retention indicators
WITH customer_dates AS (
    SELECT 
        c.customer_key,
        c.customer_id,
        c.signup_date,
        EXTRACT(YEAR FROM c.signup_date) as signup_year,
        EXTRACT(MONTH FROM c.signup_date) as signup_month,
        MIN(d.date_value) as first_purchase_date,
        MAX(d.date_value) as last_purchase_date,
        COUNT(DISTINCT fs.transaction_id) as total_purchases,
        SUM(fs.line_total) as lifetime_value
    FROM warehouse.dim_customers c
    LEFT JOIN warehouse.fact_sales fs ON c.customer_key = fs.customer_key
    LEFT JOIN warehouse.dim_date d ON fs.date_key = d.date_key
    WHERE c.is_current = TRUE
    GROUP BY c.customer_key, c.customer_id, c.signup_date
)
SELECT 
    signup_year,
    signup_month,
    TO_CHAR(TO_DATE(CONCAT(signup_year, '-', signup_month, '-01'), 'YYYY-MM-DD'), 'Mon-YYYY') as signup_month_year,
    COUNT(*) as new_customers,
    ROUND(AVG(lifetime_value), 2) as avg_lifetime_value,
    COUNT(CASE WHEN total_purchases > 0 THEN 1 END) as customers_with_purchases,
    ROUND(
        (COUNT(CASE WHEN total_purchases > 0 THEN 1 END)::NUMERIC / COUNT(*)) * 100,
        2
    ) as conversion_rate
FROM customer_dates
GROUP BY signup_year, signup_month
ORDER BY signup_year DESC, signup_month DESC;
-- ============================================
-- 9. PRODUCT PERFORMANCE BY CUSTOMER SEGMENT
-- ============================================
-- Query: Which products perform best in different customer segments
WITH customer_segments AS (
    SELECT 
        c.customer_key,
        CASE 
            WHEN SUM(fs.line_total) >= 50000 THEN 'High-Value'
            WHEN SUM(fs.line_total) >= 10000 THEN 'Medium-Value'
            ELSE 'Low-Value'
        END as segment
    FROM warehouse.dim_customers c
    LEFT JOIN warehouse.fact_sales fs ON c.customer_key = fs.customer_key
    WHERE c.is_current = TRUE
    GROUP BY c.customer_key
)
SELECT 
    cs.segment,
    p.product_name,
    p.category,
    COUNT(DISTINCT fs.transaction_id) as purchase_count,
    SUM(fs.quantity) as total_quantity,
    ROUND(SUM(fs.line_total), 2) as total_revenue,
    ROUND(AVG(fs.quantity), 2) as avg_qty_per_transaction
FROM customer_segments cs
JOIN warehouse.fact_sales fs ON cs.customer_key = fs.customer_key
JOIN warehouse.dim_products p ON fs.product_key = p.product_key
WHERE p.is_current = TRUE
GROUP BY cs.segment, p.product_name, p.category
ORDER BY cs.segment, total_revenue DESC;
-- ============================================
-- 10. GEOGRAPHIC SALES ANALYSIS
-- ============================================
-- Query: Sales performance by city and state
SELECT 
    c.state,
    c.city,
    COUNT(DISTINCT c.customer_key) as num_customers,
    COUNT(DISTINCT fs.transaction_id) as num_transactions,
    SUM(fs.quantity) as total_quantity,
    ROUND(SUM(fs.line_total), 2) as total_revenue,
    ROUND(AVG(fs.line_total), 2) as avg_transaction_value,
    ROUND(SUM(fs.line_total) / COUNT(DISTINCT c.customer_key), 2) as revenue_per_customer,
    ROUND(
        (SUM(fs.line_total) / (SELECT SUM(line_total) FROM warehouse.fact_sales)) * 100,
        2
    ) as revenue_percentage
FROM warehouse.fact_sales fs
JOIN warehouse.dim_customers c ON fs.customer_key = c.customer_key
WHERE c.is_current = TRUE
GROUP BY c.state, c.city
ORDER BY total_revenue DESC;
