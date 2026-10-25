# Changelog

## 1.1.0 (2026-10-25)
- The bundle may carry `governed_roles`, the edge roles KeyClerk governs on this edge, as SCIM 2.0 Group shapes
  `[{displayName, externalId?}]` (section 5). An edge can now tell a role KeyClerk governs from one it does not, and
  report a holder of a governed role who has no lease for it. Absent means no catalogue; a signed empty list means
  none governed. Built from KeyClerk 0.25.0.
- Verifiers refuse a malformed `governed_roles` (not a list of objects with a non-empty string `displayName` and an
  optional string `externalId`, a role named twice, or null).
- Stated explicitly: a verifier ignores a bundle member this version does not name; the ceiling and the officer's
  statements keep exactly their named members.
- Conformance: eight bundle-verifier cases for governed roles; every verifier case's expected output carries
  `governed_roles`.

## 1.0.0 (2026-10-24)
- First publication: trust pinned on site, enrolment, signed requests and objects, the bundle, policy in the edge,
  carried visit leases, phoned unlock, the lifecycle, TPM attestation and the conformance set, as KeyClerk 0.24.0
  ships them.
