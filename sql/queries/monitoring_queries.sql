-- sql/queries/monitoring_queries.sql
-- Monitoring and Performance Queries for Pipeline Health Check
-- ============================================
-- STAGING SCHEMA MONITORING
-- ============================================
-- Check staging table row counts and freshness
SELECT 
    'staging' as schema_name,
    'customers' as table_name,
    COUNT(*) as row_count,
    MAX(load_timestamp) as last_loaded,
    CURRENT_TIMESTAMP - MAX(load_timestamp) as data_age
FROM staging.customers
UNION ALL
SELECT 'staging', 'products', COUNT(*), MAX(load_timestamp), CURRENT_TIMESTAMP - MAX(load_timestamp)
FROM staging.products
UNION ALL
SELECT 'staging', 'transactions', COUNT(*), MAX(load_timestamp), CURRENT_TIMESTAMP - MAX(load_timestamp)
FROM staging.transactions
UNION ALL
SELECT 'staging', 'transaction_items', COUNT(*), MAX(load_timestamp), CURRENT_TIMESTAMP - MAX(load_timestamp)
FROM staging.transaction_items;
-- ============================================
-- PRODUCTION SCHEMA MONITORING
-- ============================================
-- Check production table row counts and update frequency
SELECT 
    'production' as schema_name,
    'customers' as table_name,
    COUNT(*) as row_count,
    MAX(updated_at) as last_updated,
    CURRENT_TIMESTAMP - MAX(updated_at) as time_since_update
FROM production.customers
UNION ALL
SELECT 'production', 'products', COUNT(*), MAX(updated_at), CURRENT_TIMESTAMP - MAX(updated_at)
FROM production.products
UNION ALL
SELECT 'production', 'transactions', COUNT(*), MAX(updated_at), CURRENT_TIMESTAMP - MAX(updated_at)
FROM production.transactions
UNION ALL
SELECT 'production', 'transaction_items', COUNT(*), MAX(updated_at), CURRENT_TIMESTAMP - MAX(updated_at)
FROM production.transaction_items;
-- ============================================
-- WAREHOUSE SCHEMA MONITORING
-- ============================================
-- Check warehouse dimension and fact table sizes
SELECT 
    'warehouse' as schema_name,
    'dim_customers' as table_name,
    COUNT(*) as row_count,
    COUNT(DISTINCT customer_id) as unique_customers,
    SUM(CASE WHEN is_current = TRUE THEN 1 ELSE 0 END) as current_records
FROM warehouse.dim_customers
UNION ALL
SELECT 'warehouse', 'dim_products', COUNT(*), COUNT(DISTINCT product_id),
    SUM(CASE WHEN is_current = TRUE THEN 1 ELSE 0 END)
FROM warehouse.dim_products
UNION ALL
SELECT 'warehouse', 'dim_date', COUNT(*), NULL,
    COUNT(*)
FROM warehouse.dim_date
UNION ALL
SELECT 'warehouse', 'fact_sales', COUNT(*), NULL,
    COUNT(*)
FROM warehouse.fact_sales
UNION ALL
SELECT 'warehouse', 'agg_daily_sales', COUNT(*), NULL,
    COUNT(*)
FROM warehouse.agg_daily_sales;
-- ============================================
-- DATA INTEGRITY MONITORING
-- ============================================
-- Check for NULL values in critical columns (Production)
SELECT 
    'production.customers' as table_name,
    'email' as column_name,
    COUNT(*) as null_count,
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM production.customers)), 2) as null_percentage
FROM production.customers
WHERE email IS NULL
UNION ALL
SELECT 'production.customers', 'first_name', COUNT(*),
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM production.customers)), 2)
FROM production.customers
WHERE first_name IS NULL
UNION ALL
SELECT 'production.products', 'price', COUNT(*),
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM production.products)), 2)
FROM production.products
WHERE price IS NULL
UNION ALL
SELECT 'production.transactions', 'total_amount', COUNT(*),
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM production.transactions)), 2)
FROM production.transactions
WHERE total_amount IS NULL;
-- Check for duplicate keys
SELECT 
    'production.customers' as table_name,
    'customer_id' as column_name,
    COUNT(DISTINCT customer_id) as unique_values,
    COUNT(*) as total_rows,
    COUNT(*) - COUNT(DISTINCT customer_id) as duplicate_count
FROM production.customers
UNION ALL
SELECT 'production.products', 'product_id', COUNT(DISTINCT product_id), COUNT(*),
    COUNT(*) - COUNT(DISTINCT product_id)
FROM production.products
UNION ALL
SELECT 'production.transactions', 'transaction_id', COUNT(DISTINCT transaction_id), COUNT(*),
    COUNT(*) - COUNT(DISTINCT transaction_id)
FROM production.transactions;
-- ============================================
-- REFERENTIAL INTEGRITY MONITORING
-- ============================================
-- Check for orphaned foreign key references
SELECT 
    'Orphaned Transactions' as issue_type,
    COUNT(*) as orphaned_count,
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM production.transactions)), 2) as percentage_of_total
FROM production.transactions t
WHERE NOT EXISTS (
    SELECT 1 FROM production.customers c WHERE c.customer_id = t.customer_id
)
UNION ALL
SELECT 'Orphaned Transaction Items (Products)',
    COUNT(*),
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM production.transaction_items)), 2)
FROM production.transaction_items ti
WHERE NOT EXISTS (
    SELECT 1 FROM production.products p WHERE p.product_id = ti.product_id
)
UNION ALL
SELECT 'Orphaned Transaction Items (Transactions)',
    COUNT(*),
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM production.transaction_items)), 2)
FROM production.transaction_items ti
WHERE NOT EXISTS (
    SELECT 1 FROM production.transactions t WHERE t.transaction_id = ti.transaction_id
);
-- ============================================
-- WAREHOUSE DATA QUALITY MONITORING
-- ============================================
-- Check SCD Type 2 compliance (dim_customers)
SELECT 
    COUNT(*) as total_records,
    SUM(CASE WHEN is_current = TRUE THEN 1 ELSE 0 END) as current_records,
    SUM(CASE WHEN is_current = FALSE THEN 1 ELSE 0 END) as historical_records,
    COUNT(DISTINCT customer_id) as unique_customers
FROM warehouse.dim_customers;
-- Check for missing dimension records in fact table
SELECT 
    'Missing Customer Dimension' as issue_type,
    COUNT(*) as missing_count
FROM warehouse.fact_sales fs
WHERE NOT EXISTS (
    SELECT 1 FROM warehouse.dim_customers c WHERE c.customer_key = fs.customer_key
)
UNION ALL
SELECT 'Missing Product Dimension',
    COUNT(*)
FROM warehouse.fact_sales fs
WHERE NOT EXISTS (
    SELECT 1 FROM warehouse.dim_products p WHERE p.product_key = fs.product_key
)
UNION ALL
SELECT 'Missing Date Dimension',
    COUNT(*)
FROM warehouse.fact_sales fs
WHERE NOT EXISTS (
    SELECT 1 FROM warehouse.dim_date d WHERE d.date_key = fs.date_key
);
-- ============================================
-- PERFORMANCE MONITORING
-- ============================================
-- Check table sizes and growth
SELECT 
    schema_name,
    table_name,
    pg_size_pretty(pg_total_relation_size(quote_ident(schema_name) || '.' || quote_ident(table_name))::bigint) as table_size,
    row_count,
    CASE 
        WHEN row_count > 0 THEN pg_total_relation_size(quote_ident(schema_name) || '.' || quote_ident(table_name))::bigint / row_count
        ELSE 0
    END as bytes_per_row
FROM (
    SELECT 'production' as schema_name, 'customers' as table_name, COUNT(*) as row_count FROM production.customers
    UNION ALL
    SELECT 'production', 'products', COUNT(*) FROM production.products
    UNION ALL
    SELECT 'production', 'transactions', COUNT(*) FROM production.transactions
    UNION ALL
    SELECT 'production', 'transaction_items', COUNT(*) FROM production.transaction_items
    UNION ALL
    SELECT 'warehouse', 'fact_sales', COUNT(*) FROM warehouse.fact_sales
) t
ORDER BY table_size DESC;
-- ============================================
-- PIPELINE EXECUTION MONITORING
-- ============================================
-- Check staging vs production row counts (Data Loading Validation)
SELECT 
    'customers' as table_name,
    (SELECT COUNT(*) FROM staging.customers) as staging_count,
    (SELECT COUNT(*) FROM production.customers) as production_count,
    (SELECT COUNT(*) FROM staging.customers) - (SELECT COUNT(*) FROM production.customers) as filtered_out
UNION ALL
SELECT 'products',
    (SELECT COUNT(*) FROM staging.products),
    (SELECT COUNT(*) FROM production.products),
    (SELECT COUNT(*) FROM staging.products) - (SELECT COUNT(*) FROM production.products)
UNION ALL
SELECT 'transactions',
    (SELECT COUNT(*) FROM staging.transactions),
    (SELECT COUNT(*) FROM production.transactions),
    (SELECT COUNT(*) FROM staging.transactions) - (SELECT COUNT(*) FROM production.transactions)
UNION ALL
SELECT 'transaction_items',
    (SELECT COUNT(*) FROM staging.transaction_items),
    (SELECT COUNT(*) FROM production.transaction_items),
    (SELECT COUNT(*) FROM staging.transaction_items) - (SELECT COUNT(*) FROM production.transaction_items);
-- ============================================
-- BUSINESS METRICS MONITORING
-- ============================================
-- Monitor key business metrics from warehouse
SELECT 
    'Total Customers' as metric,
    COUNT(DISTINCT customer_id)::TEXT as value
FROM warehouse.dim_customers
WHERE is_current = TRUE
UNION ALL
SELECT 'Total Products',
    COUNT(DISTINCT product_id)::TEXT
FROM warehouse.dim_products
WHERE is_current = TRUE
UNION ALL
SELECT 'Total Sales Transactions',
    COUNT(DISTINCT transaction_id)::TEXT
FROM warehouse.fact_sales
UNION ALL
SELECT 'Total Revenue',
    ROUND(SUM(line_total), 2)::TEXT
FROM warehouse.fact_sales
UNION ALL
SELECT 'Average Transaction Value',
    ROUND(AVG(line_total), 2)::TEXT
FROM warehouse.fact_sales
UNION ALL
SELECT 'Total Items Sold',
    SUM(quantity)::TEXT
FROM warehouse.fact_sales;
-- ============================================
-- SCHEMA HEALTH SUMMARY
-- ============================================
-- Comprehensive health check summary
SELECT 
    'Staging' as schema_check,
    COUNT(CASE WHEN c > 0 THEN 1 END) as healthy_tables,
    COUNT(CASE WHEN c = 0 THEN 1 END) as empty_tables,
    SUM(c) as total_rows
FROM (
    SELECT COUNT(*) as c FROM staging.customers
    UNION ALL
    SELECT COUNT(*) FROM staging.products
    UNION ALL
    SELECT COUNT(*) FROM staging.transactions
    UNION ALL
    SELECT COUNT(*) FROM staging.transaction_items
) staging_counts
UNION ALL
SELECT 'Production',
    COUNT(CASE WHEN c > 0 THEN 1 END),
    COUNT(CASE WHEN c = 0 THEN 1 END),
    SUM(c)
FROM (
    SELECT COUNT(*) as c FROM production.customers
    UNION ALL
    SELECT COUNT(*) FROM production.products
    UNION ALL
    SELECT COUNT(*) FROM production.transactions
    UNION ALL
    SELECT COUNT(*) FROM production.transaction_items
) production_counts
UNION ALL
SELECT 'Warehouse',
    5,
    0,
    (SELECT COUNT(*) FROM warehouse.fact_sales)
FROM warehouse.fact_sales LIMIT 1;
