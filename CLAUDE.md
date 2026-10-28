# CLAUDE.md

## About this repo

`netbox-routing` is a NetBox plugin for tracking routing information: static routes, EIGRP, OSPF and BGP (with templates/group inheritance, IPv4/IPv6 address families, VRF and VPNv4 support). IS-IS is on the roadmap.

It was created by Daniel Sheppard (`dansheps`). This repo is a fork (`baldoarturo/netbox-routing`) of his upstream project. We forked it to develop it with modern tooling (AI-assisted, like Claude) and speed up development.

## Working agreement

The user is the project manager: they ask, Claude does the work, they approve. Treat this as a standing rule for every session.

1. **Claude manages the issues.** Every bug we find gets a GitHub issue. Issues, branches and PRs go in the user's fork (`baldoarturo/netbox-routing`), never in Dan's upstream repo (`dansheps/netbox-routing`). Always pass `--repo baldoarturo/netbox-routing` to `gh`.
2. **One branch per issue, named `NN-name`.** Create a new branch for each issue, fix it there, and open a pull request against the fork's `main` (`Closes #N`). The branch name is the issue number followed by a short kebab-case name (`NN-name`, e.g. `67-claude-md-merge-rule` for issue #67), so branch and issue match numerically. Create the issue first to get its number.
3. **Claude may merge its own PR once the issue is resolved.** Merge (`gh pr merge --merge`) when all of these hold: the full test suite passes locally, `makemigrations --check` is clean, the lint CI is green, and the PR actually resolves its issue. Do not merge, and ask first, if a test fails, the fix needs a product decision, the change is destructive or hard to undo (data loss, dropping fields), or it is not clearly what the user asked for.
4. **Tests run locally, not in CI.** CI (`ci.yml`) only runs ruff and black. Run the whole suite against the dev PostgreSQL before pushing (see below). The full suite runs in CI only on release (`release-tests.yml`), using a migrated-schema cache built from `main` (`netbox-schema-cache.yml`).
5. **Migrations that depend on each other.** When several open PRs add migrations, chain them (each depends on the previous one) and merge them in order. Before merging a PR that has a migration, merge `main` into it and re-run the suite.
6. **Work in a separate git worktree** if another session may be using the same checkout, so branch switches do not collide.
7. **If you are not sure how to fix an issue, ask before coding.** Keep asking the user questions until no doubts remain, and ask for concrete examples (sample data, expected vs actual behaviour, a screenshot, a failing request) whenever they would remove ambiguity. Do not guess at the intended behaviour, and do not open a PR for a fix you are unsure about.

## Running tests locally

The plugin is installed editable in the NetBox venv. NetBox settings must load `netbox_routing`; use a config module that extends `netbox.configuration_testing` with `PLUGINS += ['netbox_routing']` (and `DEVELOPER = True` to run `makemigrations`).

```
cd <netbox>/netbox
NETBOX_CONFIGURATION=<that config> ../venv/bin/python manage.py test netbox_routing --parallel 4 --noinput
```

- `--parallel` hides real errors behind a pickle error when a test fails: rerun serially to see them.
- Do not use `--keepdb` across branches with different migrations: the kept test database keeps the old schema. Use `--noinput` (recreates it).
- Lint exactly like CI: `ruff check --config ruff.toml netbox_routing` and `black --check --skip-string-normalization netbox_routing`.

