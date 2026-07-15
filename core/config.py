import os

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5433)),
    "user": os.getenv("DB_USER", "user"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "database": os.getenv("DB_NAME", "agn_db")
}

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "lightcurves")
KAFKA_GROUP = os.getenv("KAFKA_GROUP", "fastapi-backend-group-demo")
