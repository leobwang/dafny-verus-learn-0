"""dvl — the course's pinned verifier wrappers (phase DV1b).

Import it with scripts/ on sys.path:

    import dvl.common, dvl.dafny, dvl.verus

  dvl.common   shared types (Diag, Hole, Finding, Result), the one pinned-settings
               source (load_pins, reading scripts/dvl/pins.toml), the pinned
               toolchain paths (toolchain) and the memory-capped runner
               (run_capped). Every Dafny and Verus job runs through run_capped.
  dvl.dafny    the Dafny side: verify, holes, audit, lint, spec_hash,
               freeze_check, test, empty_body.
  dvl.verus    the Verus side, the same interface.
  dvl.python   the learner Python files (DV4): holes through the frozen core's
               AST counter, lint, audit, spec_hash, test (pytest, offline, on
               the pinned uv lock), check, ref_check, empty_body (TRIV mode).
  dvl.forms    per-item construct forms (DV3b, QPLAN §6 Q43): the `// form:`
               vocabulary, its static checks and the twins' `// cfree:`
               bodies (pure text; firsttry runs `stable`'s sweep).

The package never prints. Callers (scripts/vcheck, scripts/vaudit, pins.py,
firsttry) print locations, never content that could be an answer.
"""

import sys as _sys

if _sys.version_info < (3, 12):      # tomllib (3.11) and the harness's floor (3.12)
    raise SystemExit(f"the course tools need Python >= 3.12, not {_sys.version.split()[0]}; "
                     "see README.md, Platforms (macOS: uv python install 3.12)")

