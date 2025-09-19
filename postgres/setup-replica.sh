#!/bin/bash
set -e

# Wait for primary to be ready
until pg_isready -h postgres-primary -p 5432 -U postgres; do
  echo "Waiting for primary database..."
  sleep 2
done

# Stop PostgreSQL if running
pg_ctl stop -D "$PGDATA" -m fast || true

# Remove existing data
rm -rf "$PGDATA"/*

# Create base backup from primary
pg_basebackup -h postgres-primary -D "$PGDATA" -U replicator -W -v -P -R

# Set up recovery configuration
cat >> "$PGDATA/postgresql.conf" << EOF
hot_standby = on
primary_conninfo = 'host=postgres-primary port=5432 user=replicator password=$POSTGRES_REPLICATION_PASSWORD'
primary_slot_name = 'replica_slot'
EOF

# Start PostgreSQL
pg_ctl start -D "$PGDATA"