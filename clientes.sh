echo "services:
  server:
    build:
      context: ./services/server
      dockerfile: Dockerfile
    container_name: server
    environment:
      - PYTHONUNBUFFERED=1
      - SERVER_HOST=server
      - SERVER_PORT=5678" > docker-compose.yml


for i in $(seq 0 $1); do
    echo "  client_"$i":
    build:
      context: ./services/client
      dockerfile: Dockerfile
    container_name: client_"$i"
    depends_on:
      - server
    environment:
      - AGENCY_ID="$i"
      - SERVER_HOST=server
      - SERVER_PORT=5678" >> docker-compose.yml
done

echo "[INFO] Se creo el docker-compose con" $1 "clientes"