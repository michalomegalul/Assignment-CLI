import psycopg2
import os
import time
from typing import List, Dict, Optional
from .logging_config import get_logger, log_database_operation, log_performance, set_correlation_id


class DatabaseManager:
    """Simple database manager for domain operations"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        # Get connection string from environment
        self.connection_string = os.getenv(
            'DATABASE_URL', 
        )
        self.logger.info("DatabaseManager initialized", extra={'connection_masked': self._mask_connection_string()})
    
    def _mask_connection_string(self) -> str:
        """Mask sensitive parts of connection string for logging"""
        if not self.connection_string:
            return "No connection string set"
        
        # Replace password with ***
        masked = self.connection_string
        if 'password=' in masked or ':' in masked:
            import re
            # Replace password in URL format
            masked = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', masked)
            # Replace password in param format
            masked = re.sub(r'password=([^\s&]+)', r'password=***', masked)
        
        return masked
    
    def get_connection(self):
        """Get database connection"""
        start_time = time.time()
        correlation_id = set_correlation_id()
        
        try:
            self.logger.debug(f"Attempting database connection", extra={'correlation_id': correlation_id})
            conn = psycopg2.connect(self.connection_string)
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.info(f"Database connection established", extra={
                'correlation_id': correlation_id,
                'duration_ms': f"{duration_ms:.2f}"
            })
            
            return conn
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Database connection failed: {e}", extra={
                'correlation_id': correlation_id,
                'duration_ms': f"{duration_ms:.2f}",
                'error_type': type(e).__name__
            })
            raise
    
    def get_active_domains(self) -> List[str]:
        """Get domains that are registered and don't have active EXPIRED flag"""
        correlation_id = set_correlation_id()
        start_time = time.time()
        
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
        
        try:
            self.logger.debug(f"Executing get_active_domains query", extra={'correlation_id': correlation_id})
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    results = [row[0] for row in cur.fetchall()]
                    
            duration_ms = (time.time() - start_time) * 1000
            log_database_operation(
                self.logger, 
                "SELECT", 
                query, 
                duration_ms, 
                len(results),
                operation="get_active_domains",
                correlation_id=correlation_id
            )
            
            self.logger.info(f"Retrieved {len(results)} active domains", extra={
                'correlation_id': correlation_id,
                'result_count': len(results)
            })
            
            return results
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Failed to get active domains: {e}", extra={
                'correlation_id': correlation_id,
                'duration_ms': f"{duration_ms:.2f}",
                'error_type': type(e).__name__
            })
            raise
    
    def get_flagged_domains(self) -> List[str]:
        """Get domains that had both EXPIRED and OUTZONE flags"""
        correlation_id = set_correlation_id()
        start_time = time.time()
        
        query = """
        SELECT DISTINCT d.fqdn
        FROM domain d
        JOIN domain_flag df1 ON d.id = df1.domain_id
        JOIN domain_flag df2 ON d.id = df2.domain_id
        WHERE df1.flag = 'EXPIRED'
          AND df2.flag = 'OUTZONE'
        ORDER BY d.fqdn;
        """
        
        try:
            self.logger.debug(f"Executing get_flagged_domains query", extra={'correlation_id': correlation_id})
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    results = [row[0] for row in cur.fetchall()]
                    
            duration_ms = (time.time() - start_time) * 1000
            log_database_operation(
                self.logger, 
                "SELECT", 
                query, 
                duration_ms, 
                len(results),
                operation="get_flagged_domains",
                correlation_id=correlation_id
            )
            
            self.logger.info(f"Retrieved {len(results)} flagged domains", extra={
                'correlation_id': correlation_id,
                'result_count': len(results)
            })
            
            return results
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Failed to get flagged domains: {e}", extra={
                'correlation_id': correlation_id,
                'duration_ms': f"{duration_ms:.2f}",
                'error_type': type(e).__name__
            })
            raise
    
    def get_stats(self) -> Dict[str, int]:
        """Get basic database statistics"""
        correlation_id = set_correlation_id()
        start_time = time.time()
        
        try:
            self.logger.debug(f"Executing get_stats queries", extra={'correlation_id': correlation_id})
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get counts
                    query_start = time.time()
                    cur.execute("SELECT COUNT(*) FROM domain")
                    total_domains = cur.fetchone()[0]
                    query_duration = (time.time() - query_start) * 1000
                    log_database_operation(self.logger, "SELECT", "SELECT COUNT(*) FROM domain", 
                                         query_duration, 1, operation="count_total_domains", correlation_id=correlation_id)
                    
                    query_start = time.time()
                    cur.execute("SELECT COUNT(*) FROM domain WHERE unregistered_at IS NULL")
                    active_domains = cur.fetchone()[0]
                    query_duration = (time.time() - query_start) * 1000
                    log_database_operation(self.logger, "SELECT", "SELECT COUNT(*) FROM domain WHERE unregistered_at IS NULL", 
                                         query_duration, 1, operation="count_active_domains", correlation_id=correlation_id)
                    
                    query_start = time.time()
                    cur.execute("SELECT COUNT(*) FROM domain_flag")
                    total_flags = cur.fetchone()[0]
                    query_duration = (time.time() - query_start) * 1000
                    log_database_operation(self.logger, "SELECT", "SELECT COUNT(*) FROM domain_flag", 
                                         query_duration, 1, operation="count_total_flags", correlation_id=correlation_id)
                    
                    results = {
                        'total_domains': total_domains,
                        'active_domains': active_domains,
                        'total_flags': total_flags
                    }
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.info(f"Retrieved database statistics", extra={
                'correlation_id': correlation_id,
                'duration_ms': f"{duration_ms:.2f}",
                'total_domains': total_domains,
                'active_domains': active_domains,
                'total_flags': total_flags
            })
            
            return results
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Failed to get database stats: {e}", extra={
                'correlation_id': correlation_id,
                'duration_ms': f"{duration_ms:.2f}",
                'error_type': type(e).__name__
            })
            raise