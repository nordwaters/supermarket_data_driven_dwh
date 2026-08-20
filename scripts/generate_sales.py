import datetime
import random
import sys
import psycopg2

DB_PARAMS = {
    "host": "postgres", "database": "airflow",
    "user": "airflow", "password": "airflow", "port": 5432
}

def populate_dimensions(cursor):
    # Автоматически создаем необходимые схемы данных
    cursor.execute("CREATE SCHEMA IF NOT EXISTS staging;")
    cursor.execute("CREATE SCHEMA IF NOT EXISTS analytics;")
    
    # Создаем измерение магазинов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics.dim_stores (
            store_id VARCHAR(20) PRIMARY KEY,
            store_name VARCHAR(50),
            city VARCHAR(50),
            format VARCHAR(20)
        );
    """)
    
    # Создаем измерение продуктов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics.dim_products (
            product_id VARCHAR(20) PRIMARY KEY,
            product_name VARCHAR(50),
            category VARCHAR(50),
            cost_price NUMERIC(10, 2)
        );
    """)
    
    # Создаем сырую таблицу транзакций вstaging
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging.raw_transactions (
            transaction_id VARCHAR(50),
            timestamp TIMESTAMP,
            store_id VARCHAR(20),
            product_id VARCHAR(20),
            quantity INT,
            price_per_item NUMERIC(10, 2),
            total_amount NUMERIC(10, 2),
            payment_method VARCHAR(20)
        );
    """)

    # Наполняем справочники статичными данными
    stores = [
        ("STR_001", "Гипермаркет Центр", "Минск", "Гипермаркет"),
        ("STR_002", "Супермаркет Запад", "Минск", "Супермаркет"),
        ("STR_003", "Мини-маркет Восток", "Брест", "Мини-маркет")
    ]
    for s in stores:
        cursor.execute("""
            INSERT INTO analytics.dim_stores (store_id, store_name, city, format)
            VALUES (%s, %s, %s, %s) ON CONFLICT (store_id) DO NOTHING;
        """, s)

    products = [
        ("PRD_001", "Хлеб Бородинский", "Выпечка", 1.20),
        ("PRD_002", "Молоко 3.2%", "Молочные продукты", 1.50),
        ("PRD_003", "Кока-Кола 1.5л", "Напитки", 2.00),
        ("PRD_004", "Шоколад Аленка", "Кондитерские изделия", 2.50)
    ]
    for p in products:
        cursor.execute("""
            INSERT INTO analytics.dim_products (product_id, product_name, category, cost_price)
            VALUES (%s, %s, %s, %s) ON CONFLICT (product_id) DO NOTHING;
        """, p)

def generate_mock_sales(days_back=1):
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    populate_dimensions(cursor)
    
    payment_methods = ["Карта", "Наличные", "СБП"]
    products_pool = [
        ("PRD_001", 2.10),
        ("PRD_002", 2.60),
        ("PRD_003", 3.40),
        ("PRD_004", 4.20)
    ]
    stores_pool = ["STR_001", "STR_002", "STR_003"]
    
    start_date = datetime.datetime.now() - datetime.timedelta(days=int(days_back))
    
    records_count = 0
    for day in range(int(days_back)):
        current_date = start_date + datetime.timedelta(days=day)
        
        # Коэффициент выходного дня (в субботу и воскресенье чеков больше)
        is_weekend = current_date.weekday() in [5, 6]
        cheques_to_generate = random.randint(150, 250) if is_weekend else random.randint(80, 130)
        
        for _ in range(cheques_to_generate):
            tx_id = f"TX_{current_date.strftime('%Y%m%d')}_{random.randint(100000, 999999)}"
            store_id = random.choice(stores_pool)
            
            # В одном чеке может быть несколько случайных товаров
            for _ in range(random.randint(1, 4)):
                prod_id, sale_price = random.choice(products_pool)
                qty = random.randint(1, 5)
                total_amount = round(qty * sale_price, 2)
                
                tx_time = current_date.replace(
                    hour=random.randint(8, 22),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )
                
                cursor.execute("""
                    INSERT INTO staging.raw_transactions 
                    (transaction_id, timestamp, store_id, product_id, quantity, price_per_item, total_amount, payment_method)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (tx_id, tx_time, store_id, prod_id, qty, sale_price, total_amount, random.choice(payment_methods)))
                records_count += 1
                
    conn.commit()
    print(f"Успешно сгенерировано и загружено {records_count} строк чеков вstaging слой DWH.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    days = sys.argv[1] if len(sys.argv) > 1 else 30
    generate_mock_sales(days)
