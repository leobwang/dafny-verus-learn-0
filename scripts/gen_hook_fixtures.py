#!/usr/bin/env python3
"""gen_hook_fixtures.py: expand the guard's fixture templates (spec §7.5).

The templates live in tests/hooks/templates/{must_block,must_allow}.tmpl.jsonl.
Each line is one PreToolUse hook input plus a "why", with %NAME% placeholders
and an optional "axes" list. A template expands over the axes it names:

    "axes": ["track", "lang"]   Q, R  x  dafny, verus, python   (6 lines)
    "axes": ["lang"]            dafny, verus, python  (track Q)  (3 lines)
    "axes": ["track"]           Q, R  (lang dafny)                (2 lines)
    no "axes"                   one line (track Q, lang dafny)

"langs" and "tracks" narrow an axis. An expanded line's why gains a suffix
such as " [R verus]". The outputs are tests/hooks/must_block.jsonl and
tests/hooks/must_allow.jsonl; they are committed and drift-checked (--check).

Placeholders left for scripts/test_hooks.sh to fill at replay time: @ROOT@
(the fake checkout), @HOME@ (a fake home), @SID@ and @SLUG@ (the session the
harness injects as session_id and transcript_path), @UID@ (id -u), @LANE@ (a
throwaway author lane scratch directory the harness creates).

Fixture keys the harness consumes and never feeds to the hook:
    why          "rule <id>: …" on a must-block line: the block must come from
                 that rule (the harness greps stderr for "(rule <id>)")
    raw          a string fed verbatim (malformed-input cases)
    contract     true: the seeded contract allowlist is in place (it also
                 names forbidden paths, to prove they are ignored); otherwise
                 the allowlist is empty
    no_registry  true: MODULES.toml is moved away for this line
    nosession    true: no session_id/transcript_path is injected

The same variable tables build the decoy trees the harness replays against
(--fake-root, --fake-home): every reference file there is a decoy, never real
material.

Usage:
    scripts/gen_hook_fixtures.py            regenerate the two fixture files
    scripts/gen_hook_fixtures.py --check    exit 1 if they differ from the templates
    scripts/gen_hook_fixtures.py --stats    template and line counts
    scripts/gen_hook_fixtures.py --fake-root DIR
    scripts/gen_hook_fixtures.py --fake-home DIR --slug SLUG --sid SID
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "tests" / "hooks" / "templates"
OUTPUTS = {
    "must_block": ROOT / "tests" / "hooks" / "must_block.jsonl",
    "must_allow": ROOT / "tests" / "hooks" / "must_allow.jsonl",
}
RULE_IDS = {"1", "1b", "1c", "1d", "1e", "1f", "2", "2c", "2s", "2f", "2g"}
CONSUMED = ("axes", "langs", "tracks")
TRACKS = ("Q", "R")
LANGS = ("dafny", "verus", "python")
PLACEHOLDER = re.compile(r"%([A-Z][A-Z0-9_]*)%")

GLOBAL = {
    "DAFNY": ".toolchain/dafny-4.11.0/dafny/dafny",
    "VERUS": ".toolchain/verus-0.2026.09.27.3cf1832/verus-x86-linux/verus",
    "Z3PIN": ".toolchain/dafny-4.11.0/dafny/z3/bin/z3-4.14.1",
    "CACHE": "@HOME@/.cache/dafny-verus-learn-0",
    "LEDGER": "instructor/ledger.md",
    "OTHERPROJ": "-home-learner-code-lean-learn-0-authoring",
    "OTHERSID": "0f0e0d0c-0000-4000-8000-00000000beef",
    "OWNTMP": "/tmp/claude-@UID@/@SLUG@/@SID@",
    "OTHERTMP": "/tmp/claude-@UID@/-home-learner-code-lean-learn-0-authoring/0f0e0d0c-0000-4000-8000-00000000beef",
    "CLAUDEHOME": "@HOME@/.claude",
    "PUBANS": "bench/public/dafnybench/answers/task001.dfy",
    "PUBTASK": "bench/public/dafnybench/tasks/task001.dfy",
    "STATEMENT": "Challenges/Q19_Algorithms/Q19_Statements.dfy",
    "CHAL": "Challenges/Q19_Algorithms/Q19_Heap.dfy",
}

TRACK = {
    "Q": {
        "T": "Q", "TL": "q", "ID": "Q04", "IDL": "q04", "NAME": "Q04_Proofs",
        "SLOTS": "slots/Q04.slots", "ANSWERS": "paper/Q04_answers.tex",
        "ANSWERS_OK": "paper/Q02_answers.tex", "PROBLEMS": "paper/Q04_problems.tex",
        "DOC": "docs/Q04_Proofs.md", "PAPERSOL": "paper/solutions/Q04_solutions.tex",
        "LEAKPAT": "tests/instructor/leak_patterns/Q04.txt",
        "FIXGOLD": "tests/instructor/fixtures/Q04_gold_answers.tex",
        "FIXFLAW": "tests/instructor/fixtures/Q04_flawed_answers.tex",
        "HIDDEN": "Hidden/labs/Q15/verdicts.tar.age", "TOOLOK": "tools/Q12/count.py",
        "TOOLNEW": "tools/Q15/trace.py", "BENCHT": "bench/local/q/card01/tasks/task.dfy",
        "BENCHA": "bench/local/q/card01/answers/answer.dfy",
        "SOLO": "harness/q/fvh_q/gate/gate.py", "EXPECTED": "expected/Q04.pins",
        "RUBRIC": "paper/rubrics/Q04_rubric.md", "LAB": "Q12",
        "SPECIMEN": "specimens/Q04/P5.dfy.specimen", "CHECKS": "dafny/checks/Q04_checks.dfy",
    },
    "R": {
        "T": "R", "TL": "r", "ID": "R07", "IDL": "r07", "NAME": "R07_Library",
        "SLOTS": "slots/R07.slots", "ANSWERS": "paper/R07_answers.tex",
        "ANSWERS_OK": "paper/R02_answers.tex", "PROBLEMS": "paper/R07_problems.tex",
        "DOC": "docs/R07_Library.md", "PAPERSOL": "paper/solutions/R07_solutions.tex",
        "LEAKPAT": "tests/instructor/leak_patterns/R07.txt",
        "FIXGOLD": "tests/instructor/fixtures/R07_gold_answers.tex",
        "FIXFLAW": "tests/instructor/fixtures/R07_flawed_answers.tex",
        "HIDDEN": "Hidden/labs/R15/verdicts.tar.age", "TOOLOK": "tools/R12/profile.py",
        "TOOLNEW": "tools/R14/trigscan.py", "BENCHT": "bench/local/r/card01/tasks/task.rs",
        "BENCHA": "bench/local/r/card01/answers/answer.rs",
        "SOLO": "verus/r/r16_capstone/src/trust_report.rs", "EXPECTED": "expected/R07.pins",
        "RUBRIC": "paper/rubrics/R07_rubric.md", "LAB": "R12",
        "SPECIMEN": "specimens/R07/P3.rs.specimen", "CHECKS": "dafny/checks/R07_checks.dfy",
    },
}


def lang_vars(track, lang):
    t = TRACK[track]
    if lang == "dafny":
        exdir = f"dafny/{track}/{t['NAME']}/core"
        given = "dafny/given/Q/QG_L1_BigNat.dfy" if track == "Q" else "dafny/given/R/RG_A1_Regex.dfy"
        v = {
            "EXDIR": exdir, "EX": f"{exdir}/{t['NAME']}.dfy",
            "AGENT": f"{exdir}/{t['ID']}_AgentRepair.dfy", "PROJ": f"{exdir}/dfyconfig.toml",
            "GIVEN": given, "GIVENDIR": given.rsplit("/", 1)[0],
            "REF": f"Solutions/{exdir}/{t['NAME']}.dfy", "REFDIR": "Solutions/dafny",
            "REFPROJ": "Solutions/dafny/dfyconfig.toml", "EXT": "dfy", "PKG": t["NAME"],
            "REFPKG": "Solutions", "BUILD": f"scripts/vcheck {t['ID']} d",
            "DIRECT": f"%DAFNY% verify --cores 2 --resource-limit 5000000 {exdir}/dfyconfig.toml",
            "REFBUILD": "%DAFNY% verify --cores 2 --resource-limit 5000000 Solutions/dafny/dfyconfig.toml",
            "REFBUILD_T": f"%DAFNY% test --target py --cores 2 Solutions/{exdir}/{t['NAME']}.dfy",
            "RUNPROBE": "%DAFNY% verify --cores 2 --resource-limit 5000000",
            "IMPORT_REF": f'include "../../Solutions/{exdir}/{t["NAME"]}.dfy"\n',
            "IMPORT_OK": f'include "../../{given}"\n',
            "HOLE": "assume false;", "FILL": "assert true;",
        }
    elif lang == "verus":
        crate = f"{t['IDL']}_{t['NAME'].split('_', 1)[1].lower()}"
        exdir = f"verus/{t['TL']}/{crate}"
        gcrate = "qg_bignat_l1" if track == "Q" else "rg_re_a1"
        v = {
            "EXDIR": exdir, "EX": f"{exdir}/src/lib.rs", "AGENT": f"{exdir}/src/agent.rs",
            "PROJ": f"{exdir}/Cargo.toml", "GIVEN": f"verus/given/{gcrate}/src/lib.rs",
            "GIVENDIR": f"verus/given/{gcrate}", "REF": f"Solutions/{exdir}/src/lib.rs",
            "REFDIR": "Solutions/verus", "REFPROJ": "Solutions/verus/Cargo.toml", "EXT": "rs",
            "PKG": crate, "REFPKG": f"solutions_{crate}",
            "BUILD": f"scripts/vcheck {t['ID']} v",
            "DIRECT": f"cargo verus verify -p {crate} -- --rlimit 2",
            "REFBUILD": "cargo verus verify --manifest-path Solutions/verus/Cargo.toml -- --rlimit 2",
            "REFBUILD_T": f"cargo verus verify -p solutions_{crate} -- --rlimit 2",
            "RUNPROBE": "%VERUS% --crate-type=lib --rlimit 2",
            "IMPORT_REF": f"use solutions_{crate}::*;\n", "IMPORT_OK": "use vstd::prelude::*;\n",
            "HOLE": "assume(false);", "FILL": "assert(true);",
        }
    else:
        pkg = f"fvh_{t['TL']}"
        exdir = f"harness/{t['TL']}/{pkg}"
        mod = "policies" if track == "Q" else "extract"
        agent = "report" if track == "Q" else "loop"
        v = {
            "EXDIR": exdir, "EX": f"{exdir}/{mod}.py", "AGENT": f"{exdir}/{agent}.py",
            "PROJ": "harness/pyproject.toml", "GIVEN": "harness/fvh/stats.py",
            "GIVENDIR": "harness/fvh", "REF": f"Solutions/{exdir}/{mod}.py",
            "REFDIR": "Solutions/harness", "REFPROJ": "Solutions/harness/pyproject.toml",
            "EXT": "py", "PKG": pkg, "REFPKG": f"solutions_{pkg}",
            "BUILD": f"cd harness && uv run pytest -q tests/{t['TL']}",
            "DIRECT": f"uv run --directory harness pytest -q tests/{t['TL']}",
            "REFBUILD": "uv run --project Solutions/harness pytest -q",
            "REFBUILD_T": f"pytest -q Solutions/harness/tests/{t['TL']}",
            "RUNPROBE": "python3",
            "IMPORT_REF": f"from solutions_{pkg} import {mod}\n",
            "IMPORT_OK": f"from {pkg} import {mod}\n",
            "HOLE": "raise NotImplementedError", "FILL": "return []",
        }
    n = t["IDL"]
    v.update({
        "PROBE": f"instructor/scratch/probe_{n}.{v['EXT']}",
        "LEAKY": f"instructor/scratch/leaky_{n}.{v['EXT']}",
        "PEEK": f"instructor/scratch/peek_{n}.{v['EXT']}",
        "EXLINK": f"instructor/scratch/ex_{n}.{v['EXT']}",
        "GIVENLINK": f"instructor/scratch/given_{n}.{v['EXT']}",
        "LANG": lang,
    })
    return v


def variables(track, lang):
    v = dict(GLOBAL)
    v.update(TRACK[track])
    v.update(lang_vars(track, lang))
    return v


def subst(value, env, where):
    if isinstance(value, str):
        for _ in range(4):
            new = PLACEHOLDER.sub(lambda m: env[m.group(1)] if m.group(1) in env else m.group(0), value)
            if new == value:
                break
            value = new
        left = PLACEHOLDER.findall(value)
        if left:
            raise SystemExit(f"gen_hook_fixtures: unknown placeholder(s) {left} in {where}")
        return value
    if isinstance(value, list):
        return [subst(x, env, where) for x in value]
    if isinstance(value, dict):
        return {k: subst(x, env, where) for k, x in value.items()}
    return value


def expand(kind):
    path = TEMPLATES / f"{kind}.tmpl.jsonl"
    lines, ntmpl = [], 0
    for lineno, text in enumerate(path.read_text().splitlines(), 1):
        if not text.strip() or text.lstrip().startswith("//"):
            continue
        where = f"{path.name}:{lineno}"
        try:
            tmpl = json.loads(text)
        except ValueError as e:
            raise SystemExit(f"gen_hook_fixtures: {where}: {e}")
        ntmpl += 1
        why = tmpl.get("why", "")
        m = re.match(r"rule ([0-9a-z]+):", why)
        if kind == "must_block" and (not m or m.group(1) not in RULE_IDS):
            raise SystemExit(f"gen_hook_fixtures: {where}: a must-block why starts 'rule <id>:' with id in {sorted(RULE_IDS)}")
        if kind == "must_allow" and why.startswith("rule "):
            raise SystemExit(f"gen_hook_fixtures: {where}: a must-allow why never starts with 'rule '")
        axes = tmpl.get("axes", [])
        tracks = tmpl.get("tracks", list(TRACKS)) if "track" in axes else ["Q"]
        langs = tmpl.get("langs", list(LANGS)) if "lang" in axes else ["dafny"]
        body = {k: x for k, x in tmpl.items() if k not in CONSUMED}
        for tr in tracks:
            for lg in langs:
                env = variables(tr, lg)
                out = subst(body, env, where)
                tags = ([tr] if "track" in axes else []) + ([lg] if "lang" in axes else [])
                if tags:
                    out["why"] = f"{out['why']} [{' '.join(tags)}]"
                lines.append(json.dumps(out, ensure_ascii=False))
    whys = [json.loads(x)["why"] for x in lines]
    dup = {w for w in whys if whys.count(w) > 1}
    if dup:
        raise SystemExit(f"gen_hook_fixtures: duplicate why in {kind}: {sorted(dup)[:5]}")
    return ntmpl, lines


# --- Decoy trees ---------------------------------------------------------------
DECOY = "decoy: hook tests never ship reference material\n"


def write(base, rel, text=DECOY):
    p = Path(base) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def link(base, rel, target_rel):
    p = Path(base) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.is_symlink() or p.exists():
        p.unlink()
    os.symlink(os.path.relpath(Path(base) / target_rel, p.parent), p)


def seeded_allowlist():
    """The contract allowlist for "contract": true lines. Forbidden lines
    (given, frozen, solo) are seeded on purpose: rules 2f and 2s ignore them."""
    lines = []
    for tr in TRACKS:
        for lg in LANGS:
            lines.append(variables(tr, lg)["AGENT"])
        t = TRACK[tr]
        lines += [t["ANSWERS_OK"], t["TOOLOK"]]
    for tr in TRACKS:
        for lg in LANGS:
            lines.append(variables(tr, lg)["GIVEN"])
        lines.append(TRACK[tr]["SOLO"])
        lines.append(TRACK[tr]["EXPECTED"])
    lines += [GLOBAL["CHAL"], GLOBAL["STATEMENT"], "agents/prover.py"]
    out, seen = [], set()
    for x in lines:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return "\n".join(out) + "\n"


def fake_root(base):
    base = Path(base)
    for tr in TRACKS:
        t = TRACK[tr]
        for lg in LANGS:
            v = variables(tr, lg)
            write(base, v["EX"], f"// decoy exercise for hook tests\n{v['HOLE']}\n")
            write(base, v["AGENT"], f"// decoy agentic file\n{v['HOLE']}\n")
            write(base, v["GIVEN"], "// decoy given layer\n")
            write(base, v["REF"])
            write(base, v["REFPROJ"])
            if lg == "dafny":
                write(base, v["PROJ"], f'includes = ["*.dfy", "../../../given/{tr}/*.dfy"]\n')
            elif lg == "verus":
                write(base, v["PROJ"], f'[package]\nname = "{v["PKG"]}"\n\n[dependencies]\n'
                                       f'{v["GIVENDIR"].rsplit("/", 1)[1]} = {{ path = "../../given/{v["GIVENDIR"].rsplit("/", 1)[1]}" }}\n')
            else:
                write(base, v["PROJ"], '[project]\nname = "harness"\n')
            write(base, v["PROBE"], v["IMPORT_OK"])
            write(base, v["LEAKY"], v["IMPORT_REF"])
            link(base, v["PEEK"], v["REF"])
            link(base, v["EXLINK"], v["EX"])
            link(base, v["GIVENLINK"], v["GIVEN"])
        for k in ("ANSWERS", "ANSWERS_OK", "PROBLEMS", "DOC", "TOOLOK", "SLOTS", "BENCHT", "BENCHA", "SOLO", "EXPECTED", "RUBRIC"):
            write(base, t[k], "decoy course file\n")
        write(base, t["SPECIMEN"], "// SLOT: FAILS ???\n// decoy obligation specimen\n")
        write(base, t["CHECKS"], "// decoy given-only check unit\n// SLOT: expect Turn(Turn(North)) == ???;\n")
        write(base, t["PAPERSOL"])
        write(base, t["LEAKPAT"], "# decoy: hook tests never ship leak patterns\n")
        # The grader calibration fixtures (spec §4.7) are reference-class too
        # (rule 1): a gold fixture is a correct answer set by design.
        for k in ("FIXGOLD", "FIXFLAW"):
            write(base, t[k], "% decoy: hook tests never ship calibration fixtures\n")
        write(base, t["HIDDEN"], "decoy\n")
        write(base, f"docs/{t['ID']}_Intro.md", "decoy chapter\n")
    for rel in ("Solutions/dafny/Q/Q04_Proofs/core/Q04_Proofs-py/Q04_Proofs.py",
                "Solutions/verus/target/debug/deps/solutions_q04_proofs.vir",
                "Solutions/bench/local/r/card01/answers/answer.rs", "Solutions/labs/Q15/specs.dfy",
                "Solutions/runs/q12/arm1.jsonl", "Solutions/Challenges/Ref/Q19_Heap.dfy",
                "Solutions/pins/Q04.pins"):
        write(base, rel)
    write(base, "verus/Cargo.toml", '[workspace]\nmembers = ["given/*", "q/*"]\nexclude = ["../Solutions"]\n')
    write(base, "verus/Cargo.lock", "# decoy lock\n")
    write(base, "verus/rust-toolchain.toml", '[toolchain]\nchannel = "1.98.1"\n')
    write(base, "verus/.cargo/config.toml", "# decoy cargo config\n")
    write(base, "verus/target/debug/deps/q04_proofs.vir", "decoy vir\n")
    write(base, "verus/target/debug/deps/libq04_proofs.rmeta", "decoy rmeta\n")
    write(base, "verus/target/debug/deps/libsolutions_q04_proofs.rlib", "decoy rlib\n")
    write(base, ".verus-log/root.smt2", "decoy smt\n")
    write(base, ".verus-solver-log/root.smt2", "decoy smt\n")
    write(base, "build/dafny/Q04_Proofs.doo", "decoy doo\n")
    write(base, "dafny/Q/Q04_Proofs/core/Q04_Proofs-py/Q04_Proofs.py", "decoy generated python\n")
    write(base, "harness/q/fvh_q/__pycache__/policies.cpython-312.pyc", "decoy\n")
    write(base, "dafny/options/core.toml", "# decoy options\n")
    write(base, "dafny/checks/Q04_checks.dfy", "// decoy check unit\n")
    write(base, "harness/uv.lock", "# decoy\n")
    write(base, "harness/tests/q/test_policies.py", "def test_x():\n    pass\n")
    write(base, "harness/tests/r/test_extract.py", "def test_x():\n    pass\n")
    write(base, "harness/tests/core/test_stats.py", "def test_x():\n    pass\n")
    write(base, "harness/fvh/core.py", "# decoy frozen harness core\n")
    # Neighbours of the calibration fixtures that stay open: a README beside
    # them, a pytest fixtures/ directory and the wrapper tests' fixtures/
    # (the name alone is no reference).
    write(base, "tests/instructor/README.md", "decoy: what tests/instructor holds\n")
    write(base, "harness/tests/q/fixtures/case1.json", "{}\n")
    write(base, "tests/wrappers/fixtures/dafny/README.md", "decoy: the wrapper tests' captured outputs\n")
    # A partial copy of the checkout in scratch that holds only the calibration
    # fixtures, so the reach of a recursive reader is tested on them alone
    # (the real tests/instructor/ holds the leak patterns as well).
    write(base, "instructor/scratch/kit/tests/instructor/fixtures/Q04_gold_answers.tex",
          "% decoy: hook tests never ship calibration fixtures\n")
    link(base, "instructor/scratch/ti", "instructor/scratch/kit/tests/instructor")
    write(base, "research/EVAL.md", "# EVAL\n")
    write(base, "research/TRUST.md", "# TRUST\n")
    write(base, "research/runs/q12/run1.jsonl", "{}\n")
    write(base, GLOBAL["PUBANS"], "decoy public answer\n")
    write(base, GLOBAL["PUBTASK"], "decoy public task\n")
    write(base, GLOBAL["STATEMENT"], "// decoy challenge statements\n")
    write(base, GLOBAL["CHAL"], "// decoy challenge file\n")
    write(base, "agents/prover.py", "def act(state):\n    pass\n")
    write(base, "instructor/ledger.md", "- Q04 decoy item due: 2000-01-01\n")
    write(base, "instructor/feedback/Q04.md", "decoy feedback\n")
    write(base, "instructor/records/.keep", "")
    write(base, "instructor/scratch/notes.md", "decoy notes\n")
    write(base, "instructor/scratch/dock.py", "import docker\nprint(docker.from_env())\n")
    write(base, "instructor/scratch/peek.sh", "#!/bin/sh\ncat Solutions/dafny/dfyconfig.toml\n")
    write(base, "instructor/scratch/probe.sh", "#!/bin/sh\nls dafny/Q\n")
    write(base, "instructor/scratch/setci.sh", "#!/bin/sh\nexport CI=true\nexec scripts/ci.sh\n")
    write(base, "instructor/scratch/setci.py",
          "import os, subprocess\nos.environ['CI'] = 'true'\nsubprocess.run(['scripts/pins.py', '--ci'])\n")
    write(base, "instructor/scratch/readci.py", "import os\nprint(os.environ.get('CI', 'unset'))\n")
    write(base, "instructor/scratch/crate/lib.rs", "mod twin;\n")
    link(base, "instructor/scratch/crate/twin.rs", variables("Q", "verus")["REF"])
    write(base, "instructor/scratch/pyprobe/main.py", "import twin\n")
    link(base, "instructor/scratch/pyprobe/twin.py", variables("Q", "python")["REF"])
    write(base, "instructor/scratch/inc_peek.dfy", 'include "peek_q04.dfy"\n')
    write(base, "instructor/scratch/leaky_spec.dfy.specimen",
          '// SLOT: FAILS ???\ninclude "../../Solutions/dafny/Q/Q04_Proofs/core/Q04_Proofs.dfy"\n')
    link(base, "instructor/scratch/spec_q04.dfy.specimen", TRACK["Q"]["SPECIMEN"])
    # Patch files for the patch / git apply / git am write targets: one that
    # fills a specimen slot, one that only touches scratch, and one that only
    # touches an allowlisted agentic file (decoy hunks; nothing applies them).
    write(base, "instructor/scratch/fix_specimen.diff",
          "--- a/specimens/Q04/P5.dfy.specimen\n+++ b/specimens/Q04/P5.dfy.specimen\n"
          "@@ -1 +1 @@\n-// SLOT: FAILS ???\n+// SLOT: FAILS 3\n")
    write(base, "instructor/scratch/fix_scratch.diff",
          "--- a/instructor/scratch/notes.md\n+++ b/instructor/scratch/notes.md\n"
          "@@ -1 +1 @@\n-decoy notes\n+decoy notes, patched\n")
    agent = variables("Q", "dafny")["AGENT"]
    write(base, "instructor/scratch/fix_agent.diff",
          f"diff --git a/{agent} b/{agent}\n--- a/{agent}\n+++ b/{agent}\n"
          "@@ -2 +2 @@\n-assume false;\n+assert true;\n")
    write(base, "instructor/scratch/crate_ok/lib.rs", "mod helper;\n")
    write(base, "instructor/scratch/crate_ok/helper.rs", "// decoy helper\n")
    write(base, "docs/README.md", "decoy docs\n")
    write(base, "paper/Makefile", "paper:\n\ttrue\n")
    write(base, "specimens/Q04/K1.dfy.specimen", "// decoy specimen\n")
    write(base, "scripts/vcheck", "#!/bin/sh\n# decoy wrapper\n")
    write(base, "scripts/ci.sh", "#!/bin/sh\n# decoy CI script; the real one builds Solutions/\n")
    write(base, "scripts/reference_lint.py", "# decoy: the real script reads the reference\n")
    write(base, "scripts/pins.py", "# decoy golden harness\n")
    write(base, "scripts/update_rubric_pins.sh", "#!/bin/sh\n# decoy: the real one hashes reference files\n")
    write(base, "scripts/firsttry.sh", "#!/bin/sh\n")
    write(base, "scripts/firsttry.py", "# decoy: the real one holds firsttry's implementation\n")
    write(base, "scripts/vaudit", "#!/bin/sh\n# decoy assumption audit\n")
    write(base, "scripts/specfreeze", "#!/bin/sh\n# decoy statement freeze\n")
    write(base, "scripts/test_corpus.py", "# decoy cheat-corpus runner\n")
    write(base, "expected/Q04.freeze", "decoy freeze pin\n")
    write(base, "expected/Q04.audit", "# decoy pinned audit report\n")
    # The cheat corpus (tests/corpus/, rule 2g; content-scanned like learner
    # files): two clean decoy fixtures and one that includes the reference.
    # Fixture directories use the corpus's canonical <lang>/<ID>/ layout
    # (tests/corpus/README.md); the decoys reuse real fixture paths.
    write(base, "tests/corpus/dafny/G01/main.dfy",
          "// decoy cheat-corpus fixture: G1\nlemma {:axiom} Decoy() ensures false\n")
    write(base, "tests/corpus/verus/V03/src/lib.rs",
          "// decoy cheat-corpus fixture: V3\nuse vstd::prelude::*;\n")
    write(base, "tests/corpus/dafny/G09/main.dfy",
          '// decoy cheat-corpus fixture that reaches the reference\n'
          'include "../../../../Solutions/dafny/Q/Q04_Proofs/core/Q04_Proofs.dfy"\n')
    write(base, "scripts/mksandbox-run", "#!/bin/sh\n# decoy: the real one runs docker\n")
    write(base, "scripts/contract_local.sh", "#!/bin/sh\n# decoy: the real one runs docker run ... opencode\n")
    write(base, "scripts/check_course_map.py", "# decoy\n")
    write(base, "scripts/course_mode.sh", "#!/bin/sh\n")
    write(base, "sandbox/manifests/q12-lab1.toml", "# decoy manifest\n")
    write(base, ".claude/hooks/spoiler-guard.sh", "#!/bin/sh\n# decoy hook copy\n")
    write(base, ".claude/settings.json", "{}\n")
    write(base, ".claude/skills/instructor/CORE.md", "# decoy instructor contract\n")
    write(base, ".claude/skills/tutor/SKILL.md", "---\nname: tutor\n---\ndecoy skill\n")
    write(base, "CLAUDE.md", "# decoy CLAUDE.md\n\n<!-- learner-owned below: contract v0/v1/v2 -->\n\n"
                             "### Q-v0 — Q03 (not written yet)\n")
    write(base, ".claude/state/contract-allowlist", "")
    write(base, ".vscode/settings.json", "{}\n")
    write(base, ".mcp.json", "{}\n")
    write(base, ".toolchain/dafny-4.11.0/dafny/z3/bin/z3-4.14.1", "")
    write(base, ".toolchain/dafny-4.11.0/dafny/z3/bin/z3-4.12.1", "")
    write(base, "MODULES.toml", "schema = 1\n\n" + "".join(
        f'[[module]]\nid = "{i}"\n\n' for i in ("Q01", "Q04", "Q07", "Q12", "Q19", "R01", "R07", "R12")))
    write(base, "tests/hooks/seeded-allowlist", seeded_allowlist())


def fake_home(base, slug, sid):
    base = Path(base)
    ch = ".claude"
    other = GLOBAL["OTHERSID"]
    oproj = GLOBAL["OTHERPROJ"]
    for rel in (f"{ch}/projects/{slug}/memory/MEMORY.md", f"{ch}/projects/{slug}/{sid}.jsonl",
                f"{ch}/projects/{slug}/{sid}/tool-results/r1.txt",
                f"{ch}/projects/{slug}/{other}.jsonl",
                f"{ch}/projects/{slug}/{other}/subagents/agent-a1.jsonl",
                f"{ch}/projects/{slug}/{other}/tool-results/r1.txt",
                f"{ch}/projects/{oproj}/memory/notes.md", f"{ch}/projects/{oproj}/{other}.jsonl",
                f"{ch}/file-history/{other}/f1@v1", f"{ch}/file-history/{sid}/f1@v1",
                f"{ch}/history.jsonl", f"{ch}/paste-cache/p1.txt", f"{ch}/debug/{other}.txt",
                f"{ch}/settings.json", ".cache/dafny-verus-learn-0/grader/out.json",
                ".cache/dafny-verus-learn-0/author-probes/dafny/D1/stdout.txt"):
        write(base, rel, "decoy session state\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--fake-root")
    ap.add_argument("--fake-home")
    ap.add_argument("--slug")
    ap.add_argument("--sid")
    a = ap.parse_args()
    if a.fake_root:
        fake_root(a.fake_root)
        return 0
    if a.fake_home:
        if not (a.slug and a.sid):
            ap.error("--fake-home needs --slug and --sid")
        fake_home(a.fake_home, a.slug, a.sid)
        return 0
    rc = 0
    for kind, out in OUTPUTS.items():
        ntmpl, lines = expand(kind)
        text = "\n".join(lines) + "\n"
        if a.stats:
            print(f"{kind}: {ntmpl} templates, {len(lines)} lines")
        if a.check:
            if not out.exists() or out.read_text() != text:
                print(f"gen_hook_fixtures: {out.relative_to(ROOT)} is stale; run scripts/gen_hook_fixtures.py", file=sys.stderr)
                rc = 1
        elif not a.stats:
            out.write_text(text)
    return rc


if __name__ == "__main__":
    sys.exit(main())
