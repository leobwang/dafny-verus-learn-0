#!/usr/bin/env python3
"""Check whether the specified constructor contracts support the R10 consumer.

This checks logical sufficiency on arbitrary normal inputs/results. It never
uses constructor bodies. Implementability, examples, snapshots and complete
native gates are separate obligations. Run under a capped native lane.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile


def driver(core, source: Path, lang: str) -> str:
    text = source.read_text()
    clauses = {}
    if lang == "d":
        parsed = core.D.parse_source(text, str(source))
        for op in ["Alt", "Cat", "Star"]:
            name = "Build" + op + "R10"
            found = [d for d in parsed.decls if d.name == name]
            if len(found) != 1:
                raise ValueError(f"expected exactly one {name}")
            _, parts = core.dafny_spec_parts(parsed, found[0])
            clauses[op] = {k: [c.removeprefix(k).strip() for c in v]
                           for k, v in parts.items()}
        result = "module R10_StatementConsumer {\n import opened RG_A1_Re\n import opened RG_A4_Norm\n"
        for op, parts in clauses.items():
            params = "a:NormRe,b:NormRe,out:NormRe" if op != "Star" else "a:NormRe,out:NormRe"
            args = "a,b" if op != "Star" else "a"
            pre = " && ".join("(" + x + ")" for x in parts["requires"]) or "true"
            post = " && ".join("(" + x + ")" for x in parts["ensures"]) or "true"
            result += (f" lemma {{:induction false}} Ready{op}R10({params})\n"
                       f"  ensures ({pre})\n"
                       f"  ensures ({pre}) && ({post}) ==> EquivalentReR10(out,{op}({args}))\n {{}}\n")
        return result + "}\n"
    parsed = core.V.vs.parse(text)
    for op in ["alt", "cat", "star"]:
        name = "build_" + op + "_r10"
        found = [it for it in parsed.walk() if it.kind == "fn" and it.name == name]
        if len(found) != 1:
            raise ValueError(f"expected exactly one {name}")
        _, clauses[op] = core.verus_spec_parts(parsed, found[0])
    result = "use vstd::prelude::*;\nuse rg_re_a1::*;\nuse rg_re_a4::*;\nverus! {\n"
    for op, parts in clauses.items():
        params = "a:NormRe,b:NormRe,out:NormRe" if op != "star" else "a:NormRe,out:NormRe"
        domain = "is_norm(a.re()),is_norm(out.re())," + ("is_norm(b.re())," if op != "star" else "")
        raw = f"Re::{op.title()}(Box::new(a.re())" + (",Box::new(b.re())" if op != "star" else "") + ")"
        pre = " && ".join("(" + x + ")" for x in parts["requires"]) or "true"
        post = " && ".join("(" + x + ")" for x in parts["ensures"]) or "true"
        result += (f"proof fn ready_{op}_r10({params})\n requires {domain}\n"
                   f" ensures ({pre}),\n ({pre}) && ({post}) ==> equiv(out.re(),{raw}),\n {{}}\n")
    return result + "}\n"


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lang", choices=["d", "v", "both"], default="both")
    ap.add_argument("--dafny-file", type=Path, default=root / "dafny/R/R10_TypeInvariants/agent/R10_AgentFlagship.dfy")
    ap.add_argument("--verus-file", type=Path, default=root / "verus/r/r10_type_invariants/src/agent.rs")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    out = args.out or Path(tempfile.mkdtemp(prefix="dvl0-r10-statements-"))
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root / "tests/wrappers"))
    import test_tools_common as common

    core = common.load_script("vcheck")
    report = {"claim": "contract sufficiency for the printed consumer; no implementation assumed",
              "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "results": {}}
    ok = True
    for lang, source, lib in [("d", args.dafny_file, core.D), ("v", args.verus_file, core.V)]:
        if args.lang not in [lang, "both"]:
            continue
        generated = driver(core, source, lang)
        report["results"][lang] = {"source": str(source.resolve()),
                                    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        if lang == "d":
            names = ["RG_A1_Re", "RG_A1b_Facts", "RG_A2_Deriv", "RG_A2_MatcherStatement", "RG_A3_Syntax", "RG_A4_Norm"]
            includes = "".join("include " + json.dumps(str(root / "dafny/given/R" / (n + ".dfy"))) + "\n" for n in names)
            target = out / "consumer.dfy"
            target.write_text(includes + generated)
        else:
            target = out / "consumer-verus"
            (target / "src").mkdir(parents=True, exist_ok=True)
            (target / "src/lib.rs").write_text(generated)
            cargo = '[package]\nname="r10_statement_consumer"\nversion="0.1.0"\nedition="2021"\nbuild=false\n[dependencies]\nvstd="=0.0.0-2026-09-20-0158"\n'
            for layer in ["a1", "a1b", "a2", "a3", "a4"]:
                name = "rg_re_" + layer
                cargo += name + "={path=" + json.dumps(str(root / "verus/given" / name)) + "}\n"
            cargo += '[package.metadata.verus]\nverify=true\n[workspace]\n'
            (target / "Cargo.toml").write_text(cargo)
        result = lib.verify(str(target), gate=True)
        data = result.to_dict()
        report["results"][lang]["native"] = data
        passed = result.verdict == "verified" and not result.holes
        ok &= passed
        print(f"{lang}: {'consumer proved' if passed else 'consumer not proved'} ({result.verdict})", flush=True)
        (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Retained generated consumer and native evidence: {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
