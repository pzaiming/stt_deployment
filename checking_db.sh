container_id=cf49b00b2834

docker ps

docker exec -it $container_id bash

# in your docker it ===========
psql -U user -d initexample;

\dt

SELECT * FROM user_data;

SELECT * FROM keyword;

\q
