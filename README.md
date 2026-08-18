# Система автоматической обработки, хранения и прогнозирования данных о продажах сети супермаркетов

Курсовой проект по дисциплине "Data Engineering". Реализация отказоустойчивого, масштабируемого конвейера данных по методологии **ELT (Extract-Load-Transform)** на стеке **Modern Data Stack (MDS)**.

Проект развернут локально в изолированном контейнеризированном окружении под управлением Linux Mint и реализует сквозной процесс: от генерации сырых транзакций до построения аналитических витрин, Data-Driven прогнозирования и DevOps-мониторинга.

---

## Архитектура системы и Стек технологий

Проект объединяет современные индустриальные инструменты обработки данных:

*   **Оркестрация и Управление**: `Apache Airflow 2.7.1` — координирует расписание конвейера, управляет зависимостями задач и перезапускает шаги при сбоях.
*   **Хранилище данных (DWH)**: `PostgreSQL 15 (Alpine)` — реляционное хранилище, логически разделенное на изолированные слои данных (`staging` и `analytics`).
*   **Трансформация данных**: `dbt (Data Build Tool) 1.7.3` — T-этап конвейера. Выполняет очистку, типизацию, денормализацию и сборку витрин.
*   **Бизнес-аналитика (BI)**: `Metabase` — слой визуализации KPI, построение интерактивных дашбордов для менеджмента.
*   **Прогнозирование (ML-компонент)**: `Python 3 (psycopg2-binary)` — математический модуль расчета трендов и прогнозных показателей продаж на 7 дней вперед.
*   **Инфраструктурный мониторинг**: `Prometheus` + `Grafana` + `cAdvisor` + `Node Exporter` — DevOps-стек для контроля производительности контейнеров и хост-системы в реальном времени.

---

## Структура Хранилища Данных (DWH Layers)

### 1. Слой Staging (`staging.raw_transactions`)
Сюда сбрасывается сырой поток чеков из супермаркетов в неизменном виде.
*   `transaction_id` (VARCHAR) — Уникальный идентификатор чека.
*   `timestamp` (TIMESTAMP) — Дата и время совершения покупки.
*   `store_id` (VARCHAR) — Идентификатор магазина (Гипермаркет, Супермаркет, Мини-маркет).
*   `product_id` (VARCHAR) — Идентификатор товара.
*   `quantity` (INT) — Количество позиций в чеке.
*   `price_per_item` (NUMERIC) — Розничная цена за единицу товара.
*   `total_amount` (NUMERIC) — Итоговая сумма по позиции.
*   `payment_method` (VARCHAR) — Способ оплаты (Карта, Наличные, СБП).

### 2. Слой Analytics (Справочники и Витрины dbt)
*   `analytics.dim_products` — Измерение товаров (Имя, категория, закупочная себестоимость `cost_price`).
*   `analytics.dim_stores` — Измерение магазинов (Название, город, формат точки).
*   **`analytics.mart_daily_sales` (Витрина dbt)** — Агрегированные исторические продажи. Рассчитывает общую выручку, себестоимость и ключевой показатель — чистую маржу бизнеса (`net_profit = total_amount - cost_price * qty`).
*   **`analytics.fact_sales_forecast` (Витрина прогнозов)** — Таблица с рассчитанными Data-Driven прогнозами выручки по категориям товаров на 7 дней вперед с учетом волатильности рынка (±7%).

---

## Описание Конвейера Данных (Data Pipeline)

Конвейер запускается ежедневно в Apache Airflow (DAG: `supermarket_sales_pipeline`) и состоит из трех последовательных стадий:

1.  **Stage 1: Ingestion (`generate_and_load_sales`)**: Python-скрипт имитирует работу касс, генерируя реалистичные продажи за прошедшие сутки, учитывая повышенный спрос в выходные дни, и осуществляет инжест в слой `staging`.
2.  **Stage 2: Transformation (`run_dbt_transformations`)**: Контейнер dbt подключается к DWH, валидирует данные, связывает факты со справочниками измерений по внешним ключам и обновляет физическую таблицу витрины `mart_daily_sales`.
3.  **Stage 3: Forecasting (`run_ml_forecasting`)**: Python-модуль считывает исторические средние показатели из dbt-витрины, применяет алгоритм скользящего среднего для симуляции трендов и сохраняет прогноз в таблицу `fact_sales_forecast`.

---

## Инструкция по локальному запуску

Весь проект полностью автоматизирован и поднимается одной командой.

### 1. Клонирование и запуск основного стека:
```bash
git clone git@github.com:nordwaters/supermarket_data_driven_dwh.git
cd supermarket_data_driven_dwh
docker-compose up -d
```

### 2. Запуск компонентов мониторинга:
Для изоляции от системных портов Linux Mint, агенты мониторинга и Grafana запускаются прямыми командами в общую сеть:
```bash
# Запуск Node Exporter (сбор метрик железа)
docker run -d --name monitor_node_exporter --network supermarket_dwh_project_default --network-alias node_exporter -p 9100:9100 --pid="host" -v "/:/host:ro,rslave" prom/node-exporter:latest --path.rootfs=/host

# Запуск cAdvisor (сбор метрик контейнеров Docker)
docker run -d --name monitor_cadvisor --network supermarket_dwh_project_default --network-alias cadvisor -p 8082:8080 --volume=/:/rootfs:ro --volume=/var/run:/var/run:ro --volume=/sys:/sys:ro --volume=/var/lib/docker/:/var/lib/docker:ro --volume=/sys/fs/cgroup:/sys/fs/cgroup:ro --privileged --device=/dev/kmsg gcr.io/cadvisor/cadvisor:v0.49.1

# Запуск Grafana (Визуализация метрик)
docker run -d --name monitor_grafana --network supermarket_dwh_project_default -p 8085:3000 -e "GF_SECURITY_ADMIN_USER=admin" -e "GF_SECURITY_ADMIN_PASSWORD=admin" -v \$(pwd)/grafana/provisioning:/etc/grafana/provisioning grafana/grafana:latest
```

### 3. Точки доступа к веб-интерфейсам:
*   **Apache Airflow**: [http://localhost:8080](http://localhost:8080) (Логин: `admin` / Пароль: `admin`)
*   **Metabase BI**: [http://localhost:3030](http://localhost:3030) (Бизнес-дашборды исторических продаж и прогнозов)
*   **Grafana**: [http://localhost:8085](http://localhost:8085) (DevOps-мониторинг инфраструктуры, ID дашборда: `10619`)
*   **Prometheus**: [http://localhost:9090](http://localhost:9090) (Статус сбора метрик `/targets`)
