"""fvh.tools — one interface for every instrument run, host or container
(DV4-PLAN §3.7).

  INSTRUMENTS   the wrapper instruments of tests/corpus/README.md's table, by
                the same names: "vcheck --gate", "vaudit", "specfreeze --check",
                "witness", "swap-to-false", "seed-rerun"
  ToolResult    one instrument run on one target (fvh.tools.runners)
  Runner        execute(instrument, target, *, timeout_s=None) -> ToolResult;
                HostRunner, ContainerRunner, ReplayRunner
  run(instrument, target, *, root=None, timeout_s=None, runner=None,
      provenance=None) -> ToolResult
      one instrument on one target, in a fresh process. The target (a path,
      relative to the course root unless absolute) gets its provenance from
      the provenance rule (`provenance_of`); `provenance="agent"` (or
      "learner") raises it, and a request to lower it raises
      ProvenanceError. With no runner, a course or learner target runs on
      the host (HostRunner) and an agent target in the verification
      container (ContainerRunner). An agent target given to a runner that is
      not isolated raises ProvenanceError, so no gate runs an instrument on
      agent output on the host. A kill or a time-out comes back as such
      (`killed`), never as a pass.
  replay(fixture_id, instrument, *, root=None) -> ToolResult
      the recorded result of one instrument on one fixture, from
      harness/tests/q/fixtures/q09/<lang>/<ID>/<slug(instrument)>.json;
      fixture_id is "<ID>" or "<lang>/<ID>". NoRecording when there is none.
  provenance_of(target, *, root=None), command(instrument, target), slug(...)
      command() is the instrument's argv in tests/corpus/README.md's form;
      the paths it names besides the target are the companion files the
      instrument reads (the README's layout, which is public). A gate may
      compose it to learn which companions an instrument needs; whether a
      delivery brings them, and what a result means, is the gate's own work.

The recorded files are written only by the author-only recorder
`python -m fvh.tools.record` (fvh.tools.record). Frozen (guard rule 2f),
standard library only. Look `run` up at call time (`from fvh import tools`;
`tools.run(...)`), so that a test can replace it.
"""

import dataclasses

from fvh.tools.runners import (FIXTURES, INSTRUMENTS, KILLS, LANGS, PROVENANCES, RUNNERS,
                               ContainerRunner, HostRunner, NoRecording, PreflightError,
                               ProvenanceError, ReplayRunner, Runner, RunnerUnavailable,
                               ToolResult, _real, _root, command, higher, provenance_of,
                               raise_provenance, read_recording, recording_path, slug)

__all__ = ["FIXTURES", "INSTRUMENTS", "KILLS", "PROVENANCES", "RUNNERS", "ContainerRunner",
           "HostRunner", "NoRecording", "PreflightError", "ProvenanceError", "ReplayRunner",
           "Runner", "RunnerUnavailable", "ToolResult", "command", "provenance_of", "replay",
           "run", "slug"]


def run(instrument: str, target, *, root=None, timeout_s=None, runner=None,
        provenance=None) -> ToolResult:
    """One instrument on one target under the provenance rule (module docstring)."""
    if instrument not in INSTRUMENTS:
        raise ValueError(f"{instrument!r} is not an instrument fvh.tools runs "
                         f"({', '.join(INSTRUMENTS)})")
    root = _root(root)
    real = _real(target, root)
    prov = raise_provenance(provenance_of(real, root=root), provenance)
    if runner is None:
        runner = ContainerRunner(root) if prov == "agent" else HostRunner(root)
    if prov == "agent" and not getattr(runner, "isolated", False):
        raise ProvenanceError(f"{target}: a target of agent provenance runs only in the "
                              "verification container (ContainerRunner), never through "
                              f"{type(runner).__name__}")
    res = runner.execute(instrument, str(real), timeout_s=timeout_s)
    if not isinstance(res, ToolResult):
        raise TypeError(f"{type(runner).__name__}.execute returned {type(res).__name__}, "
                        "not a ToolResult")
    if res.instrument != instrument:
        raise ValueError(f"{type(runner).__name__} answered {res.instrument!r} for "
                         f"{instrument!r}")
    return dataclasses.replace(res, provenance=higher(prov, res.provenance))


def replay(fixture_id: str, instrument: str, *, root=None) -> ToolResult:
    """The recorded result of one instrument on one fixture (module docstring)."""
    slug(instrument)
    base = _root(root) / FIXTURES
    if not isinstance(fixture_id, str) or not fixture_id:
        raise ValueError("fixture_id must be a non-empty string")
    if "/" in fixture_id:
        lang, fid = fixture_id.split("/", 1)
        if lang not in LANGS:
            raise ValueError(f"{fixture_id!r}: the language must be one of {', '.join(LANGS)}")
        found = [(lang, fid)]
    else:
        found = [(lang, fixture_id) for lang in LANGS if (base / lang / fixture_id).is_dir()]
        if len(found) > 1:
            raise ValueError(f"{fixture_id!r} names a fixture in more than one language; "
                             "write <lang>/<ID>")
        if not found:
            raise NoRecording(f"no recorded fixture {fixture_id!r} under {base}")
    path = recording_path(base, found[0][0], found[0][1], instrument)
    if not path.is_file():
        raise NoRecording(f"no recorded result of {instrument} on {found[0][0]}/{found[0][1]} "
                          f"({path.name} under {path.parent})")
    return read_recording(path)
