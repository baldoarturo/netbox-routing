# CLAUDE.md

## About this repo

`netbox-routing-protocols` is a NetBox plugin for tracking routing information: static routes, EIGRP, OSPF and BGP (with templates/group inheritance, IPv4/IPv6 address families, VRF and VPNv4 support). IS-IS is on the roadmap.

It was created by Daniel Sheppard (`dansheps`). This repo is a fork (`baldoarturo/netbox-routing-protocols`) of his upstream project. We forked it to develop it with modern tooling (AI-assisted, like Claude) and speed up development.

## Working agreement

The user is the project manager: they ask, Claude does the work, they approve. Treat this as a standing rule for every session.

1. **Claude manages the issues.** Every bug we find gets a GitHub issue. Issues, branches and PRs go in the user's fork (`baldoarturo/netbox-routing-protocols`), never in Dan's upstream repo (`dansheps/netbox-routing`). Always pass `--repo baldoarturo/netbox-routing-protocols` to `gh`.
2. **One branch per issue, named `NN-name`.** Create a new branch for each issue, fix it there, and open a pull request against the fork's `main` (`Closes #N`). The branch name is the issue number followed by a short kebab-case name (`NN-name`, e.g. `67-claude-md-merge-rule` for issue #67), so branch and issue match numerically. Create the issue first to get its number.
3. **Claude may merge its own PR once the issue is resolved.** Merge (`gh pr merge --merge`) when all of these hold: the full test suite passes locally, `makemigrations --check` is clean, the lint CI is green, and the PR actually resolves its issue. Do not merge, and ask first, if a test fails, the fix needs a product decision, the change is destructive or hard to undo (data loss, dropping fields), or it is not clearly what the user asked for.
4. **Tests run locally, not in CI.** CI (`ci.yml`) only runs ruff and black. Run the whole suite against the dev PostgreSQL before pushing (see below). The full suite runs in CI only on release (`release-tests.yml`), using a migrated-schema cache built from `main` (`netbox-schema-cache.yml`).
5. **Migrations that depend on each other.** When several open PRs add migrations, chain them (each depends on the previous one) and merge them in order. Before merging a PR that has a migration, merge `main` into it and re-run the suite.
6. **Work in a separate git worktree** if another session may be using the same checkout, so branch switches do not collide.
7. **If you are not sure how to fix an issue, ask before coding.** Keep asking the user questions until no doubts remain, and ask for concrete examples (sample data, expected vs actual behaviour, a screenshot, a failing request) whenever they would remove ambiguity. Do not guess at the intended behaviour, and do not open a PR for a fix you are unsure about.
8. **Routing protocol design must follow the existing RFCs.** Model fields, choices, defaults, validation and terminology for BGP, OSPF, EIGRP, IS-IS and the like must conform to the relevant RFCs (e.g. RFC 4271 for BGP, RFC 2328 for OSPFv2, RFC 5340 for OSPFv3, RFC 7868 for EIGRP, ISO 10589 / RFC 1195 for IS-IS). Cite the RFC in the issue or PR when a design choice depends on it.
9. **If you have any doubt about the implementation, ask.** This applies to design and implementation, not only to bug fixes: when more than one reasonable approach exists, or the RFC is ambiguous or silent, ask the user before coding.
10. **Track every body of work with a tracking issue and a GitHub project.** When a review, gap analysis or feature area produces more than a couple of issues, set it up like the OSPF one (tracking issue #90, project "OSPFv2 support"):
    - One tracking issue titled `Tracking: <area>`. Body: a one-line intro ending with "Close each item through its own issue/branch/PR", then `##` sections with one `- [ ] #N short description` per issue (mark design items with `(design)`).
    - Every item is also a sub-issue of the tracking issue (`gh api repos/baldoarturo/netbox-routing-protocols/issues/<tracking>/sub_issues -X POST -F sub_issue_id=<issue id, not number>`), so the progress bar updates itself.
    - One GitHub project per area (GraphQL `createProjectV2`, owner `baldoarturo`), linked to the repo (`linkProjectV2ToRepository`), with the tracking issue and all items added. Keep the default workflows enabled (Auto-close issue, Item closed, Pull request merged) so closing an issue moves it to Done. The installed `gh` is too old for `gh project` and `gh label`: use `gh api`.
    - Give the issues a shared area label (e.g. `ospf`, `prefix-list`).
    - Claude keeps the tracking body current: when an issue is resolved, tick its `[x]` (strike through with `~#N~` and add the reason if it is dropped), and add new issues found later. Nothing ticks the checklist or closes the tracking issue automatically; close it by hand when every item is done.
    - Do not start coding until the user approves the tracking.

## Running the dev server

`dev/run.sh` runs NetBox with this plugin against its own database (`netbox_routing_protocols_dev`, a copy of the shared `netbox` one), so the plugin's migrations never run against the shared database. It starts the podman containers if needed, creates the database if missing, migrates, makes sure `admin`/`admin` exists and starts the server on port 8000.

- `dev/run.sh --reset` drops and rebuilds the dev database (only that one), so it can be run as often as wanted.
- `dev/run.sh --no-server` prepares everything without starting the server.
- The plugin is installed in editable mode from the main checkout, so the server runs whatever is checked out there.

## Running tests locally

`dev/test.sh` runs the plugin tests (all of them without arguments, or the labels you pass) against a copy of a migrated template database, so a run no longer spends about 4 minutes applying every NetBox migration. The template is built once from `origin/main`; each run clones it and uses `--keepdb`, so Django only applies the migrations of the branch. Run it from the main checkout or from a worktree.

```
dev/test.sh                          # the whole suite
dev/test.sh netbox_routing_protocols.tests.ospf
dev/test.sh --parallel=4             # about twice as fast
dev/test.sh --own                    # only the hand-written tests, a quick loop
dev/test.sh --rebuild                # build the template again
```

- Measured on the whole suite (2048 tests): about 6 minutes before, 129 s with the script, 55 s with `--parallel=4`.
- Only the plugin's tests run, never NetBox's own: without a test label the script defaults to `netbox_routing_protocols`.
- `--own` skips the tests inherited from NetBox's CRUD test classes (API and GUI, about 85 % of the suite) and runs the ones written by hand (models, forms, filters, migrations, validation rules). Run the whole suite once before merging.
- `--parallel` needs `tblib` in the NetBox venv (`pip install tblib`) to report failures, and hides the real error behind a pickle error otherwise: rerun that test alone.
- After merging a branch with migrations into `main`, run `dev/test.sh --rebuild` once.
- Without the script: the plugin is installed editable in the NetBox venv; use a config module that extends `netbox.configuration_testing` with `PLUGINS += ['netbox_routing_protocols']` (and `DEVELOPER = True`), and run `manage.py test netbox_routing_protocols --noinput` from `<netbox>/netbox`. Do not use `--keepdb` there across branches with different migrations.
- Lint exactly like CI: `ruff check --config ruff.toml netbox_routing_protocols` and `black --check --skip-string-normalization netbox_routing_protocols`.

