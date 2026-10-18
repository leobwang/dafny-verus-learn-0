#!/usr/bin/env python3
"""Finite compiled observations of R13's two executable items, after their full gates.

R13.T1 (`AcceptsR13` / `accepts_r13`) and R13.H2 (`ClassCoversR13` /
`class_covers_r13`) are executable. This tool gates the learner files you name
(by default your own), then compiles a client that calls those two functions on
fixed inputs and compares each result with an expected value computed here, by
Python's `re` module for the patterns and by plain set membership for the
classes. The defaults are learner files; no reference is read.

A passed observation is finite evidence about the compiled code on these inputs.
It does not prove the compiler correct and does not replace the proof.

Usage: python3 tools/R13/check_repairs.py --output DIR [--d FILE] [--v FILE]
"""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# (Dafny regex, Verus regex, Python regex) for each pattern.
PATTERNS = [
    ("Cat(Chr('a'), Star(Chr('b')))",
     "Re::Cat(Box::new(Re::Chr('a')), Box::new(Re::Star(Box::new(Re::Chr('b')))))", "ab*"),
    ("Alt(Chr('x'), Eps)", "Re::Alt(Box::new(Re::Chr('x')), Box::new(Re::Eps))", "x?"),
    ("Star(Alt(Chr('a'), Chr('b')))",
     "Re::Star(Box::new(Re::Alt(Box::new(Re::Chr('a')), Box::new(Re::Chr('b')))))", "[ab]*"),
    ("Cat(Chr('\\U{03bb}'), Chr('b'))", "Re::Cat(Box::new(Re::Chr('\\u{3bb}')), Box::new(Re::Chr('b')))",
     "λb"),
    ("Empty", "Re::Empty", None),
]
WORDS = ["", "a", "abb", "x", "ba", "λb", "abab"]

# (Dafny class, Verus class, Python set) for each class.
CLASSES = [
    ("A2.ClassRange('a', 'f')", "CharClass::class_range('a', 'f')", set("abcdef")),
    ("A2.ClassOfString(['x', 'y'])", "rg_re_a2::char_class::class_of_string(&vec!['x', 'y'])", set("xy")),
    ("A2.ClassRange('z', 'a')", "CharClass::class_range('z', 'a')", set()),
]
STRINGS = ["", "abc", "abz", "xyx", "λ"]


def dafny_chars(s):
    return "[" + ", ".join("'" + (f"\\U{{{ord(c):04x}}}" if ord(c) > 127 else c) + "'" for c in s) + "]"


def rust_chars(s):
    return "vec![" + ", ".join("'" + (f"\\u{{{ord(c):x}}}" if ord(c) > 127 else c) + "'" for c in s) + "]"


def invoke(args):
    p = subprocess.run([str(ROOT / "scripts/vcheck"), *args], cwd=ROOT, capture_output=True, text=True)
    try:
        doc = json.loads(p.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(p.stdout + p.stderr)
    return p.returncode, doc


def cases():
    """[(kind, dafny call, verus call, expected bool)]."""
    out = []
    for d, v, py in PATTERNS:
        for w in WORDS:
            want = py is not None and re.fullmatch(py, w) is not None
            out.append(("accepts", f"AcceptsR13({d}, {dafny_chars(w)})",
                        f"accepts_r13(&{v}, &{rust_chars(w)})", want))
    for d, v, chars in CLASSES:
        for s in STRINGS:
            want = all(c in chars for c in s)
            out.append(("covers", f"ClassCoversR13({d}, {dafny_chars(s)})",
                        f"class_covers_r13(&{v}, &{rust_chars(s)})", want))
    return out


def client(lang, text, rows):
    if lang == "d":
        lines = [f"    var o{n} := {d};\n    expect o{n} == {str(w).lower()};" for n, (_, d, _, w) in enumerate(rows)]
        return (text + "\nmodule R13_CompiledClient {\n  import opened RG_A1_Re\n  import A2 = RG_A2_Deriv\n"
                "  import opened R13_Repairs\n\n  method {:test} ObserveR13()\n  {\n" + "\n".join(lines) + "\n  }\n}\n")
    calls = "\n".join(f"    let o{n} = {v};" for n, (_, _, v, _) in enumerate(rows))
    checks = "\n".join(f"    let o{n} = {v};\n    assert!(o{n} == {str(w).lower()});" for n, (_, _, v, w) in enumerate(rows))
    return (text + "\nverus! {\n\npub fn observe_compiled_r13() {\n" + calls + "\n}\n\n} // verus!\n\n"
            "#[test]\nfn observed_r13() {\n    observe_compiled_r13();\n" + checks + "\n}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--d", type=Path, default=ROOT / "dafny/R/R13_Pipelines/std/R13_Pipelines.dfy")
    ap.add_argument("--v", type=Path, default=ROOT / "verus/r/r13_pipelines/src/lib.rs")
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    rows_all = cases()
    report = []
    with tempfile.TemporaryDirectory(prefix="r13-compiled-") as tmp:
        for lang, path in [("d", a.d.resolve()), ("v", a.v.resolve())]:
            original = path.read_bytes()
            row = {"lang": lang, "source": str(path), "sha256": hashlib.sha256(original).hexdigest(),
                   "compiled_cases": 0}
            code, gate = invoke(["--json", "--module", "R13", "--gate", str(path)])
            row["gate"] = gate
            if code or gate.get("verdict") != "verified" or gate.get("holes"):
                row["status"] = "gate-failed"
                report.append(row)
                continue
            text = client(lang, original.decode(), rows_all)
            unit = Path(tmp) / lang
            unit.mkdir(exist_ok=True)
            if lang == "d":
                p = unit / "client.dfy"
                config = (ROOT / "dafny/R/R13_Pipelines/std/dfyconfig.toml").read_text()
                (unit / "dfyconfig.toml").write_text(config.replace("../../../given/", str(ROOT / "dafny/given") + "/"))
            else:
                p = unit / "src/lib.rs"
                p.parent.mkdir(exist_ok=True)
                config = (ROOT / "verus/r/r13_pipelines/Cargo.toml").read_text()
                config = config.replace("r13_pipelines", "r13_runtime_observations")
                config = config.replace("../../given/", str(ROOT / "verus/given") + "/") + "\n[workspace]\n"
                (unit / "Cargo.toml").write_text(config)
            p.write_text(text)
            (a.output / ("client.dfy" if lang == "d" else "client.rs")).write_text(text)
            code, test = invoke(["--json", "--test", str(unit)])
            row["compiled"] = test
            ok = code == 0 and test.get("verdict") == "verified" and test.get("stage") == "test"
            row["status"] = "passed" if ok else "failed"
            row["compiled_cases"] = len(rows_all) if ok else 0
            if path.read_bytes() != original:
                raise RuntimeError("the source changed during the observations")
            report.append(row)
    (a.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    for row in report:
        print(row["lang"], row["status"], row["compiled_cases"])
    return 0 if all(row["status"] == "passed" for row in report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
