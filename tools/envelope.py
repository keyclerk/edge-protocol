# SPDX-License-Identifier: EUPL-1.2
"""A reference reader for section 4 of the edge protocol: the sealed object, canonical base64 and canonical JSON.
Standard library only; the Ed25519 check is the caller's (pass `verify`), since the standard library has no Ed25519.

    body = read_sealed(sealed, "kc-edge-bundle-v3", pinned_key, verify)

Raises ValueError, and nothing else, for anything the protocol refuses. The order is the protocol's: the envelope's
members, the pinned key and its key id, the signature over the decoded bytes, then the bytes parsed, re-encoded and
compared, then the format and the key id inside. Fuzzed by tools/fuzz_envelope.py; checked against the conformance
set by tools/check.py.
"""
import base64
import binascii
import hashlib
import json
import re

HEX64 = re.compile(r"[0-9a-f]{64}")
HEX128 = re.compile(r"[0-9a-f]{128}")
MEMBERS = {"bytes", "signature", "key", "key_id"}
MAX_INT = 2 ** 53 - 1


def key_id(key_hex: str) -> str:
    """The first 16 hex characters of the SHA-256 of the raw 32-byte key."""
    return hashlib.sha256(bytes.fromhex(key_hex)).hexdigest()[:16]


def decode_base64(text) -> bytes:
    """Signed bytes from canonical base64: standard alphabet, padded, no line breaks, no stray bits."""
    if not isinstance(text, str) or not text.isascii():
        raise ValueError("bytes: base64 text")
    try:
        raw = base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("bytes: not base64") from None
    if base64.b64encode(raw).decode("ascii") != text:
        raise ValueError("bytes: not canonical base64")
    return raw


def _plain(value):
    """What canonical JSON may hold: objects, lists, strings, whole numbers 0 to 2^53-1, booleans and null."""
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        if not 0 <= value <= MAX_INT:
            raise ValueError("an integer outside 0 to 2^53-1")
        return value
    if isinstance(value, list):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    raise ValueError(f"{type(value).__name__} is not part of a signed object")


def canonical(value) -> bytes:
    """Sorted keys, no spaces, UTF-8, no ASCII escaping."""
    return json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _no_float(text):
    raise ValueError("a float in signed bytes")


def _no_constant(text):
    raise ValueError(f"{text} in signed bytes")


def parse_canonical(raw: bytes) -> dict:
    """The object in signed bytes; refused unless re-encoding it gives the same bytes (this also refuses duplicate
    names, which a parser would silently collapse)."""
    try:
        text = raw.decode("utf-8")
        obj = json.loads(text, parse_float=_no_float, parse_constant=_no_constant)
        again = canonical(obj)
    except (UnicodeDecodeError, RecursionError):
        raise ValueError("the signed bytes are not canonical JSON") from None
    except ValueError as e:
        raise ValueError(f"the signed bytes are not canonical JSON: {str(e)[:80]}") from None
    if again != raw:
        raise ValueError("the signed bytes are not canonical JSON")
    if not isinstance(obj, dict):
        raise ValueError("the signed bytes hold an object")
    return obj


def read_sealed(sealed, fmt: str, pinned_key: str, verify) -> dict:
    """The object inside a sealed object signed by the pinned key, or ValueError.
    verify(key_hex, signature_hex, raw) -> bool: the Ed25519 check over the decoded bytes."""
    if not isinstance(sealed, dict) or set(sealed) != MEMBERS:
        raise ValueError("a sealed object is exactly {bytes, signature, key, key_id}")
    key, sig = sealed["key"], sealed["signature"]
    if not isinstance(key, str) or not HEX64.fullmatch(key) or key != pinned_key:
        raise ValueError("a wrong signer: not the pinned key")
    if sealed["key_id"] != key_id(key):
        raise ValueError("the key_id is not the pinned key's")
    if not isinstance(sig, str) or not HEX128.fullmatch(sig):
        raise ValueError("signature: 128 lower-case hex")
    raw = decode_base64(sealed["bytes"])
    if not verify(key, sig, raw):
        raise ValueError("a wrong signer: the signature does not verify over the bytes")
    obj = parse_canonical(raw)
    if obj.get("format") != fmt or obj.get("key_id") != key_id(key):
        raise ValueError(f"not a {fmt} signed by the pinned key")
    return obj
