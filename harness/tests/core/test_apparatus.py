"""The frozen core's own tests: fvh.apparatus (DV4-PLAN §3.6, §9): the apparatus
file's schema, binaries pinned relative to HOME, the sha256 check before an exec,
the facts every record carries, drift, and the prompt hash. Throwaway files
and roots only; no binary is executed."""

import hashlib
import os
import subprocess
from pathlib import Path

import pytest

from fvh import apparatus as A
from fvh import budget

FAKE = Path(__file__).resolve().parent / "fakes" / "apparatus.toml"


def write(tmp_path, text):
    p = tmp_path / "apparatus.toml"
    p.write_text(text)
    return p


def binary(home, rel="bin/tool", data=b"#!/bin/sh\nexit 0\n"):
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    p.chmod(0o755)
    return hashlib.sha256(data).hexdigest()


def test_the_fake_apparatus_file_loads():
    app = A.load(FAKE)
    assert app.families() == tuple(sorted(budget.FAMILIES))
    assert app.defaults().calls == 40 and app.window().allowed_overage == ("rejected",)
    assert app.model_server()["version"] == "0.0.0-fake"


def test_the_default_location_and_the_environment(tmp_path, monkeypatch):
    monkeypatch.delenv(A.ENV, raising=False)
    assert A.location(tmp_path) == tmp_path / "sandbox" / "apparatus.toml"
    monkeypatch.setenv(A.ENV, str(tmp_path / "x.toml"))
    assert A.location(tmp_path) == tmp_path / "x.toml"
    with pytest.raises(A.ApparatusError, match="no apparatus file"):
        A.load()


@pytest.mark.parametrize("text, match", [
    ("schema = 2\n", "schema"),
    ("schema = 1\n[extra]\n", "unknown table"),
    ("schema = 1\n[backend.gpt]\nbinary = '~/x'\n", "family"),
    ("schema = = 1\n", "unreadable"),
    ("schema = 1\n[defaults]\ndollars = 3\n", "dollars"),
])
def test_bad_files_refuse(tmp_path, text, match):
    with pytest.raises(A.ApparatusError, match=match):
        app = A.load(write(tmp_path, text))
        app.defaults()


def test_binaries_resolve_under_home_only(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert A.resolve_binary("~/a/b") == tmp_path / "a" / "b"
    for bad in ("/usr/bin/tool", "a/b", "~/../x", "~/", None):
        with pytest.raises(A.ApparatusError):
            A.resolve_binary(bad)
    monkeypatch.setenv("HOME", "")
    with pytest.raises(A.ApparatusError, match="HOME"):
        A.resolve_binary("~/a")


def test_check_binary(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    sha = binary(tmp_path)
    assert A.check_binary({"binary": "~/bin/tool", "sha256": sha}) == tmp_path / "bin" / "tool"
    with pytest.raises(A.ApparatusMismatch, match="sha256"):
        A.check_binary({"binary": "~/bin/tool", "sha256": "f" * 64})
    with pytest.raises(A.ApparatusMismatch, match="missing"):
        A.check_binary({"binary": "~/bin/other", "sha256": sha})
    with pytest.raises(A.ApparatusError, match="no sha256"):
        A.check_binary({"binary": "~/bin/tool"})


def test_under_an_empty_home_every_pinned_binary_drifts(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    drift = A.check(A.load(FAKE), tmp_path)
    assert {d.field for d in drift} >= {f"backend.{f}.sha256" for f in budget.FAMILIES}
    assert all("missing" in d.found for d in drift if d.field.endswith(".sha256"))


def test_check_names_the_field_both_values_and_the_reprobe(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    sha = binary(tmp_path, ".local/share/c/versions/1.2.3")
    (tmp_path / "scripts" / "dvl").mkdir(parents=True)
    (tmp_path / "scripts" / "dvl" / "pins.toml").write_text("x = 1\n")
    pins = hashlib.sha256(b"x = 1\n").hexdigest()
    p = write(tmp_path, f"""schema = 1
[backend.{budget.CLAUDE}]
binary = "~/.local/share/c/versions/1.2.3"
version = "1.2.3"
sha256 = "{sha}"
[pins]
toolchain_sha256 = "{pins}"
""")
    assert A.check(A.load(p), tmp_path) == []
    p.write_text(p.read_text().replace('version = "1.2.3"', 'version = "1.2.4"'))
    (tmp_path / "scripts" / "dvl" / "pins.toml").write_text("x = 2\n")
    drift = {d.field: d for d in A.check(A.load(p), tmp_path)}
    assert set(drift) == {f"backend.{budget.CLAUDE}.version", "pins.toolchain_sha256"}
    d = drift[f"backend.{budget.CLAUDE}.version"]
    assert (d.pinned, d.found) == ("1.2.4", "1.2.3") and "re-p" in d.reprobe
    assert "pinned 1.2.4, found 1.2.3" in d.line()


def test_collect_carries_the_git_facts(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@example.invalid", GIT_CONFIG_GLOBAL=os.devnull)
    root = tmp_path / "r"
    (root / "harness" / "fvh").mkdir(parents=True)
    (root / "harness" / "fvh" / "m.py").write_text("x = 1\n")
    for cmd in (["init", "-q"], ["add", "."], ["commit", "-qm", "c"]):
        subprocess.run(["git", "-C", str(root), *cmd], check=True, env=env)
    facts = A.collect(A.load(FAKE), root)
    assert len(facts["course_commit"]) == 40 and not facts["course_dirty"]
    assert len(facts["fvh_tree"]) == 40 and not facts["fvh_dirty"]
    (root / "harness" / "fvh" / "m.py").write_text("x = 2\n")
    facts = A.collect(A.load(FAKE), root)
    assert facts["course_dirty"] and facts["fvh_dirty"]
    assert facts["apparatus_sha256"] == hashlib.sha256(FAKE.read_bytes()).hexdigest()
    assert facts["backend"][budget.CLAUDE]["found_sha256"] is None


def test_the_prompt_hash_covers_every_part():
    base = dict(system="s", message="m", schema={"a": 1}, policy_source="p")
    h = A.prompt_hash(**base)
    assert h == A.prompt_hash(**base)
    for k, v in (("system", "s2"), ("message", "m2"), ("schema", {"a": 2}),
                 ("policy_source", "p2")):
        assert A.prompt_hash(**{**base, k: v}) != h
    assert A.prompt_hash(system="ab", message="c", schema={}, policy_source="") != \
        A.prompt_hash(system="a", message="bc", schema={}, policy_source="")


def test_source_sha256():
    def f():
        return 1
    assert len(A.source_sha256(f)) == 64
    assert A.source_sha256(FAKE) == hashlib.sha256(FAKE.read_bytes()).hexdigest()
