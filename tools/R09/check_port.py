#!/usr/bin/env python3
"""Compile the specified escaped-atom implementations and check fixed observations.

Default sources are the learner's R09 agent files. No reference is read.
Run under the course's capped native lane; this utility does not alter pins.
Runtime drivers are generated in private scratch and retained for inspection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import tomllib


def run(root: Path, dafny_file: Path, verus_file: Path, out: Path) -> int:
    sys.path.insert(0, str(root / "tests/wrappers"))
    import test_tools_common as common

    core = common.load_script("vcheck")
    cases_file = root / "tools/R09/port_cases.json"
    cases = json.loads(cases_file.read_text())
    assert cases and all(0 <= c["at"] < len(c["input"]) and
                         c["input"][c["at"]] == "\\" for c in cases)
    out.mkdir(parents=True, exist_ok=True)
    report = {"schema": 1, "claim": "finite compiled escaped-atom observations",
              "cases": len(cases), "inputs": {}, "results": {}}
    for path in [dafny_file, verus_file, cases_file, Path(__file__).resolve()]:
        report["inputs"][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()

    given = root / "dafny/given/R"
    names = ["RG_A1_Re.dfy", "RG_A1b_Facts.dfy", "RG_A2_Deriv.dfy",
             "RG_A2_MatcherStatement.dfy", "RG_A3_Syntax.dfy"]
    includes = "".join("include " + json.dumps(str(given / n)) + "\n" for n in names)
    driver = includes + "include " + json.dumps(str(dafny_file)) + "\n" + r'''
module R09_PortObservation {
 import opened R09_AgentRefactor
 method ObserveR09(id:nat,s:seq<char>,at:nat)
  requires at<|s| && s[at]=='\\'
 {
  var cur:=new EscapedCursorR09(s,at);
  var result:=EscapedAtomR09(cur);
  expect cur.input==s;
  print "CASE ",id," ";
  if result.Err? {print "ERR",result.pos,":",cur.position;}
  else {print "OK",result.value as int,":",cur.position;}
  print " END\n";
 }
'''
    for i, row in enumerate(cases):
        driver += (f' @Test method PortCase{i:03}() {{ObserveR09({i},'
                   f'{json.dumps(row["input"], ensure_ascii=False)},{row["at"]});}}\n')
    driver += "}\n"
    dpath = out / "port.dfy"
    dpath.write_text(driver)
    vtests = r'''
#[cfg(test)] mod port_observations {
 use super::*;
 fn observe(s:&str,at:usize,expected:&str) {
  let input:Vec<char>=s.chars().collect();let original=input.clone();
  let mut cur=EscapedCursorR09 {input,position:at};
  let actual=match escaped_atom_r09(&mut cur) {
   Ok(c)=>format!("OK{}:{}",c as u32,cur.position),
   Err(e)=>format!("ERR{}:{}",e.pos,cur.position),
  };
  assert_eq!(cur.input,original);assert_eq!(actual,expected);
 }
'''
    for i, row in enumerate(cases):
        vtests += (f' #[test] fn port_case_{i:03}() {{observe('
                   f'{json.dumps(row["input"], ensure_ascii=False)},{row["at"]},'
                   f'{json.dumps(row["expected"])});}}\n')
    vtests += "}\n"
    vpath = out / "verus"
    (vpath / "src").mkdir(parents=True, exist_ok=True)
    (vpath / "src/lib.rs").write_text(verus_file.read_text() + vtests)
    original = root / "verus/r/r09_effects/Cargo.toml"
    deps = tomllib.loads(original.read_text())["dependencies"]
    cargo = ('[package]\nname = "r09_port_observation"\nversion = "0.1.0"\n'
             'edition = "2021"\nbuild = false\n[lib]\npath = "src/lib.rs"\n'
             '[dependencies]\n')
    for name, dep in deps.items():
        if isinstance(dep, str):
            cargo += name + " = " + json.dumps(dep) + "\n"
        else:
            path = (original.parent / dep["path"]).resolve()
            cargo += name + " = { path = " + json.dumps(str(path)) + " }\n"
    cargo += "[package.metadata.verus]\nverify = true\n[workspace]\n"
    (vpath / "Cargo.toml").write_text(cargo)

    ok = True
    for language, target, backend in [("dafny", dpath, core.D), ("verus", vpath, core.V)]:
        result = backend.test(str(target))
        doc = result.to_dict()
        accepted = result.verdict == "verified" and result.stage == "test" and not result.holes
        if accepted and language == "dafny":
            logs = [p.read_text(errors="replace") for p in Path(result.raw_dir).rglob("*")
                    if p.is_file() and "stdout" in p.name]
            actual = {int(m[1]): m[2] for log in logs
                      for m in re.finditer(r"CASE (\d+) (.*?) END", log)}
            bad = [i for i, row in enumerate(cases) if actual.get(i) != row["expected"]]
            accepted = not bad and len(actual) == len(cases)
            doc["mismatched_case_ids"] = bad
        elif accepted:
            accepted = len(result.per_symbol) == len(cases) and all(
                value == "passed" for value in result.per_symbol.values())
        report["results"][language] = {"accepted": accepted, "native": doc}
        ok = ok and accepted
        (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"{language}: {result.verdict}/{result.stage}; "
              f"holes={len(result.holes)}; fixed observations {'pass' if accepted else 'fail'}",
              flush=True)
    print(f"Retained artifacts: {out}")
    print("Finite compiled observations; mirror implications and a full grammar theorem are separate.")
    return 0 if ok else 1


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dafny-file", type=Path,
                        default=root / "dafny/R/R09_Effects/agent/R09_AgentRefactor.dfy")
    parser.add_argument("--verus-file", type=Path,
                        default=root / "verus/r/r09_effects/src/agent.rs")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    out = args.out or Path(tempfile.mkdtemp(prefix="dvl0-r09-port-"))
    return run(root, args.dafny_file.resolve(), args.verus_file.resolve(), out.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
