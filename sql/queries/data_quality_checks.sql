-- sql/queries/data_quality_checks.sql
-- Data Quality Check Queries for Staging Schema
-- ============================================
-- COMPLETENESS CHECKS
-- ============================================
-- Check for NULL values in customers table
SELECT 
    'customers' as table_name,
    'customer_id' as column_name,
    COUNT(*) as null_count
FROM staging.customers
WHERE customer_id IS NULL
UNION ALL
SELECT 'customers', 'email', COUNT(*) FROM staging.customers WHERE email IS NULL
UNION ALL
SELECT 'customers', 'first_name', COUNT(*) FROM staging.customers WHERE first_name IS NULL
UNION ALL
SELECT 'customers', 'last_name', COUNT(*) FROM staging.customers WHERE last_name IS NULL
UNION ALL
SELECT 'products', 'product_id', COUNT(*) FROM staging.products WHERE product_id IS NULL
UNION ALL
SELECT 'products', 'product_name', COUNT(*) FROM staging.products WHERE product_name IS NULL
UNION ALL
SELECT 'products', 'price', COUNT(*) FROM staging.products WHERE price IS NULL
UNION ALL
SELECT 'transactions', 'transaction_id', COUNT(*) FROM staging.transactions WHERE transaction_id IS NULL
UNION ALL
SELECT 'transactions', 'customer_id', COUNT(*) FROM staging.transactions WHERE customer_id IS NULL
UNION ALL
SELECT 'transactions', 'transaction_date', COUNT(*) FROM staging.transactions WHERE transaction_date IS NULL
UNION ALL
SELECT 'transactions', 'total_amount', COUNT(*) FROM staging.transactions WHERE total_amount IS NULL
UNION ALL
SELECT 'transaction_items', 'item_id', COUNT(*) FROM staging.transaction_items WHERE item_id IS NULL
UNION ALL
SELECT 'transaction_items', 'transaction_id', COUNT(*) FROM staging.transaction_items WHERE transaction_id IS NULL
UNION ALL
SELECT 'transaction_items', 'product_id', COUNT(*) FROM staging.transaction_items WHERE product_id IS NULL
UNION ALL
SELECT 'transaction_items', 'quantity', COUNT(*) FROM staging.transaction_items WHERE quantity IS NULL;
-- ============================================
-- UNIQUENESS CHECKS
-- ============================================
-- Check for duplicate customer IDs
SELECT 
    'customers' as table_name,
    'customer_id' as column_name,
    customer_id,
    COUNT(*) as duplicate_count
FROM staging.customers
GROUP BY customer_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
-- Check for duplicate product IDs
SELECT 
    'products' as table_name,
    'product_id' as column_name,
    product_id,
    COUNT(*) as duplicate_count
FROM staging.products
GROUP BY product_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
-- Check for duplicate transaction IDs
SELECT 
    'transactions' as table_name,
    'transaction_id' as column_name,
    transaction_id,
    COUNT(*) as duplicate_count
FROM staging.transactions
GROUP BY transaction_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
-- Check for duplicate item IDs
SELECT 
    'transaction_items' as table_name,
    'item_id' as column_name,
    item_id,
    COUNT(*) as duplicate_count
FROM staging.transaction_items
GROUP BY item_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
-- ============================================
-- VALIDITY CHECKS
-- ============================================
-- Check for invalid email formats in customers
SELECT 
    'Invalid Email Format' as issue_type,
    COUNT(*) as count,
    STRING_AGG(DISTINCT email, ', ') as sample_emails
FROM staging.customers
WHERE email NOT LIKE '%@%' OR email IS NULL OR email = '';
-- Check for zero or negative prices in products
SELECT 
    'Invalid Price (<=0)' as issue_type,
    COUNT(*) as count,
    MIN(price) as min_price,
    MAX(price) as max_price
FROM staging.products
WHERE price <= 0;
-- Check for zero or negative quantities in transaction_items
SELECT 
    'Invalid Quantity (<=0)' as issue_type,
    COUNT(*) as count,
    MIN(quantity) as min_quantity,
    MAX(quantity) as max_quantity
FROM staging.transaction_items
WHERE quantity <= 0;
-- Check for zero or negative transaction amounts
SELECT 
    'Invalid Transaction Amount (<=0)' as issue_type,
    COUNT(*) as count,
    MIN(total_amount) as min_amount,
    MAX(total_amount) as max_amount
FROM staging.transactions
WHERE total_amount <= 0;
-- Check for invalid payment methods
SELECT 
    payment_method,
    COUNT(*) as count
FROM staging.transactions
WHERE payment_method NOT IN ('Credit Card', 'Debit Card', 'UPI', 'Net Banking', 'Cash')
GROUP BY payment_method;
-- Check for invalid transaction statuses
SELECT 
    transaction_status,
    COUNT(*) as count
FROM staging.transactions
WHERE transaction_status NOT IN ('Completed', 'Pending', 'Failed')
GROUP BY transaction_status;
-- ============================================
-- CONSISTENCY CHECKS
-- ============================================
-- Check line_total consistency (line_total should equal quantity * unit_price)
SELECT 
    'Line Total Mismatch' as issue_type,
    COUNT(*) as count,
    COUNT(DISTINCT transaction_id) as affected_transactions
FROM staging.transaction_items
WHERE ABS(line_total - (quantity * unit_price)) > 0.01;
-- Show specific mismatches
SELECT 
    item_id,
    transaction_id,
    quantity,
    unit_price,
    line_total,
    (quantity * unit_price) as calculated_total,
    ABS(line_total - (quantity * unit_price)) as difference
FROM staging.transaction_items
WHERE ABS(line_total - (quantity * unit_price)) > 0.01
LIMIT 10;
-- ============================================
-- REFERENTIAL INTEGRITY CHECKS
-- ============================================
-- Check for transactions with non-existent customers
SELECT 
    'Orphaned Customer Reference' as issue_type,
    COUNT(*) as count,
    COUNT(DISTINCT customer_id) as unique_customer_ids
FROM staging.transactions t
WHERE NOT EXISTS (
    SELECT 1 FROM staging.customers c WHERE c.customer_id = t.customer_id
);
-- Show specific orphaned records
SELECT 
    t.transaction_id,
    t.customer_id,
    t.transaction_date
FROM staging.transactions t
WHERE NOT EXISTS (
    SELECT 1 FROM staging.customers c WHERE c.customer_id = t.customer_id
)
LIMIT 10;
-- Check for transaction_items with non-existent products
SELECT 
    'Orphaned Product Reference' as issue_type,
    COUNT(*) as count,
    COUNT(DISTINCT product_id) as unique_product_ids
FROM staging.transaction_items ti
WHERE NOT EXISTS (
    SELECT 1 FROM staging.products p WHERE p.product_id = ti.product_id
);
-- Show specific orphaned records
SELECT 
    ti.item_id,
    ti.product_id,
    ti.transaction_id
FROM staging.transaction_items ti
WHERE NOT EXISTS (
    SELECT 1 FROM staging.products p WHERE p.product_id = ti.product_id
)
LIMIT 10;
-- Check for transaction_items with non-existent transactions
SELECT 
    'Orphaned Transaction Reference' as issue_type,
    COUNT(*) as count,
    COUNT(DISTINCT transaction_id) as unique_transaction_ids
FROM staging.transaction_items ti
WHERE NOT EXISTS (
    SELECT 1 FROM staging.transactions t WHERE t.transaction_id = ti.transaction_id
);
-- Show specific orphaned records
SELECT 
    ti.item_id,
    ti.transaction_id,
    ti.product_id
FROM staging.transaction_items ti
WHERE NOT EXISTS (
    SELECT 1 FROM staging.transactions t WHERE t.transaction_id = ti.transaction_id
)
LIMIT 10;
-- ============================================
-- DATA QUALITY SUMMARY
-- ============================================
-- Overall data quality summary
SELECT 
    'Customers' as entity,
    COUNT(*) as total_records,
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) as null_ids,
    SUM(CASE WHEN email NOT LIKE '%@%' THEN 1 ELSE 0 END) as invalid_emails
FROM staging.customers
UNION ALL
SELECT 
    'Products',
    COUNT(*),
    SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN price <= 0 THEN 1 ELSE 0 END)
FROM staging.products
UNION ALL
SELECT 
    'Transactions',
    COUNT(*),
    SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN total_amount <= 0 THEN 1 ELSE 0 END)
FROM staging.transactions
UNION ALL
SELECT 
    'Transaction Items',
    COUNT(*),
    SUM(CASE WHEN item_id IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN quantity <= 0 THEN 1 ELSE 0 END)
FROM staging.transaction_items;
-- Row counts by table
SELECT 
    'Customers' as table_name,
    COUNT(*) as row_count
FROM staging.customers
UNION ALL
SELECT 'Products', COUNT(*) FROM staging.products
UNION ALL
SELECT 'Transactions', COUNT(*) FROM staging.transactions
UNION ALL
SELECT 'Transaction Items', COUNT(*) FROM staging.transaction_items;
