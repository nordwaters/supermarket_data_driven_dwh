{{ config(materialized="table") }}

WITH raw_data AS (
    SELECT 
        transaction_id,
        CAST(timestamp AS DATE) as transaction_date,
        store_id,
        product_id,
        quantity,
        price_per_item,
        total_amount,
        payment_method
    FROM staging.raw_transactions
),
products AS (
    SELECT product_id, product_name, category, cost_price FROM analytics.dim_products
)
SELECT 
    r.transaction_date,
    r.store_id,
    p.category as product_category,
    r.payment_method,
    SUM(r.quantity) as total_qty_sold,
    SUM(r.total_amount) as total_revenue,
    SUM(r.quantity * p.cost_price) as total_cost,
    SUM(r.total_amount) - SUM(r.quantity * p.cost_price) as net_profit
FROM raw_data r
JOIN products p ON r.product_id = p.product_id
GROUP BY 1, 2, 3, 4
