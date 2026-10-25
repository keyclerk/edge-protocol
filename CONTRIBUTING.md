# Contributing

Issues are welcome: a question about the specification, a place where it is ambiguous or where two readings are
possible, or an interoperability report (your edge and the vectors disagree, with the case name).

Pull requests are not accepted yet. KeyClerk will ask outside contributors to accept a contributor licence agreement,
which is being prepared; until it is published, please open an issue instead, and a change you propose there may be
made by the maintainers.

AI-assisted work says so: a pull request, once they are open, states its level of AI use.

## What every change carries
- **A change to the protocol comes with conformance vectors.** New behaviour, or a new refusal, is a case in
  `conformance/edge.json` whose verdict comes from the reference implementation, never written by hand, and a line in
  `CHANGELOG.md` under the version it lands in.
- **A change to `tools/` keeps the checks green:** `python3 tools/check.py` (the vectors, the section 4 reader against
  them, the release hashes, the links), `ruff check tools` with no warnings (`ruff.toml`), `reuse lint`, and the fuzz
  target in `tools/fuzz_envelope.py` still stating what must hold.
- **The specification cites what it builds on.** Every outside standard or product `edge-protocol.md` names is cited
  with a tag such as `[RFC8032]` in the paragraph where it first appears, and every tag has an entry under
  References (Normative: what an implementation must follow; Informative: context) with an https link. `tools/check.py`
  checks it, including entries no longer cited. A new term goes into its `TERMS` table with its tag.
- CI runs all of these on every pull request, and fuzzes the reader for two minutes. A pull request merges only with
  every check green and the branch up to date.
