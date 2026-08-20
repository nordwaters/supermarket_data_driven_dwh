#!/usr/bin/env fish
docker-compose down --remove-orphans
docker rm -f monitor_node_exporter monitor_cadvisor monitor_grafana air_webserver air_scheduler 2>/dev/null
echo "🛑 ВСЕ КОМПОНЕНТЫ УСПЕШНО ОСТАНОВЛЕНЫ!"
