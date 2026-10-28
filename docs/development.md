# Development

For people who want to run the plugin from source or contribute.

## Run it

```
git clone https://github.com/baldoarturo/netbox-routing-protocols
cd netbox-routing-protocols
dev/run.sh
```

`dev/run.sh` installs podman if needed, downloads NetBox, creates the virtual environment, starts
PostgreSQL and Redis, loads the NetBox demo data and starts NetBox on <http://localhost:8000>
(user `admin`, password `admin`). It can be run again at any time. The full explanation, the options
and how to run the tests are in [`dev/README.md`](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/dev/README.md).

## Work on these docs

The documentation is Markdown in `docs/`, built with [MkDocs](https://www.mkdocs.org/) and the Material
theme.

```
pip install -r docs/requirements.txt
mkdocs serve        # preview at http://127.0.0.1:8000, reloads on save
mkdocs build --strict
```

`--strict` fails on broken links, which is what the publishing workflow runs.

When you add or change a feature, update its section in the page of the protocol, with the RFC it comes
from and why it exists when that is not obvious, and add the RFC to the [RFC index](rfc-index.md).

## Publishing

The site is published to GitHub Pages by the `docs` workflow when `main` changes. The repository needs
Pages enabled with the source set to *GitHub Actions* and the repository variable `DOCS_PAGES` set to
`true`; until then the workflow only checks that the site builds.
