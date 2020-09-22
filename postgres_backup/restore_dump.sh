# First down / delete pgdata / up
docker cp pg_backup_latest.bak nictiz_webtools_postgres_1:/home/backup_latest.bak
docker volume rm nictiz_webtools_pgdata
docker exec -it nictiz_webtools_postgres_1 psql -U postgres -f /home/backup_latest.bak postgres
# docker exec -it nictiz_webtools_postgres_1 psql -U tickets tickets < /home/dump.sql
