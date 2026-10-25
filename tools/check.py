# SPDX-License-Identifier: EUPL-1.2
"""Checks this repository holds together: the conformance set parses, the section 4 reader (tools/envelope.py) agrees
with the bundle verifier's recorded verdicts, every file RELEASE.txt lists has the hash it lists, and every relative
link in the Markdown files points at a file that exists. Standard library only.

    python3 tools/check.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\]\(([^)\s]+)\)|(?:src|srcset|href)=\"([^\"]+)\"")


# Bundle cases refused for their envelope or signed bytes alone: the section 4 reader must refuse each of them.
ENVELOPE_REFUSALS = ("a fractional float", "NaN in the signed", "an upper-case signature", "non-zero trailing bits",
                     "an outer key_id", "non-canonical signed bytes", "a duplicate name", "a float in the signed",
                     "another format inside", "a key id that is not", "a sealed bundle with an extra member",
                     "with a line break inside", "a wrong signer")


def envelope_errors(conformance: dict) -> list[str]:
    """The reader accepts every bundle the verifier accepts, and refuses every envelope-level refusal. Signatures are
    not checked here (no Ed25519 in the standard library): the reference verifier's verdicts already include them."""
    sys.path.insert(0, str(ROOT / "tools"))
    sys.dont_write_bytecode = True                       # no __pycache__ left in the checkout
    import envelope
    errors, seen = [], set()
    for c in conformance["verifier"]["cases"]:
        try:
            envelope.read_sealed(c["sealed"], "kc-edge-bundle-v3", c["pins"]["bundle_key"], lambda *_: True)
            read = True
        except ValueError:
            read = False
        refusal = next((r for r in ENVELOPE_REFUSALS if r in c["name"]), None)
        if refusal:
            seen.add(refusal)
        if c["expected"]["ok"] and not read:
            errors.append(f"envelope: the reader refuses an accepted bundle ({c['name']})")
        if refusal and read:
            errors.append(f"envelope: the reader accepts an envelope the verifier refuses ({c['name']})")
    errors += [f"envelope: no case named like {r!r}" for r in ENVELOPE_REFUSALS if r not in seen]
    return errors


# Every outside standard or product the specification names is cited at its first mention, and every citation has a
# reference with a link (CONTRIBUTING.md, "References"). A term found in the text needs its tag in the same paragraph
# the first time it appears; terms the specification does not use are not required.
TERMS = {
    "Ed25519": "RFC8032", "X25519": "RFC7748", "P-256": "SP800-186", "ECDH": "SP800-56A", "HKDF": "RFC5869",
    "HMAC": "RFC2104", "SHA-256": "FIPS180-4", "base32": "RFC4648", "base64": "RFC4648", "AES-256-GCM": "SP800-38D",
    "SCIM": "RFC7643", "TPM": "TPM2", "tpm2_": "TPM2-TOOLS", "WebAssembly": "WASM", "OPA": "OPA-WASM",
    "JSON": "RFC8259", "passkey": "WEBAUTHN", "Keycloak": "KEYCLOAK", "SEC1": "SEC1",
}
CITE = re.compile(r"\[([A-Z][A-Z0-9-]*[0-9A-Z])\]")
ENTRY = re.compile(r"^- \[([A-Z][A-Z0-9-]*)\] (.+)$")


def reference_errors(text: str) -> list[str]:
    errors = []
    body, sep, refs = text.partition("\n## References")
    if not sep:
        return ["edge-protocol.md: no References section (normative and informative, each entry with a link)"]
    entries, current = {}, None
    for line in refs.splitlines():
        m = ENTRY.match(line)
        if m:
            current = m.group(1)
            entries[current] = m.group(2)
        elif current and line.startswith("  "):
            entries[current] += " " + line.strip()
        else:
            current = None
    for tag, entry in entries.items():
        if "<https://" not in entry:
            errors.append(f"References: [{tag}] has no https link")
    if "### Normative" not in refs or "### Informative" not in refs:
        errors.append("References: split into ### Normative and ### Informative")
    prose = re.sub(r"```.*?```", "", body, flags=re.S)                # code blocks are not prose
    paragraphs = [p for p in re.split(r"\n\s*\n", prose) if p.strip()]
    cited = set(CITE.findall(prose))
    for tag in sorted(cited - set(entries)):
        errors.append(f"edge-protocol.md: [{tag}] is cited but has no reference")
    for tag in sorted(set(entries) - cited):
        errors.append(f"References: [{tag}] is never cited")
    for term, tag in TERMS.items():
        first = next((p for p in paragraphs if term in p), None)
        if first is not None and f"[{tag}]" not in first:
            errors.append(f"edge-protocol.md: {term} first appears without [{tag}] in its paragraph")
    return errors


def main() -> int:
    errors = []
    try:
        conformance = json.loads((ROOT / "conformance" / "edge.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        conformance = None
        errors.append(f"conformance/edge.json does not parse: {e}")
    if conformance is not None:
        errors += envelope_errors(conformance)
    errors += reference_errors((ROOT / "edge-protocol.md").read_text(encoding="utf-8"))
    listed = re.findall(r"^  (\S+)  sha256 ([0-9a-f]{64})$", (ROOT / "RELEASE.txt").read_text(encoding="utf-8"), re.M)
    if not listed:
        errors.append("RELEASE.txt lists no files")
    for name, digest in listed:
        f = ROOT / name
        if not f.is_file():
            errors.append(f"{name}: listed in RELEASE.txt, missing")
        elif hashlib.sha256(f.read_bytes()).hexdigest() != digest:
            errors.append(f"{name}: differs from the hash in RELEASE.txt")
    for md in sorted(ROOT.rglob("*.md")):
        for m in LINK.finditer(md.read_text(encoding="utf-8")):
            target = (m.group(1) or m.group(2)).split("#", 1)[0]
            if not target or re.match(r"^[a-z]+:", target):
                continue
            if not (md.parent / target).exists():
                errors.append(f"{md.relative_to(ROOT).as_posix()}: link to {target}, which does not exist")
    for e in errors:
        print(e)
    print(f"{len(listed)} files checked against RELEASE.txt; {'no' if not errors else len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
