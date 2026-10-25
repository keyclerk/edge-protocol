#!/bin/bash -eu
# SPDX-License-Identifier: EUPL-1.2
# Every tools/fuzz_*.py becomes a fuzz target (compile_python_fuzzer is OSS-Fuzz's, from the base image).
cd "$SRC/edge-protocol/tools"
for fuzzer in fuzz_*.py; do
  compile_python_fuzzer "$fuzzer"
done
