# CLAUDE.md

## About this repo

`netbox-routing` is a NetBox plugin for tracking routing information: static routes, EIGRP, OSPF and BGP (with templates/group inheritance, IPv4/IPv6 address families, VRF and VPNv4 support). IS-IS is on the roadmap.

It was created by Daniel Sheppard (`dansheps`). This repo is a fork (`baldoarturo/netbox-routing`) of his upstream project. We forked it to develop it with modern tooling (AI-assisted, like Claude) and speed up development.

## Working agreement

The user is the project manager: they ask, Claude does the work, they approve. Treat this as a standing rule for every session.

1. **Claude manages the issues.** Every bug we find gets a GitHub issue. Issues, branches and PRs go in the user's fork (`baldoarturo/netbox-routing`), never in Dan's upstream repo (`dansheps/netbox-routing`). Always pass `--repo baldoarturo/netbox-routing` to `gh`.
2. **One branch per issue.** Create a new branch for each issue, fix it there, and open a pull request against the fork's `main`. The user reviews and approves; do not merge on their behalf.
