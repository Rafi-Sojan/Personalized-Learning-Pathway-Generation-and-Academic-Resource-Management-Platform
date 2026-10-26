# Scoring Engine Specification

**Document ID:** ILR-CPP-001
**Version:** 1.0
**Status:** Development baseline
**Last reviewed:** 2026-10-27

## Purpose

The C++ engine ranks incomplete concepts by difficulty, learning gap, and prerequisite readiness. Build it with:

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build
```

The public headers under `include/scoring` define the native types and scorer contract. The executable under `src/main.cpp` is a demonstration boundary; the backend currently retains a Python integration/fallback path. Native deployment, ABI compatibility, benchmarking, and packaging are not yet production-approved.

For service integration, invoke `scoring-cli --stdin` with one record per line in the form `concept-id|difficulty|progress|prerequisite-ready` and read ranked records as `concept-id|score`. Configure the backend with `SCORING_ENGINE_PATH`.
