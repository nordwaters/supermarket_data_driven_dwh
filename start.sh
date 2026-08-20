#!/usr/bin/env fish
echo "1. Глубокая очистка абсолютно всех контейнеров проекта..."
docker rm -f dwh_postgres bi_metabase monitor_prometheus monitor_node_exporter monitor_cadvisor monitor_grafana air_webserver air_scheduler 2>/dev/null

echo "2. Запуск Хранилища Данных (PostgreSQL 15)..."
docker run -d --name dwh_postgres --network supermarket_dwh_project_default --network-alias postgres -p 5433:5432 -v postgres_data:/var/lib/postgresql/data -e POSTGRES_USER=airflow -e POSTGRES_PASSWORD=airflow -e POSTGRES_DB=airflow postgres:15-alpine

echo "3. Ожидание запуска СУБД..."
sleep 5

echo "4. Автоматическая инициализация и миграция базы метаданных Airflow..."
docker run --rm --network supermarket_dwh_project_default -e AIRFLOW__CORE__EXECUTOR=LocalExecutor -e AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow apache/airflow:2.7.1 db init 2>/dev/null

echo "5. Создание дефолтного пользователя admin (игнорируется если уже создан)..."
docker run --rm --network supermarket_dwh_project_default -e AIRFLOW__CORE__EXECUTOR=LocalExecutor -e AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow apache/airflow:2.7.1 users create --username admin --firstname Admin --lastname Admin --role Admin --email admin@example.com --password admin 2>/dev/null

echo "6. Запуск Бизнес-Аналитики (Metabase BI)..."
docker run -d --name bi_metabase --network supermarket_dwh_project_default -p 3030:3000 -v metabase_data:/metabase-data metabase/metabase:latest

echo "7. Запуск Сборщика Метрик (Prometheus)..."
docker run -d --name monitor_prometheus --network supermarket_dwh_project_default --network-alias prometheus -p 9090:9090 -v /home/auger/supermarket_dwh_project/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus:latest

echo "8. Запуск Оркестратора Apache Airflow (Webserver)..."
docker run -d --name air_webserver --network supermarket_dwh_project_default -p 8081:8080 -e AIRFLOW__CORE__EXECUTOR=LocalExecutor -e AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow -e AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true -e AIRFLOW__CORE__LOAD_EXAMPLES=false -e _PIP_ADDITIONAL_REQUIREMENTS=dbt-postgres -v /home/auger/supermarket_dwh_project/dags:/opt/airflow/dags -v /home/auger/supermarket_dwh_project/scripts:/opt/airflow/scripts -v /home/auger/supermarket_dwh_project/dbt:/opt/airflow/dbt apache/airflow:2.7.1 webserver

echo "9. Запуск Оркестратора Apache Airflow (Scheduler)..."
docker run -d --name air_scheduler --network supermarket_dwh_project_default -e AIRFLOW__CORE__EXECUTOR=LocalExecutor -e AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow -e AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true -e AIRFLOW__CORE__LOAD_EXAMPLES=false -e _PIP_ADDITIONAL_REQUIREMENTS=dbt-postgres -v /home/auger/supermarket_dwh_project/dags:/opt/airflow/dags -v /home/auger/supermarket_dwh_project/scripts:/opt/airflow/scripts -v /home/auger/supermarket_dwh_project/dbt:/opt/airflow/dbt apache/airflow:2.7.1 scheduler

echo "10. Запуск DevOps-компонентов мониторинга железа и Docker..."
docker run -d --name monitor_node_exporter --network supermarket_dwh_project_default --network-alias node_exporter -p 9100:9100 --pid=host -v /:/host:ro,rslave prom/node-exporter:latest --path.rootfs=/host
docker run -d --name monitor_cadvisor --network supermarket_dwh_project_default --network-alias cadvisor -p 8082:8080 --volume=/:/rootfs:ro --volume=/var/run:/var/run:ro --volume=/sys:/sys:ro --volume=/var/lib/docker/:/var/lib/docker:ro --volume=/sys/fs/cgroup:/sys/fs/cgroup:ro --privileged --device=/dev/kmsg gcr.io/cadvisor/cadvisor:v0.49.1
docker run -d --name monitor_grafana --network supermarket_dwh_project_default -p 8085:3000 -e GF_SECURITY_ADMIN_USER=admin -e GF_SECURITY_ADMIN_PASSWORD=admin -v /home/auger/supermarket_dwh_project/grafana/provisioning:/etc/grafana/provisioning grafana/grafana:latest

echo "🚀 ВСЕ КОМПОНЕНТЫ УСПЕШНО ЗАПУЩЕНЫ!"
