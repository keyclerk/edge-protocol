<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="brand/keyclerk-lockup-dark.svg">
    <img src="brand/keyclerk-lockup-light.svg" alt="KeyClerk" width="360">
  </picture>
</p>
<p align="center"><em>Every key signed. Every key returned.</em></p>
<p align="center">
  <a href="https://github.com/keyclerk/edge-protocol/actions/workflows/ci.yml"><img src="https://github.com/keyclerk/edge-protocol/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/keyclerk/edge-protocol"><img src="https://api.scorecard.dev/projects/github.com/keyclerk/edge-protocol/badge" alt="OpenSSF Scorecard"></a>
  <a href="https://github.com/keyclerk/edge-protocol/releases/latest"><img src="https://img.shields.io/github/v/release/keyclerk/edge-protocol" alt="Latest release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/licence-EUPL--1.2-blue" alt="Licence: EUPL-1.2"></a>
</p>

# The KeyClerk edge protocol

KeyClerk is an access-governance engine for Keycloak: people get access for a time, through signed approvals, and it
ends by itself; every change is a signed record anyone can check. An **edge** is the small appliance at a site that
admits people to the systems behind it on the strength of leases KeyClerk has signed, and keeps working for a bounded
time when KeyClerk is out of reach.

This repository holds the protocol between the two, so that anyone can build an edge, and the conformance set that
says whether an edge gets it right:

- [`edge-protocol.md`](edge-protocol.md): trust pinned on site, enrolment, signed requests, the signed objects, the
  bundle, policy in the edge, the calls an edge makes, envelopes to people, carried visit leases, phoned unlock, the
  lifecycle, TPM attestation.
- [`conformance/edge.json`](conformance/edge.json): fixed vectors for the bundle verifier, officer statements,
  ceilings, ended notices, phoned-unlock codes, policy modules by hash, and the edge policy itself. An implementation
  conforms when it gives every recorded verdict.

## Status
Version 1 of the formats, as KeyClerk 0.24.0 ships them. A format changes only under a new name (`-v4` after `-v3`),
so an edge that verifies `kc-edge-bundle-v3` keeps working until it chooses to move. The KeyClerk engine itself will
be published as open source later under the same licence; until then this repository is the reference for edge
builders.

## Using the conformance set
Load `conformance/edge.json`. For each family, feed your implementation the case's inputs and compare with `expected`:
`verifier` (a sealed bundle, the pins, the edge's state and a moment, giving a verdict and the live leases),
`statements`, `ceilings`, `ended`, `unlock` and `module_bytes`; the top-level `cases` are inputs to the edge policy
modules named in `modules` by sha256. The keys in the set are fixed test seeds: never use them for anything else.

## Licence
EUPL-1.2 (European Union Public Licence, version 1.2): see [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Security and contributions
Report a vulnerability privately as [SECURITY.md](SECURITY.md) says, never in a public issue. Questions, ambiguities
and interoperability reports are welcome as issues; see [CONTRIBUTING.md](CONTRIBUTING.md).
