#!/bin/bash
set -euo pipefail

# Usage: dev/run.sh [--netbox DIR] [--reset] [--no-server]
#   --netbox DIR  where NetBox is (default: $NETBOX_ROOT, or .netbox/ inside this
#                 repository); cloned there at a pinned tag if it does not exist
#   --reset       drop and recreate the dev database (never any other)
#   --no-server   prepare everything but do not start the server
#
# Runs NetBox with this plugin against its own database ($DEV_DB). It takes
# care of everything it needs, so it works on a fresh clone of the repository,
# and it can be run as many times as wanted (every step is skipped when it is
# already done):
#   1. installs podman and the build packages with apt or dnf (sudo) if missing
#   2. clones NetBox (tag $NETBOX_REF, see dev/lib.sh) if DIR does not exist
#   3. creates the virtualenv there, with NetBox's requirements, this plugin
#      (editable, from the main checkout) and podman-compose
#   4. starts postgres and redis from dev/compose.yml if they are not running
#   5. creates $DEV_DB from the NetBox demo data (downloaded) if it is missing;
#      --reset drops it first
#   6. migrates, makes sure an admin/admin user exists and starts the server
#
# Environment: NETBOX_ROOT (same as --netbox), NETBOX_ROUTING_DEV_DB (default:
# netbox_routing_protocols_dev), PORT (default: 8000), NETBOX_REF, DEMO_VERSION.

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

RESET=""
SERVER=1
while [ $# -gt 0 ]; do
    case "$1" in
        --reset) RESET=1 ;;
        --no-server) SERVER="" ;;
        --netbox) [ $# -ge 2 ] || die "--netbox needs a directory"; NETBOX_ROOT="$2"; shift ;;
        --netbox=*) NETBOX_ROOT="${1#--netbox=}" ;;
        *) die "unknown argument: $1" ;;
    esac
    shift
done

DEV_DB="${NETBOX_ROUTING_DEV_DB:-netbox_routing_protocols_dev}"
PORT="${PORT:-8000}"

dev_setup
psql_() { podman exec -i "$POSTGRES" psql -U netbox -d postgres -v ON_ERROR_STOP=1 "$@"; }

if [ -n "$RESET" ]; then
    say "Dropping $DEV_DB"
    psql_ -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DEV_DB' AND pid <> pg_backend_pid()" >/dev/null
    psql_ -c "DROP DATABASE IF EXISTS \"$DEV_DB\""
fi

if [ "$(psql_ -Atc "SELECT count(*) FROM pg_database WHERE datname = '$DEV_DB'")" = 0 ]; then
    DEMO_SQL="$(demo_sql)"
    say "Creating $DEV_DB from the demo data $DEMO_VERSION"
    psql_ -c "CREATE DATABASE \"$DEV_DB\""
    # Two fixes to the dump: it is owned by the postgres role, which this container
    # does not have, and it empties the search_path, so the ltree operators used
    # by its triggers cannot be found
    grep -v '^\\restrict\|^\\unrestrict' "$DEMO_SQL" \
        | sed "s/OWNER TO postgres;/OWNER TO netbox;/; s/set_config('search_path', '', false)/set_config('search_path', 'public', false)/" \
        | podman exec -i "$POSTGRES" psql -U netbox -d "$DEV_DB" -v ON_ERROR_STOP=1 >/dev/null
fi

export PYTHONPATH="$DEV_DIR${PYTHONPATH:+:$PYTHONPATH}"
export NETBOX_CONFIGURATION=configuration_dev
export NETBOX_ROUTING_DEV_DB="$DEV_DB"
cd "$NETBOX_ROOT/netbox"

say "Migrating $DEV_DB"
"$PYTHON" manage.py migrate

say "Ensuring a superuser exists (admin/admin)"
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
    say "NetBox on http://localhost:$PORT (database: $DEV_DB)"
    exec "$PYTHON" manage.py runserver "0.0.0.0:$PORT"
fi
