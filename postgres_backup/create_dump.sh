#!/bin/bash
_now=$(date +"%m_%d_%Y at %H.%M.%S")
_file="pg_backup_$_now.bak"
echo "Starting backup to $_file..."
docker exec -it nictiz_webtools_postgres_1 pg_dumpall -U postgres > "pg_backup_latest.bak"
docker exec -it nictiz_webtools_postgres_1 pg_dumpall -U postgres > "$_file"