"""fvh.apparatus — the apparatus pins, the apparatus facts, and the refusal on
drift (DV4-PLAN §3.6; design §11.1: "records carry CLI version, model id,
prompt hash, Ollama digest and sandbox manifest").

The apparatus file is the file FVH_APPARATUS names, else sandbox/apparatus.toml
(guard rule 2g). Every binary path and upstream address fvh uses comes from
it, never from a default in code (DV4-PLAN §9). Its schema 1:

  schema = 1
  [defaults]          per-run caps of a non-lab run (fvh.budget.Caps' units)
  [window]            fvh.budget.WindowRule: allowed_overage, allowed_status,
                      five_hour_max, seven_day_max, max_age_s
  [backend.<family>]  one model transport per family (fvh.budget.FAMILIES):
                      binary (a path written "~/...", relative to HOME, so
                      that under CI's empty HOME it does not exist), sha256,
                      version, and the transport's own keys (fvh.backends)
  [model_server]      the local model server's pins: version, models (tag ->
                      full digest), the unit's settings, the request options
  [pins]              optional sha256 pins of course files the apparatus
                      depends on: toolchain (scripts/dvl/pins.toml),
                      images_lock (sandbox/images.lock)

  load(path=None, *, root=None) -> Apparatus      ApparatusError when the file
      is missing, unreadable or not schema 1 (every batch then refuses)
  resolve_binary(spec) -> Path    "~/..." under $HOME; anything else refused
  check_binary(table) -> Path     the pinned binary, its sha256 checked (fvh
      checks it before every exec); ApparatusMismatch on a difference
  collect(app, root) -> dict      the facts every record carries
  check(app, root) -> list[Drift] the differences between the host and the
      pins; `fvh apparatus --check` refuses a batch (exit 3) on any, naming
      the field, both values and what to re-probe
  prompt_hash(system, message, schema, policy_source) -> sha256

Frozen (guard rule 2f), standard library only.
"""

import hashlib
import inspect
import json
import os
import subprocess
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from fvh import budget

__all__ = ["Apparatus", "ApparatusError", "ApparatusMismatch", "DEFAULT", "Drift", "ENV",
           "SCHEMA", "check", "check_binary", "collect", "file_sha256", "git_facts", "load",
           "location", "prompt_hash", "resolve_binary", "source_sha256"]

ENV = "FVH_APPARATUS"
DEFAULT = "sandbox/apparatus.toml"
SCHEMA = 1
ROOT = Path(__file__).resolve().parents[2]
_TOP = {"schema", "defaults", "window", "backend", "model_server", "pins"}
_PIN_FILES = {"toolchain": "scripts/dvl/pins.toml", "images_lock": "sandbox/images.lock"}
REPROBE = {
    "binary": "the pinned binary changed or is missing (an auto-update?): re-run the policy "
              "probes of VERSIONS.md §2.3 and re-pin, never run on the new version silently",
    "version": "the pinned version file is another version: re-probe and re-pin",
    "toolchain": "scripts/dvl/pins.toml changed: re-run get_toolchain.sh --check and re-pin",
    "images_lock": "sandbox/images.lock changed: re-run the sandbox doors and re-pin",
}


class ApparatusError(RuntimeError):
    """The apparatus file is missing, unreadable or invalid: no batch runs (exit 3)."""


class ApparatusMismatch(RuntimeError):
    """The host differs from a pin, or a call's own assertions failed: the batch
    stops as `apparatus-mismatch`; never an attempt."""


@dataclass(frozen=True)
class Drift:
    field: str
    pinned: str
    found: str
    reprobe: str

    def line(self) -> str:
        return f"{self.field}: pinned {self.pinned}, found {self.found} ({self.reprobe})"


def location(root=None) -> Path:
    env = os.environ.get(ENV)
    if env:
        return Path(env)
    return Path(root if root is not None else ROOT) / DEFAULT


class Apparatus:
    """The parsed apparatus file."""

    def __init__(self, path: Path, data: dict):
        self.path = path
        self.data = data
        self.sha256 = file_sha256(path)

    def backend(self, family: str) -> dict:
        t = (self.data.get("backend") or {}).get(family)
        if not isinstance(t, dict):
            raise ApparatusError(f"{self.path}: no [backend.{family}] table")
        return dict(t)

    def families(self) -> tuple:
        return tuple(sorted((self.data.get("backend") or {})))

    def defaults(self) -> budget.Caps:
        try:
            return budget.Caps.from_mapping(self.data.get("defaults"))
        except ValueError as e:
            raise ApparatusError(f"{self.path}: [defaults]: {e}") from None

    def window(self) -> budget.WindowRule:
        try:
            return budget.WindowRule.from_mapping(self.data.get("window"))
        except (TypeError, ValueError) as e:
            raise ApparatusError(f"{self.path}: [window]: {e}") from None

    def model_server(self) -> dict:
        t = self.data.get("model_server")
        return dict(t) if isinstance(t, dict) else {}


def load(path=None, *, root=None) -> Apparatus:
    p = Path(path) if path is not None else location(root)
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ApparatusError(f"no apparatus file at {p} (set {ENV}, or pin {DEFAULT}): no "
                             "batch runs without its pins") from None
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise ApparatusError(f"{p}: unreadable apparatus file ({type(e).__name__})") from None
    if data.get("schema") != SCHEMA:
        raise ApparatusError(f"{p}: schema {data.get('schema')!r}, not {SCHEMA}")
    unknown = set(data) - _TOP
    if unknown:
        raise ApparatusError(f"{p}: unknown table(s) " + ", ".join(sorted(unknown)))
    back = data.get("backend", {})
    if not isinstance(back, dict) or not all(isinstance(t, dict) for t in back.values()):
        raise ApparatusError(f"{p}: [backend.<family>] entries are tables")
    for fam in back:
        if fam not in budget.FAMILIES:
            raise ApparatusError(f"{p}: [backend.{fam}]: a family is one of "
                                 + ", ".join(budget.FAMILIES))
    return Apparatus(p, data)


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_binary(spec) -> Path:
    """A pinned binary's path: written "~/<relative path>", resolved under $HOME."""
    if not isinstance(spec, str) or not spec.startswith("~/"):
        raise ApparatusError(f"a pinned binary is written relative to HOME (\"~/...\"), not "
                             f"{spec!r}")
    rel = PurePosixPath(spec[2:])
    if not rel.parts or ".." in rel.parts or rel.is_absolute():
        raise ApparatusError(f"{spec!r} is not a path under HOME")
    home = os.environ.get("HOME", "")
    if not home or not os.path.isabs(home):
        raise ApparatusError("HOME is unset or not absolute: no pinned binary resolves")
    return Path(home) / rel


def check_binary(table: Mapping) -> Path:
    """The pinned binary of a backend table, present, executable and with its sha256."""
    p = resolve_binary(table.get("binary"))
    want = table.get("sha256")
    if not isinstance(want, str) or len(want) != 64:
        raise ApparatusError(f"{table.get('binary')}: no sha256 pin")
    if not p.is_file() or not os.access(p, os.X_OK):
        raise ApparatusMismatch(f"the pinned binary {table.get('binary')} is missing or not "
                                f"executable: {REPROBE['binary']}")
    got = file_sha256(p)
    if got != want:
        raise ApparatusMismatch(f"{table.get('binary')}: sha256 {got[:16]}…, pinned "
                                f"{want[:16]}…: {REPROBE['binary']}")
    return p


def _git(root, *args):
    try:
        p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                           timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return p.stdout.strip() if p.returncode == 0 else None


def git_facts(root) -> dict:
    """The course commit and dirty flag, and the git tree hash of harness/fvh with
    its own dirty flag (empty strings outside a git checkout)."""
    head = _git(root, "rev-parse", "HEAD") or ""
    dirty = _git(root, "status", "--porcelain", "--untracked-files=no")
    tree = _git(root, "rev-parse", "HEAD:harness/fvh") or ""
    fvh_dirty = _git(root, "status", "--porcelain", "--", "harness/fvh")
    return {"course_commit": head, "course_dirty": bool(dirty),
            "fvh_tree": tree, "fvh_dirty": bool(fvh_dirty)}


def _version_of(binary_spec: str) -> str:
    """The version a pinned version file names (its last path component)."""
    return PurePosixPath(binary_spec).name if isinstance(binary_spec, str) else ""


def collect(app: Apparatus, root=None) -> dict:
    """The apparatus facts every record carries (DV4-PLAN §3.6)."""
    root = Path(root if root is not None else ROOT)
    facts = {"apparatus_file": str(app.path), "apparatus_sha256": app.sha256,
             **git_facts(root), "backend": {}, "model_server": app.model_server(), "pins": {}}
    for fam in app.families():
        t = app.backend(fam)
        entry = {"binary": t.get("binary"), "version": t.get("version"),
                 "pinned_sha256": t.get("sha256")}
        try:
            p = resolve_binary(t.get("binary"))
            entry["found_sha256"] = file_sha256(p) if p.is_file() else None
        except (ApparatusError, OSError):
            entry["found_sha256"] = None
        for k in ("model", "effort", "max_turns"):
            if k in t:
                entry[k] = t[k]
        facts["backend"][fam] = entry
    for key, rel in _PIN_FILES.items():
        f = root / rel
        facts["pins"][key] = file_sha256(f) if f.is_file() else None
    return facts


def check(app: Apparatus, root=None) -> list[Drift]:
    """Every difference between the host and the pins."""
    root = Path(root if root is not None else ROOT)
    out = []
    facts = collect(app, root)
    for fam, e in facts["backend"].items():
        if e["found_sha256"] != e["pinned_sha256"]:
            out.append(Drift(f"backend.{fam}.sha256", str(e["pinned_sha256"]),
                             str(e["found_sha256"] or "missing"), REPROBE["binary"]))
        v = _version_of(e["binary"] or "")
        if fam == budget.CLAUDE and e.get("version") and v != e["version"]:
            out.append(Drift(f"backend.{fam}.version", str(e["version"]), v or "none",
                             REPROBE["version"]))
    pins = app.data.get("pins") or {}
    for key in _PIN_FILES:
        want = pins.get(f"{key}_sha256")
        if want is not None and want != facts["pins"][key]:
            out.append(Drift(f"pins.{key}_sha256", str(want), str(facts["pins"][key] or "missing"),
                             REPROBE[key]))
    return out


def source_sha256(obj) -> str:
    """sha256 of a policy's source: a path, a module, a class or a function."""
    if isinstance(obj, (str, Path)):
        return file_sha256(obj)
    try:
        src = inspect.getsource(obj)
    except (OSError, TypeError):
        mod = inspect.getmodule(obj)
        if mod is None or not getattr(mod, "__file__", None):
            raise ValueError(f"no source for {obj!r}") from None
        return file_sha256(mod.__file__)
    return hashlib.sha256(src.encode("utf-8")).hexdigest()


def prompt_hash(*, system: str, message: str, schema, policy_source: str) -> str:
    """sha256 over the system prompt, the rendered message, the action schema and
    the policy module's own source digest (DV4-PLAN §3.6)."""
    h = hashlib.sha256()
    for part in (system, message, json.dumps(schema, sort_keys=True), policy_source):
        b = part.encode("utf-8")
        h.update(len(b).to_bytes(8, "big"))
        h.update(b)
    return h.hexdigest()
