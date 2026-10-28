# CLAUDE.md

## About this repo

`netbox-routing-protocols` is a NetBox plugin for tracking routing information: static routes, EIGRP, OSPF and BGP (with templates/group inheritance, IPv4/IPv6 address families, VRF and VPNv4 support). IS-IS is on the roadmap.

It was created by Daniel Sheppard (`dansheps`). This repo is a fork (`baldoarturo/netbox-routing-protocols`) of his upstream project. We forked it to develop it with modern tooling (AI-assisted, like Claude) and speed up development.

## Working agreement

The user is the project manager: they ask, Claude does the work, they approve. Treat this as a standing rule for every session.

1. **Claude manages the issues.** Every bug we find gets a GitHub issue. Issues, branches and PRs go in the user's fork (`baldoarturo/netbox-routing-protocols`), never in Dan's upstream repo (`dansheps/netbox-routing`). Always pass `--repo baldoarturo/netbox-routing-protocols` to `gh`.
2. **One branch per issue, or per group of related issues, named `NN-name`.** Every problem still gets its own issue (create it first to get its number), but a pull request per issue is not required: issues that are related can be fixed together in one branch and one PR. Claude is the one who detects which issues are related (same model or area, the same files, one depends on the other, they add migrations that must be chained, or one fix makes the other trivial) and documents it in each issue: a line in the body or a comment such as `Related: #A, #B. Fixed together in #N (branch NN-name).` Unrelated issues keep their own branch and PR. The branch name is the number of the lead issue of the group (the lowest one, or the one that drives the change) followed by a short kebab-case name (`NN-name`, e.g. `67-claude-md-merge-rule` for issue #67), so branch and issue match numerically. Open the pull request against the fork's `main` with one `Closes #N` line per issue it resolves. Do not bundle issues just to save PRs: group them only when they are really related, so each PR stays reviewable.
3. **Claude may merge its own PR once its issues are resolved.** Merge (`gh pr merge --merge`) when all of these hold: the full test suite passes locally, `makemigrations --check` is clean, the lint CI is green, and the PR actually resolves its issues. Do not merge, and ask first, if a test fails, the fix needs a product decision, the change is destructive or hard to undo (data loss, dropping fields), or it is not clearly what the user asked for.
4. **Tests run locally, not in CI.** CI (`ci.yml`) only runs ruff and black. Run the whole suite against the dev PostgreSQL before pushing (see below). The full suite runs in CI only on release (`release-tests.yml`), using a migrated-schema cache built from `main` (`netbox-schema-cache.yml`).
5. **Migrations that depend on each other.** When several open PRs add migrations, chain them (each depends on the previous one) and merge them in order. Before merging a PR that has a migration, merge `main` into it and re-run the suite.
6. **Work in a separate git worktree** if another session may be using the same checkout, so branch switches do not collide.
7. **If you are not sure how to fix an issue, ask before coding.** Keep asking the user questions until no doubts remain, and ask for concrete examples (sample data, expected vs actual behaviour, a screenshot, a failing request) whenever they would remove ambiguity. Do not guess at the intended behaviour, and do not open a PR for a fix you are unsure about.
8. **Routing protocol design must follow the existing RFCs.** Model fields, choices, defaults, validation and terminology for BGP, OSPF, EIGRP, IS-IS and the like must conform to the relevant RFCs (e.g. RFC 4271 for BGP, RFC 2328 for OSPFv2, RFC 5340 for OSPFv3, RFC 7868 for EIGRP, ISO 10589 / RFC 1195 for IS-IS). Cite the RFC in the issue or PR when a design choice depends on it.
9. **If you have any doubt about the implementation, ask.** This applies to design and implementation, not only to bug fixes: when more than one reasonable approach exists, or the RFC is ambiguous or silent, ask the user before coding.
10. **Track every body of work with a tracking issue and a GitHub project.** When a review, gap analysis or feature area produces more than a couple of issues, set it up like the OSPF one (tracking issue #90, project "OSPFv2 support"):
    - One tracking issue titled `Tracking: <area>`. Body: a one-line intro ending with "Close each item through its own issue (related items can share a branch/PR, see rule 2)", then `##` sections with one `- [ ] #N short description` per issue (mark design items with `(design)`).
    - Every item is also a sub-issue of the tracking issue (`gh api repos/baldoarturo/netbox-routing-protocols/issues/<tracking>/sub_issues -X POST -F sub_issue_id=<issue id, not number>`), so the progress bar updates itself.
    - One GitHub project per area (GraphQL `createProjectV2`, owner `baldoarturo`), linked to the repo (`linkProjectV2ToRepository`), with the tracking issue and all items added. Keep the default workflows enabled (Auto-close issue, Item closed, Pull request merged) so closing an issue moves it to Done. The installed `gh` is too old for `gh project` and `gh label`: use `gh api`.
    - Give the issues a shared area label (e.g. `ospf`, `prefix-list`).
    - Claude keeps the tracking body current: when an issue is resolved, tick its `[x]` (strike through with `~#N~` and add the reason if it is dropped), and add new issues found later. Nothing ticks the checklist or closes the tracking issue automatically; close it by hand when every item is done.
    - Do not start coding until the user approves the tracking.

## Documentation

`docs/` is the documentation for operators and users (MkDocs, see `docs/development.md`), not for developers: it explains what each protocol and feature is for, how to use it from the menu, and which RFC it comes from and why. **Every time you add a user-facing feature, or change how a documented feature behaves, document it in the same PR** (no feature ships undocumented, and no change leaves the docs stale). The PR updates its section in the page of the protocol (and the RFC index in `docs/rfc-index.md`). Check it with `mkdocs build --strict` (`pip install -r docs/requirements.txt`).

## Running the dev server

`dev/run.sh` sets up everything and runs NetBox with this plugin against its own database (`netbox_routing_protocols_dev`, created from the NetBox demo data), so the plugin's migrations never run against any other database. It works on a fresh clone of the repository and can be run as often as wanted: every step is skipped when it is already done.

1. Installs podman and the build packages with apt or dnf (asks for sudo) if missing.
2. Clones NetBox at the pinned tag (`NETBOX_REF` in `dev/plugin.conf`) if its directory does not exist. Default directory: `.netbox/` in the repository (git-ignored); use `--netbox DIR` or `NETBOX_ROOT` for another one. An existing NetBox is used as it is.
3. Creates the venv in `<netbox>/venv` with NetBox's requirements, the plugin (editable, from the main checkout) and podman-compose.
4. Starts postgres and redis from `dev/compose.yml` unless a compose project already runs those services.
5. Creates the dev database from the demo data (downloaded the first time), migrates, makes sure `admin`/`admin` exists and starts the server on port 8000.

- `dev/run.sh --reset` drops and rebuilds the dev database (only that one).
- `dev/run.sh --no-server` prepares everything without starting the server; `--no-demo` creates the database empty instead of from the NetBox demo data.
- The only plugin-specific file of `dev/` is `dev/plugin.conf`; see `dev/README.md`.
- The server runs whatever is checked out in the main checkout.

## Running tests locally

`dev/test.sh` runs the plugin tests (all of them without arguments, or the labels you pass) against a copy of a migrated template database, so a run no longer spends about 4 minutes applying every NetBox migration. The template is built once from `origin/main`; each run clones it and uses `--keepdb`, so Django only applies the migrations of the branch. Run it from the main checkout or from a worktree. It sets up NetBox, the venv and the containers like `dev/run.sh` does, and takes the same `--netbox DIR`.

```
dev/test.sh                          # the whole suite
dev/test.sh netbox_routing_protocols.tests.ospf
dev/test.sh --parallel=4             # about twice as fast
dev/test.sh --own                    # only the hand-written tests, a quick loop
dev/test.sh --rebuild                # build the template again
```

- Measured on the whole suite (2048 tests): about 6 minutes before, 129 s with the script, 55 s with `--parallel=4`.
- Test classes that inherit NetBox's API/GUI test cases (`APIViewTestCases`, `ViewTestCases`) carry `LeanCoreTestsMixin` (`tests/base.py`), which switches off the checks that test NetBox itself and are identical for every model: permissions, bulk API edge cases, GraphQL, OPTIONS, etag. They run only on one sample model per area, whose classes do not have the mixin: `StaticRoute`, `BGPRouter`, `Community`, `PrefixListEntry`, `OSPFInstance` and `ISISInstance` (API and GUI). Add the mixin to the test classes of every new model. Do not add tests that only exercise NetBox or Django: test what the plugin defines (clean rules, constraints, defaults, filters, forms, serializers).
- Only the plugin's tests run, never NetBox's own: without a test label the script defaults to `netbox_routing_protocols`.
- `--own` skips the tests inherited from NetBox's CRUD test classes (API and GUI, about 85 % of the suite) and runs the ones written by hand (models, forms, filters, migrations, validation rules). Run the whole suite once before merging.
- `--parallel` needs `tblib` in the NetBox venv (`pip install tblib`) to report failures, and hides the real error behind a pickle error otherwise: rerun that test alone.
- After merging a branch with migrations into `main`, run `dev/test.sh --rebuild` once.
- Without the script: the plugin is installed editable in the NetBox venv; use a config module that extends `netbox.configuration_testing` with `PLUGINS += ['netbox_routing_protocols']` (and `DEVELOPER = True`), and run `manage.py test netbox_routing_protocols --noinput` from `<netbox>/netbox`. Do not use `--keepdb` there across branches with different migrations.
- Lint exactly like CI: `pre-commit run --all-files` (Ruff and Black, configured in `.pre-commit-config.yaml`, which is what `ci.yml` runs on every pull request; the versions are pinned there). Install the hooks once per clone with `pre-commit install` (`pip install pre-commit`); worktrees share them. Without pre-commit: `ruff check --config ruff.toml netbox_routing_protocols` and `black --check --skip-string-normalization netbox_routing_protocols`.

