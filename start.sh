#!/usr/bin/env fish
echo "1. Очистка старых зависших контейнеров..."
docker rm -f monitor_node_exporter monitor_cadvisor monitor_grafana air_webserver air_scheduler 2>/dev/null

echo "2. Запуск основного ядра базы данных и BI (Docker Compose)..."
docker-compose up -d --remove-orphans

echo "3. Запуск Apache Airflow (Webserver и Scheduler)..."
docker run -d --name air_webserver --network supermarket_dwh_project_default -p 8080:8080 -e AIRFLOW__CORE__EXECUTOR=LocalExecutor -e AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow -e AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true -e AIRFLOW__CORE__LOAD_EXAMPLES=false -e _PIP_ADDITIONAL_REQUIREMENTS=dbt-postgres -v /home/auger/supermarket_dwh_project/dags:/opt/airflow/dags -v /home/auger/supermarket_dwh_project/scripts:/opt/airflow/scripts -v /home/auger/supermarket_dwh_project/dbt:/opt/airflow/dbt apache/airflow:2.7.1 webserver

docker run -d --name air_scheduler --network supermarket_dwh_project_default -e AIRFLOW__CORE__EXECUTOR=LocalExecutor -e AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow -e AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true -e AIRFLOW__CORE__LOAD_EXAMPLES=false -e _PIP_ADDITIONAL_REQUIREMENTS=dbt-postgres -v /home/auger/supermarket_dwh_project/dags:/opt/airflow/dags -v /home/auger/supermarket_dwh_project/scripts:/opt/airflow/scripts -v /home/auger/supermarket_dwh_project/dbt:/opt/airflow/dbt apache/airflow:2.7.1 scheduler

echo "4. Запуск DevOps-компонентов мониторинга..."
docker run -d --name monitor_node_exporter --network supermarket_dwh_project_default --network-alias node_exporter -p 9100:9100 --pid=host -v /:/host:ro,rslave prom/node-exporter:latest --path.rootfs=/host
docker run -d --name monitor_cadvisor --network supermarket_dwh_project_default --network-alias cadvisor -p 8082:8080 --volume=/:/rootfs:ro --volume=/var/run:/var/run:ro --volume=/sys:/sys:ro --volume=/var/lib/docker/:/var/lib/docker:ro --volume=/sys/fs/cgroup:/sys/fs/cgroup:ro --privileged --device=/dev/kmsg gcr.io/cadvisor/cadvisor:v0.49.1
docker run -d --name monitor_grafana --network supermarket_dwh_project_default -p 8085:3000 -e GF_SECURITY_ADMIN_USER=admin -e GF_SECURITY_ADMIN_PASSWORD=admin -v /home/auger/supermarket_dwh_project/grafana/provisioning:/etc/grafana/provisioning grafana/grafana:latest

echo "🚀 ВСЕ КОМПОНЕНТЫ УСПЕШНО ЗАПУЩЕНЫ!"
