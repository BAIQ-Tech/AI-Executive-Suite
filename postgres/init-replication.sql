-- Create replication user
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'REPLICATION_PASSWORD_PLACEHOLDER';

-- Grant necessary permissions
GRANT CONNECT ON DATABASE ai_executive_suite TO replicator;

-- Create replication slot
SELECT pg_create_physical_replication_slot('replica_slot');