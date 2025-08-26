import os
import psycopg2
from typing import List, Dict
from .errors import handle_error


class DatabaseManager:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            handle_error("DATABASE_URL environment variable not set")

    def get_connection(self):
        try:
            return psycopg2.connect(self.db_url)
        except Exception as e:
            handle_error(f"Failed to connect to database: {e}")

    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM domain")
                total_domains = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM domain WHERE unregistered_at IS NULL")
                active_domains = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM domain_flag")
                total_flags = cur.fetchone()[0]
                
                return {
                    'total_domains': total_domains,
                    'active_domains': active_domains,
                    'total_flags': total_flags
                }

    def get_active_domains(self) -> List[str]:
        """Get list of active domains (registered, not expired)."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT d.fqdn
                    FROM domain d
                    WHERE d.unregistered_at IS NULL
                      AND d.id NOT IN (
                        SELECT df.domain_id 
                        FROM domain_flag df 
                        WHERE df.flag = 'EXPIRED' 
                            AND df.valid_to IS NULL
                      )
                    ORDER BY d.fqdn
                """)
                return [row[0] for row in cur.fetchall()]

    def get_flagged_domains(self) -> List[str]:
        """Get domains that had both EXPIRED and OUTZONE flags."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT d.fqdn
                    FROM domain d
                    JOIN domain_flag df1 ON d.id = df1.domain_id
                    JOIN domain_flag df2 ON d.id = df2.domain_id
                    WHERE df1.flag = 'EXPIRED'
                      AND df2.flag = 'OUTZONE'
                    ORDER BY d.fqdn
                """)
                return [row[0] for row in cur.fetchall()]