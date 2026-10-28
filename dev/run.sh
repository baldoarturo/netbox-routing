#!/bin/bash
set -euo pipefail

# Usage: dev/run.sh [--reset] [--no-server]
#   --reset      drop and recreate the dev database (never the shared one)
#   --no-server  prepare everything but do not start the server
#
# Runs NetBox with this plugin against its own database ($DEV_DB). Based on
# NetBox's setup-dev.sh. Like it, it can be run as many times as wanted:
# --reset drops and rebuilds the database (here only $DEV_DB, so the plugin's
# migrations never touch the shared $SOURCE_DB database, which stays as the
# baseline every rebuild starts from).
# Without --reset it keeps the current data: starts the podman containers if
# needed, creates the database if missing (a copy of $SOURCE_DB, or the demo
# data if there is none), migrates, makes sure an admin/admin user exists and
# starts the server.
#
# Environment: NETBOX_ROOT (default: two levels above the main checkout of this
# repository),
# NETBOX_ROUTING_DEV_DB (default: netbox_routing_protocols_dev), PORT (default: 8000).

RESET=""
SERVER=1
for arg in "$@"; do
    case "$arg" in
        --reset) RESET=1 ;;
        --no-server) SERVER="" ;;
        *) echo "unknown argument: $arg" >&2; exit 1 ;;
    esac
done

DEV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# The main checkout of this repository (also when run from a git worktree)
REPO_ROOT="$(cd "$(git -C "$DEV_DIR" rev-parse --path-format=absolute --git-common-dir)/.." && pwd)"
NETBOX_ROOT="${NETBOX_ROOT:-$(cd "$REPO_ROOT/../.." && pwd)}"
DEV_DB="${NETBOX_ROUTING_DEV_DB:-netbox_routing_protocols_dev}"
SOURCE_DB="netbox"
PORT="${PORT:-8000}"
DEMO_SQL="$NETBOX_ROOT/netbox-demo-v4.6.sql"
PYTHON="$NETBOX_ROOT/venv/bin/python"

[ -x "$PYTHON" ] || { echo "error: $PYTHON not found, run $NETBOX_ROOT/setup-dev.sh first" >&2; exit 1; }

echo "==> Containers (postgres, redis)"
POSTGRES="$(podman ps --filter "label=com.docker.compose.service=postgres" --format '{{.Names}}' | head -1)"
if [ -z "$POSTGRES" ]; then
    podman-compose -f "$NETBOX_ROOT/compose.yml" up -d
    POSTGRES="$(podman ps --filter "label=com.docker.compose.service=postgres" --format '{{.Names}}' | head -1)"
fi
for _ in $(seq 1 30); do
    podman ps --filter "name=$POSTGRES" --format '{{.Status}}' | grep -q '(healthy)' && break
    sleep 2
done
psql_() { podman exec -i "$POSTGRES" psql -U netbox -d postgres -v ON_ERROR_STOP=1 "$@"; }

if [ -n "$RESET" ]; then
    echo "==> Dropping $DEV_DB"
    psql_ -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DEV_DB' AND pid <> pg_backend_pid()" >/dev/null
    psql_ -c "DROP DATABASE IF EXISTS \"$DEV_DB\""
fi

if [ "$(psql_ -Atc "SELECT count(*) FROM pg_database WHERE datname = '$DEV_DB'")" = 0 ]; then
    if [ "$(psql_ -Atc "SELECT count(*) FROM pg_database WHERE datname = '$SOURCE_DB'")" = 1 ] \
        && [ "$(psql_ -Atc "SELECT count(*) FROM pg_stat_activity WHERE datname = '$SOURCE_DB'")" = 0 ]; then
        echo "==> Creating $DEV_DB as a copy of $SOURCE_DB"
        psql_ -c "CREATE DATABASE \"$DEV_DB\" TEMPLATE \"$SOURCE_DB\""
    else
        echo "==> Creating $DEV_DB from the demo data ($SOURCE_DB is missing or in use)"
        [ -f "$DEMO_SQL" ] || { echo "error: $DEMO_SQL not found" >&2; exit 1; }
        psql_ -c "CREATE DATABASE \"$DEV_DB\""
        grep -v '^\\restrict\|^\\unrestrict' "$DEMO_SQL" \
            | podman exec -i "$POSTGRES" psql -U netbox -d "$DEV_DB" -v ON_ERROR_STOP=1 >/dev/null
    fi
fi

export PYTHONPATH="$DEV_DIR${PYTHONPATH:+:$PYTHONPATH}"
export NETBOX_CONFIGURATION=configuration_dev
cd "$NETBOX_ROOT/netbox"

echo "==> Migrating $DEV_DB"
"$PYTHON" manage.py migrate

echo "==> Ensuring a superuser exists (admin/admin)"
"$PYTHON" manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('created admin/admin')
else:
    print('admin already exists')
"

if [ -n "$SERVER" ]; then
    echo "==> NetBox on http://localhost:$PORT (database: $DEV_DB)"
    exec "$PYTHON" manage.py runserver "0.0.0.0:$PORT"
fi
