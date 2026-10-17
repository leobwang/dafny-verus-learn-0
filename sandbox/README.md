# sandbox/

The per-run agent sandbox's pinned inputs and its in-container and host-side
programs (DV4-PLAN §5). Guard rule 2g: written only in authoring mode.
`scripts/mksandbox-run` (library `scripts/dvl/sandbox.py`) reads them; it is the
one program that starts a sandbox container.

| file | content | built |
|---|---|---|
| `images.lock` | the sandbox images by digest; a manifest names its image from here | DV4 step 2a (`build-images.sh`) |
| `build-images.sh` | builds `dvl-toolchain` and `dvl-agent` from a staged context (never the checkout) and writes `images.lock`; `--check` compares the lock with the local images and the current inputs | DV4 step 2a |
| `images/toolchain.Dockerfile`, `images/agent.Dockerfile` | the two images: `ubuntu:24.04` by digest, packages from a dated Ubuntu snapshot, the pinned Dafny and Verus trees (checked inside the image by `get_toolchain.sh --check`), the Rust toolchain with rustup, user `agent` (uid 1000); the pinned uv and a uv cache seeded from `harness/uv.lock` (the Python acceptance tests run offline in the verification container), and the pinned age binary (the grader's); the agent image adds the pinned opencode binary | DV4 step 2a; uv, the wheels and age in the remainder lane |
| `image/entry.py` | `/opt/dvl/bin/entry`: the relays of Route B (127.0.0.1:11434 to `/run/dvl/ollama.sock`), then it waits; the host drives the run with `docker exec` | DV4 step 2a |
| `image/controls.py` | `/opt/dvl/bin/controls`: the in-container containment controls C1–C8 (`check`), and the doors of `tests/acceptance/sandbox_doors.py` (`door …`, `--probe` runs only) | DV4 steps 2a, 2d |
| `image/truthcheck.py` | `/opt/dvl/bin/truthcheck`: the grader container's truth mode (DV4-PLAN §5.9, QPLAN §30 Q49): unseals the bound archive in the container, checks it against its manifest, validates the references (`manifest`, `validate`), and judges candidates against them (`judge`: Lab 2's cards by the archive's own frozen reference oracles, `judge/oracles.py`; the prose items by a two-way refinement check; the host half is `scripts/dvl/judge.py`, the run `mksandbox-run --truth … --truth-check judge --judge SPEC`, and `fvh report --judge` for a lab's runs); prints verdict-level JSON only, and nothing on stderr | the remainder lane; `judge` in DV5d's judging lane |
| `hostside/ollama_gate.py` | the Ollama gate, one per run (Δ146): endpoint and model allowlists, pinned options, caps, counts, `gate.log`; the model's digest checked at start and the model unloaded at stop (`keep_alive` 0) when the run's config asks; the run's per-request seeds (`seeds`) and its owner process (`--owner-pid`) for the batch runner | DV4 step 2c; live with the model at step 3a; seeds and owner in the remainder lane |
| `truth.toml` | each lab's sealed archive (`Hidden/labs/<ID>/verdicts.tar.age`: path, sha256, recipient), the pinned age binary, and where the grader's key lives (outside the checkout, in the reference class); every archive carries the reference statements or specifications, a `DVLCANARY` and `judge/oracles.py` | the remainder lane (Q15); Q13 and Q17 by the DV5c gaps lane; re-sealed with the oracles by DV5d's judging lane |
| `seal_hidden.py` | author-only: seals a lab's plaintext truth (checked against its manifest) into its archive with the pinned age, and writes the pin | the remainder lane |
| `canaries.sha256` | canary tokens by hash, for the self-test's attribution | planted by the DV5c gaps lane (§14 Q5): a `DVLCANARY` file at the top of `Solutions/`, `paper/solutions/`, `tests/instructor/leak_patterns/`, `tests/instructor/fixtures/`, `Hidden/` and the author cache, and in each public set's `answers/` (written by `get_bench.sh`, outside the digest); `sandbox_doors.py canary` checks each tree's attribution |
| `attested.toml` | the lab task cards the author attested | 88 entries: 78 re-scanned 2026-10-14 under the scan's rule `DV6` (`mksandbox-run --author --attest-rescan`; 78 of 78 re-attested): whole and renamed copies of a twin's answer spans, generic structure, including shapes two or more public pool files show, set aside (the user's decision D25), and since DV6 Lab 2's sealed reference specifications and Lab 3's reference deliveries read as twins too, in memory only (D31); each entry names its `scan`, the `pools` and the sealed twins (`refs`) it read: Lab 1's 22 cards, Lab 2's 20 local cards and Lab 3's 36 sealed crate files (from the archive decrypted into memory, at the paths `fvh unseal Q18` writes), re-scanned again after Q15's DV6 re-seal (D27, D28; 78 of 78 re-attested), and Lab 2's ten public cards (`bench/local/q/lab2pub/`) attested under `DV6` after that re-seal; on 2026-10-17 vp3-he077's rebuilt form (its kept-definition marker moved author-side) was attested and every entry re-scanned (87 re-attested, 1 already current; vp3-he077's two earlier hashes stay as stale entries for older runs): 90 entries, 88 current |
| `apparatus.toml` | the apparatus pins `fvh` checks before every batch (DV4-PLAN §3.6); its `[model_server]` table is also the gate's pins for an agent run | DV4 step 3 (the Qwen side: `[backend.qwen]`, `[model_server]`); the Claude side (`[backend.claude]`, `[window]`) is step 4a's |
| `hostside/egress_proxy.py`, `claude/` | the egress proxy and Claude agent settings | DV4 step 4c, if Claude agent mode is kept |

Nothing here is copied into a sandbox: `sandbox/` is a refused source class.
The images carry `entry.py`, `controls.py` and `truthcheck.py` as built: a
change to one of them, to a Dockerfile, to the pinned uv or age, or to
`harness/uv.lock`, needs `build-images.sh` (new digests in `images.lock`, the
apparatus file's `images_lock_sha256`, and `VERSIONS.md` §1.4) and a run of
`tests/acceptance/sandbox_doors.py`.
