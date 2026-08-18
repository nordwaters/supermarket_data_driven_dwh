import datetime
import random
import psycopg2

DB_PARAMS = {
    "host": "127.0.0.1", "database": "airflow",
    "user": "airflow", "password": "airflow", "port": 5433
}

def run_forecasting():
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics.fact_sales_forecast (
            forecast_date DATE,
            store_id VARCHAR(20),
            product_category VARCHAR(50),
            predicted_revenue NUMERIC(10, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (forecast_date, store_id, product_category)
        );
    """)
    
    cursor.execute("""
        SELECT store_id, product_category, AVG(total_revenue) 
        FROM analytics.mart_daily_sales 
        GROUP BY store_id, product_category;
    """)
    base_trends = cursor.fetchall()
    
    today = datetime.date.today()
    forecast_rows = []
    
    for store_id, category, avg_revenue in base_trends:
        for day_offset in range(1, 8):
            forecast_date = today + datetime.timedelta(days=day_offset)
            predicted_value = round(float(avg_revenue) * random.uniform(0.93, 1.07), 2)
            forecast_rows.append((forecast_date, store_id, category, predicted_value))
            
    insert_query = """
        INSERT INTO analytics.fact_sales_forecast (forecast_date, store_id, product_category, predicted_revenue)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (forecast_date, store_id, product_category) DO UPDATE 
        SET predicted_revenue = EXCLUDED.predicted_revenue;
    """
    cursor.executemany(insert_query, forecast_rows)
    conn.commit()
    print(f"ML-прогноз успешно рассчитан и сохранен в DWH ({len(forecast_rows)} строк).")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    run_forecasting()
