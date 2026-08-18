-- 1. Создаем изолированные схемы для слоев данных
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

-- 2. Таблица в слое Staging (сюда пишем сырой поток чеков из Python)
CREATE TABLE IF NOT EXISTS staging.raw_transactions (
    transaction_id VARCHAR(50),
    timestamp TIMESTAMP,
    store_id VARCHAR(20),
    product_id VARCHAR(20),
    quantity INT,
    price_per_item NUMERIC(10, 2),
    total_amount NUMERIC(10, 2),
    payment_method VARCHAR(20),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Справочники в слое Analytics (будут наполняться dbt или генератором)
CREATE TABLE IF NOT EXISTS analytics.dim_products (
    product_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(100),
    category VARCHAR(50),
    cost_price NUMERIC(10, 2) -- Себестоимость для расчета маржи
);

CREATE TABLE IF NOT EXISTS analytics.dim_stores (
    store_id VARCHAR(20) PRIMARY KEY,
    store_name VARCHAR(100),
    city VARCHAR(50),
    store_type VARCHAR(20) -- Супермаркет, Мини-маркет, Гипермаркет
);
