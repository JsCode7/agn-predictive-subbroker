import psycopg2
from psycopg2 import pool
from core.config import DB_PARAMS

class PostgresDB:
    def __init__(self):
        self.pool = None

    def init_db(self):
        try:
            self.pool = pool.SimpleConnectionPool(1, 20, **DB_PARAMS)
            conn = self.pool.getconn()
            cur = conn.cursor()
            
            # Table 1: History
            cur.execute('''
                CREATE TABLE IF NOT EXISTS inference_history (
                    id SERIAL PRIMARY KEY,
                    oid VARCHAR(50) NOT NULL,
                    n_points INT NOT NULL,
                    tau FLOAT,
                    sigma FLOAT,
                    classification VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (oid, n_points)
                )
            ''')
            
            # Table 2: Current state
            cur.execute('''
                CREATE TABLE IF NOT EXISTS current_inference (
                    oid VARCHAR(50) PRIMARY KEY,
                    tau FLOAT,
                    sigma FLOAT,
                    n_points INT,
                    classification VARCHAR(50),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            cur.close()
            self.pool.putconn(conn)
            print("Postgres DB initialized with history and current state tables.")
        except Exception as e:
            print("Failed to initialize DB:", e)

    def save_inference(self, oid, tau, sigma, n_points, classification):
        if self.pool is None: return
        try:
            conn = self.pool.getconn()
            cur = conn.cursor()
            
            cur.execute('''
                INSERT INTO inference_history (oid, n_points, tau, sigma, classification)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (oid, n_points) DO NOTHING
            ''', (oid, n_points, tau, sigma, classification))
            
            cur.execute('''
                INSERT INTO current_inference (oid, tau, sigma, n_points, classification)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (oid) DO UPDATE SET 
                    tau = EXCLUDED.tau,
                    sigma = EXCLUDED.sigma,
                    n_points = EXCLUDED.n_points,
                    classification = EXCLUDED.classification,
                    updated_at = CURRENT_TIMESTAMP
            ''', (oid, tau, sigma, n_points, classification))
            
            conn.commit()
            cur.close()
            self.pool.putconn(conn)
        except Exception as e:
            print(f"Error saving to DB: {e}")

# Singleton instance
db_manager = PostgresDB()
