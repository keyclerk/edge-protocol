# The KeyClerk edge protocol

How an edge agent works with a KeyClerk desk: the trust it pins, the requests it signs, the bundles it verifies and
the calls it makes. An edge is a small appliance at a site that admits people to systems behind it on the strength
of leases the desk has signed, and keeps doing so for a bounded time when the desk is out of reach.

Status: version 1 of the formats named below (`kc-edge-bundle-v3`, `kc-edge-ceiling-v2`, `kc-edge-officer-v2`,
`kc-edge-ended-v2`, `kc-unlock-v2` and the others in section 4), as shipped with KeyClerk 0.24.0; version 1.1 adds the optional `governed_roles` member of the
bundle (section 5), and version 1.2 the bundle long-poll (section 5), both from KeyClerk 0.25.0. The conformance set
in `conformance/edge.json` holds the vectors every implementation must reproduce. Words like "must" are normative. A verifier ignores a member of the bundle body that this version does not name, so an
optional bundle member can be added without a new format name. Other signed objects (the ceiling, the officer's
statements) have exactly the members named, and an extra one is refused.

## 1. Trust, pinned on site
An edge pins three keys at installation, from people, never from the desk:

| Pin | From | Used for |
|---|---|---|
| `bundle_key` | the desk's operator reads `key_id` from `GET /api/v1/edge-key` aloud; the installer compares it before pinning | bundles, acknowledgements, escrow status |
| `officer_key` | the edge's officer, from their hardware key | the ceiling inside every bundle |
| `release_key` (optional) | the deployment's release owner | the policy release manifest |

The edge also keeps its own floors: the highest bundle serial applied, the newest signed time seen, and the highest
ceiling serial held. Losing them means reinstalling, never resetting.

## 2. Enrolment
1. The edge makes its Ed25519 enrolment key and a P-256 key for phoned unlock, inside its TPM where it has one.
2. The officer and the edge sign one statement over the same bytes: a multi-signed `kc-edge-officer-v2` with purpose
   `enrolment`, naming the edge, the officer, the officer's key and each node as `{enrolment_key, unlock_key, tpm}`
   (the TPM commitment of section 12, or null). One node, or two for a high-availability edge.
3. The desk's root proposes the enrolment with the statement, the same values outside it, the targets (`target`,
   `role`, `entitlement`, optional `max_session_hours`) and the escrow custodians (two or more people); the security
   officer's key completes it. The desk checks the statement's signatures over its bytes and that it says exactly what
   the record holds. The officer is never the root, the security officer or a member of a privileged group, and this
   is checked again at every ceiling and every bundle. An edge id that has ended is never enrolled again: a reinstalled
   machine gets a new id.
4. The officer seals a ceiling and sets it on the desk. Without a ceiling the edge receives no leases.

## 3. Signed requests
Every call under `/api/v1/edge/` carries `KeyClerk-Edge: <edge>;<unix seconds>;<nonce>;<signature hex>`, the Ed25519
signature of the enrolment key over

```
kc-edge-request-v2 \n <edge> \n <METHOD> \n <path with query> \n <seconds> \n <nonce> \n <sha256(body) hex>
```

Clock skew at most 5 minutes; a nonce (16 to 64 base64url characters) is accepted once. No session, cookie or token is
ever accepted on these routes.

## 4. Signed objects
One signing mode: every signature is over exact bytes, and no verifier ever serialises a document to check a
signature. Two shapes:
- **sealed** `{"bytes": base64(canonical JSON), "signature": hex, "key": hex, "key_id": hex16}`, exactly these members;
  the object inside names its `format` and the signer's `key_id`. Formats: `kc-edge-bundle-v3`, `kc-edge-ceiling-v2`
  (sealed by the officer), `kc-edge-ended-v2`, `kc-edge-carried-v1`, `kc-edge-key-rollover-v1`,
  `kc-edge-escrow-ack-v1`, `kc-edge-escrow-status-v1`, `kc-edge-evidence-ack-v1`, `kc-policy-release-v1`.
- **multi-signed** `{"bytes": ..., "signatures": [{"key", "key_id", "signature"}]}`: signed by exactly the keys named
  (each once, no other); the object inside names its `format`. Format: `kc-edge-officer-v2`.

Canonical JSON: sorted keys, no spaces, UTF-8, integers 0 to 2^53-1 and strings only (no floats). Base64 is canonical
(no stray padding or trailing bits), signatures are 128 lower-case hex. Verify each signature over the decoded bytes,
then parse, re-encode and compare with the bytes (a non-canonical body is refused even when signed), then check
`format` and `key_id`. The re-encoding check guards the parse, never the signature.

## 5. The bundle
`GET /api/v1/edge/bundle` returns a sealed `kc-edge-bundle-v3` (a few KB):

```
edge, serial, issued, horizons {class: hours}, revoked [visit lease ids],
leases [{lease_id, person, username, email, key_id, public_key, target, role, class, roles, from, until, max_session_hours}],
visit_leases [{lease_id, person, username, key_id, public_key, ssh_key, targets, role, from, until}],
ceiling (the officer's sealed kc-edge-ceiling-v2, exactly as sealed) | null,
policy {modules {edge, ceiling: {sha256}}, release (sealed manifest) | null, entrypoints},
governed_roles [{displayName, externalId?}] (optional, version 1.1)
```

The newest bundle is complete: anything the edge holds that is not in it has ended. A verifier refuses: a wrong
signer; another edge's bundle; a serial at or below the floor; an issue time in the future or before the newest
signed time; a clock before the newest signed time; leases without a ceiling; a ceiling not signed by the pinned
officer key or below the ceiling floor; with a pinned release key, modules the manifest does not name; a module named
by anything but a 64 lower-case hex sha256. The agent fetches a module it does not hold by
`GET /api/v1/edge/module/{sha256}` (`{name, sha256, wasm}`), checks the bytes against the hash and keeps it by hash,
so a module crosses the network once per policy change, not at every pull.

A lease is live while `from <= now < until`, it is not revoked, it passes the ceiling policy, and the bundle is younger
than `min(horizon of its class, ceiling.max_offline_hours)`. A lease of a class without a horizon is never live. A
visit lease lives in its own window, passes the ceiling policy too
(kind visit: its window within `ceiling.max_offline_hours`, and an edge assured by its ceiling and its own
attestation), and is not revoked. A lost answer: `GET /api/v1/edge/bundle?serial=N` returns the same bundle.

Waiting for the next bundle (version 1.2): `GET /api/v1/edge/bundle?after=<serial>&wait=<seconds>`, both in
the signed path. `after` is the serial of the newest bundle the edge accepted, `wait` whole seconds from 1, held to
at most 55. The desk answers when this edge's bundle says something other than the bundle with serial `after` said
(leases, visit leases, revocations, ceiling, policy, governed roles; never serial, issue time, format or key id), or
when the wait ends, and always with a newly issued bundle, so a timed-out wait renews the offline horizon as a pull
does. It answers at once when the content already differs, when it does not know `after`, or when it holds its cap
of open waits. An edge holds at most one open wait per node; a new one answers the oldest. `serial` with `wait`, and a
malformed `wait`, are refused. Without `wait`, a pull is as in version 1.1; an older desk answers at once, which is a
plain pull. After an immediate answer an edge waits its normal pull interval before waiting again.

Governed roles (version 1.1): `governed_roles`, when present, lists the edge roles KeyClerk governs on this edge as
SCIM 2.0 Group shapes (RFC 7643 section 4.2), `[{displayName, externalId?}]`, each role once: the roles the edge's
enrolled targets map to. It shares the bundle's signature and serial floor, so a replayed bundle cannot shrink it.
Absent means no catalogue: the edge uses its own list of governed roles and never reads the absence as "none
governed". Present and empty means none governed here. A holder of a governed role without a live lease or visit
lease for it is drift, which the edge reports and never removes. A verifier must refuse the bundle when
`governed_roles` is present but is not a list of objects with a non-empty string `displayName`, an optional string
`externalId` and no other member, or names a role twice; null is refused, never read as absent. An edge that does
not implement version 1.1 ignores the member.

Acting on it: a role assignment per live lease (`username`, `role`, `until`); sessions approved only for a live lease
or visit lease of that person and target (the `admit` policy), ended at `max_session_hours` and at lease end; visit
leases install `ssh_key` for `username` until `until`. A lease's `email` is the identity broker's verified address, or
null when it has none verified; it exists for access gateways that match a single sign-on login by e-mail, and is in
leases only, on the edges where that person holds one.

## 6. Policy in the edge
`edge.wasm` (entrypoints `keyclerk/edge/settings`, `admit`, `visit_window`, `attestation`) and `ceiling.wasm`
(`keyclerk/ceiling/decision`) are named in the bundle by hash and fetched by hash; evaluate them in process (any
WebAssembly runtime that runs OPA's compiled policies). `settings` gives the horizons, `visit_max_hours`,
`local_window_hours` and `session_max_hours`. Run `conformance/edge.json` against the modules you load.

## 7. Calls an edge makes

| Call | Body | Answer |
|---|---|---|
| `POST /edge/report` | `{applied_serial, attestation {profile, ...}, drift [text]}` | `{ok}`; the profile is claimed until quotes are verified; a change raises an incident |
| `POST /edge/relay` | `{key_id, envelope, purpose: "lease:<id>"}` to a holder of that lease; envelope context equal to purpose | `{relay_id}` |
| `POST /edge/escrow` | `{system, item_id, envelopes [{key_id, envelope}] x2}` to designated custodians; context `escrow:<system>:<item>` | sealed escrow ack |
| `GET /edge/escrow/{item}` | | sealed status; forget the value only when `confirmed` |
| `POST /edge/incident` | `{kind, system, at, detail, log_sha256}`; kinds `break_glass_used`, `drift`, `evidence_floor`, `bind_without_session`, `other` | `{incident_id}` |
| `POST /edge/evidence` | `{entries [{seq, prev, sha256, size, session, at}]}`, a chain: `prev` is sha256 of the previous entry's canonical bytes | sealed ack up to a sequence; a resend is no change |
| `GET /edge/evidence` | | sealed head |

## 8. Envelopes to people
`kc-relay-v1`: `{format, epk, nonce, ct, context}`: X25519 with a fresh key, HKDF-SHA256 (salt `epk || recipient`,
info `kc-relay-v1|` + context), AES-256-GCM with the context as associated data. The recipient key is the lease's
`public_key`. People take it in the desk after a fresh sign-in and open it in the browser with the key their passkey
derives; nothing is deleted until they confirm.

## 9. Carried visit leases
A person with a visit lease takes a carried lease from the desk after a fresh sign-in: a sealed `kc-edge-carried-v1`
with `edge, lease_id, person, username, ssh_key, targets, role, from, until, carried_serial, nonce`, at most
`carried_max_hours` (24 by default) inside the visit lease's window. The edge accepts it at its local port when it
verifies (its own edge, inside the window, `carried_serial` above the floor it keeps per person) and the person proves
the SSH key with a signature over a challenge.

## 10. Phoned unlock (`kc-unlock-v2`)
Each node of an edge has a P-256 `unlock_key`, inside its TPM where it has one (TPMs offer P-256, not Curve25519),
named in the statement the officer and the edge sign; the desk's root names the people who may approve an unlock. The
node pins the desk's `unlock_key` from `GET /edge-key` (`unlock_format: kc-unlock-v2`). Keys travel as the uncompressed
SEC1 point (65 bytes, `04 x y`), base64url without padding. Both sides compute

```
z      = ECDH-P256(own private, other public)      (on a TPM: TPM2_ECDH_ZGen; z is the x coordinate)
secret = HKDF-SHA256(z, salt none, info "kc-unlock-v2|" edge "|" node "|" desk_unlock_key "|" node_unlock_key)
code   = base32(HMAC-SHA256(secret, "kc-unlock-v2|edge|node|person|fingerprint|target|nonce|minutes"))[:10]
```

where `node` is the key id of the node's enrolment key; no field holds a `|` or a line break. Nothing secret crosses
the network. The node shows person, target, the hardware key's fingerprint, a nonce and its node id; an approver who is
not that person enters them at the desk (within the policy's `unlock_max_minutes` and `unlock_per_hour` per edge) and
reads the code over a call-back. The node recomputes it. Every unlock is a logged change and an incident.

## 11. The lifecycle
- **Rotation**: the root or the officer proposes, the security officer's key completes; a new enrolment key, unlock key
  or officer, the (new) officer and the edge cosigning a statement with purpose `rotation` that states the node whole.
  The old enrolment key stops at once.
- **Ended**: an ended edge's signed requests are answered `410` with a sealed `kc-edge-ended-v2`
  `{edge, ended, reason, enrolment_keys [key ids]}`: revocation, not an outage. The agent acts on it only when it
  verifies: the pinned bundle key, its own edge id, and its own enrolment key's id in `enrolment_keys`, so a captured
  notice never ends a later enrolment.
- **Silence**: no pull for `pull_max_hours` (24 by default) raises one silence incident at the desk.
- **Incidents**: up to 60 an hour from an edge; the officer or the security officer closes them.
- **Bundle key rollover**: `GET /edge-key` carries `rollover` when the key changed: a sealed `kc-edge-key-rollover-v1`
  signed by the old key naming the new; the edge checks it against its pin.

## 12. TPM attestation
An assured edge proves three things; until it has, it gets what a basic edge gets (no visit leases, no offline grants).
- **Enrolment.** The enrolment carries `tpm`: `ek_public` (the EK's SubjectPublicKeyInfo, base64 DER, RSA 2048),
  `ek_sha256` (the fingerprint the officer reads on site), `ek_cert` (base64 DER, where the TPM has one), `ak_public`
  (the AK's TPM2B_PUBLIC, base64: a restricted signing key fixed to its TPM) and `pcr_baseline` (`{"7": hex}`). The
  officer and the edge sign the enrolment statement with the commitment in it: `tpm: {ek_sha256, ak_name, pcr_baseline}`.
- **Activation.** `GET /edge/attest/challenge` checks the EK (the officer's pin, and where there is a certificate its
  chain to the deployment's EK roots) and answers `{credential, id_object, encrypted_secret, expires_at}`:
  TPM2_MakeCredential to the EK for the AK's name, framed as `tpm2_activatecredential -i` reads it. The edge recovers
  the secret with TPM2_ActivateCredential and sends `POST /edge/attest/activate {secret: base64}` within 10 minutes. A
  wrong answer burns the challenge and raises an attestation incident.
- **Every pull.** `GET /edge/bundle` carries `KeyClerk-Quote: base64(message).base64(signature).base64(values)`, as
  `tpm2_quote -m -s -o -F values` writes them, over the SHA-256 PCR bank, with the qualifying data
  `sha256("kc-edge-quote-v1|<edge>|<seconds>|<nonce>")` from the same request's `KeyClerk-Edge` header. The policy
  (`attestation`, default PCR 7) compares the quoted PCRs with the baseline the officer signed. A changed PCR, a stale
  quote or no quote: the bundle is a basic edge's, and an attestation incident is raised once per new reason.

## 13. Conformance
`conformance/edge.json`: the policy cases, the bundle verifier, and the families `statements` (multi-signed),
`ceilings` (sealed), `ended`, `unlock` (both sides reach one code, or both refuse) and `module_bytes`. Keys in it are
fixed test seeds; never use them for anything else. An implementation conforms when it gives every recorded verdict.
