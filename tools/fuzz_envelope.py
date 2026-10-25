# SPDX-License-Identifier: EUPL-1.2
"""Fuzzes the section 4 reader (tools/envelope.py) with Atheris, under ClusterFuzzLite (.clusterfuzzlite/).

Two shapes of input, chosen by the first byte: the rest as a whole sealed object in JSON (the envelope's own checks),
or the rest as the signed bytes inside a well-formed envelope (the canonical JSON checks; the signature check is
stubbed to pass so the fuzzer reaches the parser). What must hold for every input:
- the reader raises ValueError and nothing else;
- what it accepts is canonical: re-encoding the object gives exactly the signed bytes, the object names the format and
  the key id, and reading it again gives the same object.
"""
import base64
import sys

import atheris

with atheris.instrument_imports():
    import json

    import envelope

KEY = "11" * 32
FMT = "kc-edge-bundle-v3"


def _signed(_key, _sig, _raw) -> bool:
    return True


def _wrap(raw: bytes) -> dict:
    return {"bytes": base64.b64encode(raw).decode("ascii"), "signature": "ab" * 64, "key": KEY,
            "key_id": envelope.key_id(KEY)}


def test_one_input(data: bytes) -> None:
    if not data:
        return
    mode, rest = data[0] % 2, data[1:]
    if mode == 0:
        try:
            sealed = json.loads(rest.decode("utf-8", errors="replace"))
        except (ValueError, RecursionError):
            return
    else:
        sealed = _wrap(rest)
    try:
        obj = envelope.read_sealed(sealed, FMT, KEY, _signed)
    except ValueError:
        return
    raw = envelope.decode_base64(sealed["bytes"])
    assert envelope.canonical(obj) == raw, "accepted bytes that do not re-encode to themselves"
    assert obj["format"] == FMT and obj["key_id"] == envelope.key_id(KEY), "accepted another format or key id"
    assert envelope.read_sealed(_wrap(raw), FMT, KEY, _signed) == obj, "a second reading differs"


def main() -> None:
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
