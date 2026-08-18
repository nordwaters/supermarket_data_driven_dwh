import datetime
import json
import random
import sys
import psycopg2  # Драйвер Postgres (уже есть в образе Airflow)

# Настройки подключения к БД внутри сети Docker
DB_PARAMS = {
    "host": "postgres",
    "database": "airflow",
    "user": "airflow",
    "password": "airflow",
    "port": 5432
}

# Справочники для генерации
CATEGORIES = {
    "Выпечка": [("Хлеб Бородинский", 45, 30), ("Багет французский", 60, 40), ("Круассан", 80, 50)],
    "Молочные продукты": [("Молоко 3.2%", 90, 65), ("Кефир", 85, 60), ("Творог 9%", 120, 85)],
    "Мясо и птица": [("Куриное филе кг", 350, 260), ("Фарш говяжий кг", 480, 360), ("Сосиски", 220, 160)],
    "Напитки": [("Кола 1.5л", 110, 70), ("Вода минеральная", 40, 20), ("Сок яблочный", 130, 90)]
}

STORES = [
    ("ST_001", "Перекресток Центр", "Москва", "Гипермаркет"),
    ("ST_002", "Пятерочка у дома", "Казань", "Мини-маркет"),
    ("ST_003", "Магнит Семейный", "Краснодар", "Супермаркет")
]

def populate_dimensions(cursor):
    """Заполнение таблиц измерений базовыми данными, если они пусты"""
    # Заполнение магазинов
    for store_id, name, city, st_type in STORES:
        cursor.execute("""
            INSERT INTO analytics.dim_stores (store_id, store_name, city, store_type)
            VALUES (%s, %s, %s, %s) ON CONFLICT (store_id) DO NOTHING;
        """, (store_id, name, city, st_type))
    
    # Заполнение товаров
    prod_idx = 1
    for category, products in CATEGORIES.items():
        for name, price, cost in products:
            prod_id = f"PRD_{prod_idx:03d}"
            cursor.execute("""
                INSERT INTO analytics.dim_products (product_id, product_name, category, cost_price)
                VALUES (%s, %s, %s, %s) ON CONFLICT (product_id) DO NOTHING;
            """, (prod_id, name, category, cost))
            prod_idx += 1

def generate_mock_sales(days_back=1):
    """Генерация транзакций за N дней назад до сегодняшнего момента"""
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    # Сначала проверяем/наполняем измерения
    populate_dimensions(cursor)
    
    # Собираем список сгенерированных product_id и их цен
    cursor.execute("SELECT product_id, cost_price FROM analytics.dim_products")
    products_db = cursor.fetchall()
    
    # Генерируем продажи
    target_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
    
    # Имитируем от 50 до 150 чеков за день
    num_transactions = random.randint(50, 150)
    
    transactions = []
    for i in range(num_transactions):
        tx_id = f"TX_{target_date.strftime('%Y%m%d')}_{random.randint(100000, 999999)}"
        # Генерируем случайное время внутри дня
        tx_time = target_date.replace(hour=random.randint(8, 22), minute=random.randint(0, 59), second=random.randint(0, 59))
        store = random.choice(STORES)[0]
        
        # В одном чеке может быть от 1 до 4 товаров
        for _ in range(random.randint(1, 4)):
            prod_id, cost_price = random.choice(products_db)
            qty = random.randint(1, 3)
            
            # Розничная цена = себестоимость * случайный наценочный коэффициент
            price_per_item = round(float(cost_price) * random.uniform(1.2, 1.5), 2)
            total_amount = round(qty * price_per_item, 2)
            pay_method = random.choice(["Карта", "Наличные", "СБП"])
            
            transactions.append((
                tx_id, tx_time, store, prod_id, qty, price_per_item, total_amount, pay_method
            ))
            
    # Записываем пачкой в staging layer
    query = """
        INSERT INTO staging.raw_transactions 
        (transaction_id, timestamp, store_id, product_id, quantity, price_per_item, total_amount, payment_method)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(query, transactions)
    
    conn.commit()
    print(f"Успешно сгенерировано и записано {len(transactions)} строк продаж за дату {target_date.date()}")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    # Если передан аргумент, генерируем за N дней назад, иначе за вчера
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    generate_mock_sales(days)
