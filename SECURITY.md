# Security

If you find a weakness in the edge protocol or in a conformance vector (a way to make an edge accept a bundle,
statement, notice or unlock code it should refuse, or to make two conforming implementations disagree), report it
privately through this repository's "Report a vulnerability" button (GitHub private vulnerability reporting:
<https://github.com/keyclerk/edge-protocol/security/advisories/new>), never in a public issue. You get an answer within five working days. Fixes are prepared in private and published with a new
format version or new vectors, and the report is credited unless you ask otherwise.

The protocol's own defences are in the specification: exact-byte signatures with one signing mode, keys pinned on
site by people, serial and time floors kept by the edge, complete bundles, horizons that bound offline use, and
notices bound to the enrolment they end.

## Supported versions

| Version | Supported |
|---|---|
| 1.3 | yes: fixes and new vectors |
| 1.0 to 1.2 | verifiable: a 1.3 verifier still accepts their formats, but they get no new vectors |
