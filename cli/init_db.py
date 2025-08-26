import os
import psycopg2
import logging
from .errors import handle_error

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        handle_error("DATABASE_URL environment variable not set")

    seed_file = "sql/seed.sql"
    if not os.path.exists(seed_file):
        handle_error(f"Seed file not found: {seed_file}")

    try:
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cur:
                logger.info("Clearing existing data...")
                cur.execute("TRUNCATE TABLE domain_flag, domain RESTART IDENTITY CASCADE;")
                
                logger.info(f"Running seed SQL from {seed_file}")
                with open(seed_file, "r") as f:
                    sql = f.read()
                    cur.execute(sql)
                conn.commit()
                logger.info("DB seeding complete")
    except Exception as e:
        handle_error(f"Failed to initialize DB: {e}")

if __name__ == "__main__":
    init_db()