"""
Database Performance Configuration for PostgreSQL optimization.
Implements connection pooling, query optimization, and performance monitoring.
"""

from dataclasses import dataclass
from typing import Any, Dict

from HappyRobot.config.settings import settings


@dataclass
class DatabasePerformanceConfig:
    """PostgreSQL performance configuration settings."""

    # Connection Pool Settings
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 1 hour
    pool_pre_ping: bool = True

    # Query Performance Settings
    statement_timeout: int = 30000  # 30 seconds
    lock_timeout: int = 10000  # 10 seconds
    idle_in_transaction_session_timeout: int = 60000  # 1 minute

    # Memory Settings
    shared_buffers: str = "256MB"
    effective_cache_size: str = "1GB"
    work_mem: str = "4MB"
    maintenance_work_mem: str = "64MB"

    # Write Performance
    wal_buffers: str = "16MB"
    checkpoint_completion_target: float = 0.9
    max_wal_size: str = "1GB"
    min_wal_size: str = "80MB"

    # Query Planning
    random_page_cost: float = 1.1  # For SSD
    effective_io_concurrency: int = 200  # For SSD
    default_statistics_target: int = 100

    # Parallel Query Execution
    max_parallel_workers_per_gather: int = 2
    max_parallel_workers: int = 8
    max_worker_processes: int = 8


def get_optimized_database_url() -> str:
    """Get database URL with performance parameters."""
    base_url = settings.get_async_database_url

    # Add performance parameters
    params = [
        "sslmode=prefer",
        "connect_timeout=10",
        "keepalives=1",
        "keepalives_idle=30",
        "keepalives_interval=10",
        "keepalives_count=5",
        "options=-c statement_timeout=30000 -c lock_timeout=10000",
    ]

    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{'&'.join(params)}"


def get_sqlalchemy_engine_config() -> Dict[str, Any]:
    """Get SQLAlchemy engine configuration for optimal performance."""
    config = DatabasePerformanceConfig()

    return {
        "pool_size": config.pool_size,
        "max_overflow": config.max_overflow,
        "pool_timeout": config.pool_timeout,
        "pool_recycle": config.pool_recycle,
        "pool_pre_ping": config.pool_pre_ping,
        "echo": False,  # Disable SQL logging in production
        "echo_pool": False,
        "future": True,
        "query_cache_size": 1200,
        "connect_args": {
            "server_settings": {
                "application_name": "HappyRobot",
                "jit": "off",  # Disable JIT for consistent performance
            },
            "command_timeout": 60,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
    }


def get_index_recommendations() -> Dict[str, str]:
    """Get recommended database indexes for common queries."""
    return {
        # User queries
        "idx_users_email": "CREATE INDEX idx_users_email ON users(email);",
        "idx_users_organization": "CREATE INDEX idx_users_organization_id ON users(organization_id);",
        # Project queries
        "idx_projects_organization": "CREATE INDEX idx_projects_organization_id ON projects(organization_id);",
        "idx_projects_created_by": "CREATE INDEX idx_projects_created_by ON projects(created_by);",
        "idx_projects_status": "CREATE INDEX idx_projects_status ON projects(status) WHERE status != 'archived';",
        # File metadata queries
        "idx_files_path": "CREATE INDEX idx_files_path ON file_metadata(file_path);",
        "idx_files_created_at": "CREATE INDEX idx_files_created_at ON file_metadata(created_at DESC);",
        # Chat queries
        "idx_chats_project": "CREATE INDEX idx_chats_project_id ON chats(project_id);",
        "idx_chats_user": "CREATE INDEX idx_chats_user_id ON chats(user_id);",
        "idx_chat_messages_chat": "CREATE INDEX idx_chat_messages_chat_id ON chat_messages(chat_id);",
        "idx_chat_messages_created": "CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at DESC);",
        # WebSocket tracking
        "idx_websocket_dedup": "CREATE INDEX idx_websocket_dedup ON websocket_dedup_tracking(message_hash, client_id);",
        "idx_websocket_timestamp": "CREATE INDEX idx_websocket_timestamp ON websocket_dedup_tracking(created_at);",
        # Activity logs
        "idx_activity_logs_entity": "CREATE INDEX idx_activity_logs_entity ON activity_logs(entity_type, entity_id);",
        "idx_activity_logs_user": "CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);",
        "idx_activity_logs_timestamp": "CREATE INDEX idx_activity_logs_timestamp ON activity_logs(timestamp DESC);",
        # Composite indexes for complex queries
        "idx_files_composite": "CREATE INDEX idx_files_composite ON file_metadata(user_id, upload_timestamp DESC) INCLUDE (original_filename, file_size);",
        "idx_projects_composite": "CREATE INDEX idx_projects_composite ON projects(organization_id, status) WHERE deleted_at IS NULL;",
    }


def get_database_maintenance_queries() -> Dict[str, str]:
    """Get database maintenance queries for optimal performance."""
    return {
        "analyze_tables": """
            DO $$
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public'
                LOOP
                    EXECUTE 'ANALYZE ' || quote_ident(r.tablename);
                END LOOP;
            END $$;
        """,
        "vacuum_tables": """
            DO $$
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public'
                LOOP
                    EXECUTE 'VACUUM (ANALYZE) ' || quote_ident(r.tablename);
                END LOOP;
            END $$;
        """,
        "reindex_bloated": """
            SELECT
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
                idx_scan as index_scans
            FROM pg_stat_user_indexes
            JOIN pg_index ON pg_stat_user_indexes.indexrelid = pg_index.indexrelid
            WHERE idx_scan = 0
            AND indisunique = false
            AND pg_relation_size(indexrelid) > 1048576; -- > 1MB
        """,
        "find_missing_indexes": """
            SELECT
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats
            WHERE schemaname = 'public'
            AND n_distinct > 100
            AND correlation < 0.1
            ORDER BY n_distinct DESC;
        """,
        "connection_stats": """
            SELECT
                state,
                count(*) as count,
                max(now() - state_change) as max_duration
            FROM pg_stat_activity
            WHERE datname = current_database()
            GROUP BY state
            ORDER BY count DESC;
        """,
        "slow_queries": """
            SELECT
                query,
                calls,
                mean_exec_time,
                total_exec_time,
                rows
            FROM pg_stat_statements
            WHERE mean_exec_time > 100  -- queries slower than 100ms
            ORDER BY mean_exec_time DESC
            LIMIT 20;
        """,
        "table_bloat": """
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
                pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size,
                round(100 * pg_total_relation_size(schemaname||'.'||tablename) / pg_database_size(current_database()))::numeric, 2 AS percent_of_db
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 20;
        """,
        "cache_hit_ratio": """
            SELECT
                'index hit rate' AS name,
                sum(idx_blks_hit) / sum(idx_blks_hit + idx_blks_read) AS ratio
            FROM pg_statio_user_indexes
            UNION ALL
            SELECT
                'table hit rate' AS name,
                sum(heap_blks_hit) / sum(heap_blks_hit + heap_blks_read) AS ratio
            FROM pg_statio_user_tables;
        """,
    }


def get_postgresql_config_recommendations() -> Dict[str, str]:
    """Get PostgreSQL configuration recommendations for production."""
    return {
        "shared_buffers": "25% of RAM (min 256MB, max 8GB)",
        "effective_cache_size": "50-75% of RAM",
        "work_mem": "RAM / (max_connections * 3)",
        "maintenance_work_mem": "RAM / 16 (max 2GB)",
        "wal_buffers": "16MB",
        "checkpoint_segments": "32 (for older versions)",
        "checkpoint_completion_target": "0.9",
        "random_page_cost": "1.1 for SSD, 4.0 for HDD",
        "effective_io_concurrency": "200 for SSD, 2 for HDD",
        "max_connections": "100-200 (use connection pooling instead)",
        "autovacuum": "on",
        "autovacuum_max_workers": "4",
        "autovacuum_naptime": "30s",
        "log_min_duration_statement": "100ms",
        "log_checkpoints": "on",
        "log_connections": "on",
        "log_disconnections": "on",
        "log_lock_waits": "on",
        "log_temp_files": "0",
        "shared_preload_libraries": "pg_stat_statements",
    }


def generate_performance_report_query() -> str:
    """Generate comprehensive database performance report query."""
    return """
    WITH
    db_size AS (
        SELECT pg_database_size(current_database()) as size
    ),
    cache_ratio AS (
        SELECT
            sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as heap_ratio,
            sum(idx_blks_hit) / (sum(idx_blks_hit) + sum(idx_blks_read)) as idx_ratio
        FROM pg_statio_user_tables
    ),
    connection_info AS (
        SELECT
            count(*) as total_connections,
            count(*) FILTER (WHERE state = 'active') as active_connections,
            count(*) FILTER (WHERE state = 'idle') as idle_connections,
            count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
        FROM pg_stat_activity
        WHERE datname = current_database()
    ),
    long_running AS (
        SELECT count(*) as long_queries
        FROM pg_stat_activity
        WHERE datname = current_database()
        AND state = 'active'
        AND now() - query_start > interval '1 minute'
    ),
    table_sizes AS (
        SELECT
            count(*) as table_count,
            sum(pg_total_relation_size(schemaname||'.'||tablename)) as total_size
        FROM pg_tables
        WHERE schemaname = 'public'
    )
    SELECT
        pg_size_pretty(db_size.size) as database_size,
        round(cache_ratio.heap_ratio * 100, 2) as table_cache_hit_ratio,
        round(cache_ratio.idx_ratio * 100, 2) as index_cache_hit_ratio,
        connection_info.total_connections,
        connection_info.active_connections,
        connection_info.idle_connections,
        connection_info.idle_in_transaction,
        long_running.long_queries,
        table_sizes.table_count,
        pg_size_pretty(table_sizes.total_size) as total_table_size
    FROM db_size, cache_ratio, connection_info, long_running, table_sizes;
    """
