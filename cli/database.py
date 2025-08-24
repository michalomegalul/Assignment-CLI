import psycopg2
import os
from typing import List, Dict, Optional


class DatabaseManager:
    """Simple database manager for domain operations"""
    
    def __init__(self):
        # Get connection string from environment
        self.connection_string = os.getenv(
            'DATABASE_URL', 
        )
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.connection_string)
    
    def get_active_domains(self) -> List[str]:
        """Get domains that are registered and don't have active EXPIRED flag"""
        query = """
        SELECT d.fqdn
        FROM domain d
        WHERE d.unregistered_at IS NULL
          AND d.id NOT IN (
            SELECT df.domain_id 
            FROM domain_flag df 
            WHERE df.flag = 'EXPIRED' 
                AND df.valid_to IS NULL
          )
        ORDER BY d.fqdn;
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return [row[0] for row in cur.fetchall()]
    
    def get_flagged_domains(self) -> List[str]:
        """Get domains that had both EXPIRED and OUTZONE flags"""
        query = """
        SELECT DISTINCT d.fqdn
        FROM domain d
        JOIN domain_flag df1 ON d.id = df1.domain_id
        JOIN domain_flag df2 ON d.id = df2.domain_id
        WHERE df1.flag = 'EXPIRED'
          AND df2.flag = 'OUTZONE'
        ORDER BY d.fqdn;
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return [row[0] for row in cur.fetchall()]
    
    def get_stats(self) -> Dict[str, int]:
        """Get basic database statistics"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Get counts
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