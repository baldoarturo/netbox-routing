#!/bin/bash
set -euo pipefail

# Usage: dev/test.sh [--rebuild] [--own] [manage.py test arguments]
#   --rebuild  build the template database again
#   --own      only the tests written by hand (models, forms, filters, migrations,
#              validation rules), not the ones inherited from NetBox's CRUD test
#              classes for the API and the GUI: a quick loop while developing
#
# Runs the plugin tests (all of them without arguments) against a copy of a
# template database that is already migrated, instead of applying every NetBox
# migration on each run, which takes about 4 minutes. The template is built once
# from origin/main; each run clones it (under a second) and uses --keepdb, so
# Django only applies the migrations the checked out branch adds.
#
# Examples:
#   dev/test.sh
#   dev/test.sh netbox_routing_protocols.tests.ospf
#   dev/test.sh --parallel=4          (a failing test then hides its error: rerun it alone)
#
# Environment: NETBOX_ROOT (default: two levels above the main checkout of this
# repository).

REBUILD=""
OWN=""
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --rebuild) REBUILD=1 ;;
        --own) OWN=1 ;;
        *) ARGS+=("$arg") ;;
    esac
done
# Without a test label Django would discover every test under the current
# directory, NetBox's own included: default to the plugin's
HAS_LABEL=""
for arg in "${ARGS[@]+"${ARGS[@]}"}"; do
    case "$arg" in -*|[0-9]*) ;; *) HAS_LABEL=1 ;; esac
done
[ -n "$HAS_LABEL" ] || ARGS+=(netbox_routing_protocols)
if [ -n "$OWN" ]; then
    # test ids contain the module and the class: select the hand-written ones
    for pattern in test_models test_forms test_filtersets test_form_meta test_urls \
        migration unique ModelTestCase FormTestCase FilterSetTestCase \
        AuthenticationTestCase InheritanceTestCase; do
        ARGS+=(-k "$pattern")
    done
fi

DEV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$DEV_DIR")"
MAIN_DIR="$(cd "$(git -C "$DEV_DIR" rev-parse --path-format=absolute --git-common-dir)/.." && pwd)"
NETBOX_ROOT="${NETBOX_ROOT:-$(cd "$MAIN_DIR/../.." && pwd)}"
PYTHON="$NETBOX_ROOT/venv/bin/python"
TEST_DB="test_netbox"
TEMPLATE_DB="test_netbox_base"

[ -x "$PYTHON" ] || { echo "error: $PYTHON not found, run $NETBOX_ROOT/setup-dev.sh first" >&2; exit 1; }

POSTGRES="$(podman ps --filter "label=com.docker.compose.service=postgres" --format '{{.Names}}' 2>/dev/null | head -1)"
if [ -z "$POSTGRES" ]; then
    echo "==> Starting the containers"
    podman-compose -f "$NETBOX_ROOT/compose.yml" up -d >/dev/null 2>&1
    POSTGRES="$(podman ps --filter "label=com.docker.compose.service=postgres" --format '{{.Names}}' | head -1)"
fi
for _ in $(seq 1 30); do
    podman ps --filter "name=$POSTGRES" --format '{{.Status}}' 2>/dev/null | grep -q '(healthy)' && break
    sleep 2
done
psql_() { podman exec -i "$POSTGRES" psql -U netbox -d postgres -v ON_ERROR_STOP=1 -q "$@" 2>&1 | grep -v 'level=warning' || true; }
psql_q() { podman exec -i "$POSTGRES" psql -U netbox -d postgres -v ON_ERROR_STOP=1 -Atq "$@" 2>/dev/null; }
exists() { [ "$(psql_q -c "SELECT count(*) FROM pg_database WHERE datname = '$1'")" = 1 ]; }
drop_db() {
    psql_q -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$1' AND pid <> pg_backend_pid()" >/dev/null
    psql_q -c "DROP DATABASE IF EXISTS \"$1\"" >/dev/null
}
drop_test_databases() {
    # the test database and the clones of an earlier parallel run
    for db in $(psql_q -c "SELECT datname FROM pg_database WHERE datname ~ '^${TEST_DB}(_[0-9]+)?\$'"); do
        drop_db "$db"
    done
}

run_tests() { # $1: source directory of the plugin, rest: manage.py test arguments
    local source="$1"; shift
    (cd "$NETBOX_ROOT/netbox" && \
        PYTHONPATH="$source:$DEV_DIR" NETBOX_CONFIGURATION=configuration_test \
        "$PYTHON" manage.py test "$@")
}

build_template() {
    echo "==> Building the template database from origin/main (once, about 5 minutes)"
    local source="$MAIN_DIR" tmp=""
    if git -C "$MAIN_DIR" fetch -q origin main 2>/dev/null; then
        tmp="$(mktemp -d)"
        if git -C "$MAIN_DIR" worktree add -q --detach "$tmp/main" origin/main 2>/dev/null; then
            source="$tmp/main"
        fi
    fi
    drop_test_databases
    drop_db "$TEMPLATE_DB"
    # creates and migrates the test database, then keeps it
    run_tests "$source" netbox_routing_protocols.tests.test_urls --noinput --keepdb
    drop_db "$TEMPLATE_DB"
    psql_q -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$TEST_DB' AND pid <> pg_backend_pid()" >/dev/null
    psql_q -c "CREATE DATABASE \"$TEMPLATE_DB\" TEMPLATE \"$TEST_DB\"" >/dev/null
    if [ -n "$tmp" ]; then
        git -C "$MAIN_DIR" worktree remove --force "$tmp/main" 2>/dev/null || true
        rm -rf "$tmp"
    fi
}

if [ -n "$REBUILD" ] || ! exists "$TEMPLATE_DB"; then
    build_template
else
    # The template must not hold migrations this checkout does not have
    missing=""
    for name in $(podman exec -i "$POSTGRES" psql -U netbox -d "$TEMPLATE_DB" -Atq -c "SELECT name FROM django_migrations WHERE app = 'netbox_routing_protocols'" 2>/dev/null); do
        [ -e "$REPO_DIR/netbox_routing_protocols/migrations/$name.py" ] || missing="$missing $name"
    done
    if [ -n "$missing" ]; then
        echo "warning: the template has migrations this checkout lacks:$missing" >&2
        echo "         merge main into the branch, or run dev/test.sh --rebuild" >&2
    fi
fi

echo "==> Cloning $TEMPLATE_DB into $TEST_DB"
drop_test_databases
psql_q -c "CREATE DATABASE \"$TEST_DB\" TEMPLATE \"$TEMPLATE_DB\"" >/dev/null

run_tests "$REPO_DIR" "${ARGS[@]}" --noinput --keepdb
