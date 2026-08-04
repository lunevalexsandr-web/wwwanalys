FROM postgres:15

# Копируем дамп БД в init-директорию — PostgreSQL сам накатит его при первом старте
COPY init.sql /docker-entrypoint-initdb.d/