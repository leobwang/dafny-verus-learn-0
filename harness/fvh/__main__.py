"""python -m fvh — the harness's command line (DV4-PLAN §3.1, §3.6, §4, §6).

Run from harness/ (`uv run --offline --frozen --directory harness python -m fvh …`):

  run <ID> --plan PLAN.toml [--dry-run] [--mem-gb N]
      a batch (fvh.batch): the pre-registration gate (for a lab plan), the
      apparatus check, the ledger against its anchors, no open batch, and the
      plan against the registry budget; then the plan in the ledger, the open
      anchor and every attempt in plan order, each a harness-executed run
      with every Verify in a fresh verification container; the batch closes
      when every id is settled. --dry-run stops after the checks and prints
      the plan's arithmetic. --mem-gb caps each verification container
      (a lane whose memory share is below the pinned bound).
  resume <ID> [--dry-run] [--mem-gb N] [--after-overage-check] [--new-apparatus]
      the open batch: the apparatus checked as for run (and the apparatus
      file the batch opened on), every id a killed runner left running
      settled from its run directory (truncated:interrupted after model
      output, else infra-failed), then the planned, deferred and re-issuable
      ids run in plan order (never a scored one); --dry-run lists them (with
      the plan's max_reissue). --after-overage-check clears a recorded
      overage stop once the human has checked the account; --new-apparatus
      records a changed apparatus file in the ledger instead of refusing.
  ledger <ID>
      the ledger's attempts by state, the chain and the anchors checked.
  report <ID> [--reverify RUN|all | --judge RUN|all --truth ARCHIVE] [--mem-gb N]
      the frozen half of the report (fvh.report): outcomes re-derived from
      the logs, the ledger re-checked, the apparatus and disclosure block.
      --reverify re-runs the gate on a run's returned files in a fresh
      verification container, from the run's own course commit (Docker
      needed); "all" does every run that recorded a verification.
      --judge re-judges each lab run's delivered task file against the
      lab's sealed reference in the grader container (fvh.judging; the key
      on this machine needed; --truth names the archive sandbox/truth.toml
      pins, so a study session's guard refuses the line): one verdict word
      per run, printed, never written into a run directory.
  apparatus [--check]
      the apparatus facts as JSON; --check compares the host with the pins,
      and, when the apparatus pins a Qwen backend and models are enabled, the
      live model server (version, digests, the unit's settings).
  unseal <ID> [--dry-run]
      the module's sealed lab tasks (fvh.statements; QPLAN §28.6, §30 Q64):
      refused until every statement file expected/<ID>.statements names is
      committed with content other than its shipped form; then each sealed
      stratum's archive is checked, decrypted with the pinned age binary and
      the key on this machine, checked against its manifest and the
      stratum's pins, and its cards' task files are written (never over a
      file that differs). --dry-run runs every check and writes nothing.
  contract-local <ID> [--file PATH] [--from REV] [--dry-run]
      the CONTRACT parsed and its allowlist validated (fvh.contract), the
      starting state found and the acceptance lines classified. The replay
      itself is scripts/contract_local.sh's, live from DV4 step 3b.

The PLAN.toml of `run`: fvh.batch's module docstring (seed, tasks and their
[task.<id>] paths, repeats, attempts, the [[arm]] tables with each arm's
family, rounds, policy and construct, the material, lever_check).

Exit codes: 0 done (a batch closed, every re-verification agreed), 1 a check
failed (a run not reproduced or not re-verified, a batch interrupted or left
with re-issuable ids), 2 usage, 3 refused (a check failed, or the batch was
deferred or stopped between attempts: it stays open for `fvh resume`). A live
batch is refused with FVH_NO_MODEL=1 or DVL_NO_DOCKER=1 (the CI environment).
Frozen (guard rule 2f), standard library only.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from fvh import apparatus, backends, batch, budget, contract, prereg, report, statements, tools
from fvh import judging

EXIT_OK, EXIT_FAIL, EXIT_USAGE, EXIT_REFUSED = 0, 1, 2, 3
ROOT = Path(__file__).resolve().parents[2]


class Refusal(Exception):
    pass


def say(msg, *, err=False):
    print(f"fvh: {msg}", file=sys.stderr if err else sys.stdout)


def _module(root, mid):
    try:
        return contract.record(root, mid.upper())
    except contract.Refused as e:
        raise Refusal(str(e)) from None


def _load_plan(path, root):
    try:
        plan = batch.load_plan(path, root)
    except batch.BatchError as e:
        raise Refusal(str(e)) from None
    return plan, plan.items()


def _live_ok():
    """A live batch calls a model and runs verification containers: refused in
    the CI environment before anything is written."""
    try:
        backends.refuse_if_disabled()
    except backends.ModelDisabled as e:
        raise Refusal(str(e)) from None
    if os.environ.get("DVL_NO_DOCKER") == "1":
        raise Refusal("DVL_NO_DOCKER=1 is set (the CI environment): no verification container "
                      "runs here")


def _server_check(app):
    """(drift, found): the host's model server as fvh.backends.gate.discover finds
    it (Δ505). No server answering, or a model that cannot be chosen, is one
    drift line (a batch refuses); the server's identity is never pinned.
    ([], None) when the apparatus pins no Qwen backend or models are disabled (CI)."""
    if budget.QWEN not in app.families():
        return [], None
    try:
        backends.refuse_if_disabled()
    except backends.ModelDisabled:
        return [], None
    from fvh.backends import gate as G
    try:
        return [], G.discover(app)
    except G.GateError as e:
        return [apparatus.Drift("model_server", "an OpenAI-compatible server on localhost "
                                "(127.0.0.1) port 8000 or 8001", str(e),
                                "start your model server, or set DVL_MODEL_URL / DVL_MODEL")], None


def _server_drift(app):
    return _server_check(app)[0]


def _checks(root, rec, *, lab, server=False):
    """The batch's refusal checks; returns the pre-registration hash (or "")."""
    mid = rec["id"]
    if rec.get("status") == "planned":
        raise Refusal(f"{mid} is planned: not authored yet")
    full = ""
    if lab:
        try:
            full = prereg.check(root, mid)
        except prereg.PreregRefused as e:
            raise Refusal(str(e)) from None
    try:
        app = apparatus.load(root=root)
    except apparatus.ApparatusError as e:
        raise Refusal(str(e)) from None
    drift = apparatus.check(app, root)
    if server and not drift:
        drift = _server_drift(app)
    if drift:
        raise Refusal("apparatus drift: " + "; ".join(d.line() for d in drift))
    try:
        budget.check_anchors(root, mid)
    except (budget.AnchorError, budget.LedgerError) as e:
        raise Refusal(str(e)) from None
    return full


def cmd_run(a, root):
    rec = _module(root, a.module)
    plan, items = _load_plan(a.plan, root)
    full = _checks(root, rec, lab=bool(plan.lab), server=budget.QWEN in plan.families())
    last = budget.last_anchor(root, rec["id"])
    if last is not None and last["event"] == "open":
        raise Refusal(f"{rec['id']}'s last batch is still open: resume it (fvh resume)")
    ledger = budget.Ledger(budget.ledger_path(root, rec["id"]))
    problems = budget.check_plan(items, rec.get("budget") or {}, used=ledger.used())
    if problems:
        raise Refusal("; ".join(problems))
    tot = budget.plan_totals(items)
    say(f"{rec['id']}: plan of {len(items)} attempt(s): " + ", ".join(
        f"{f} {t['calls']} calls / {t['runs']} runs" for f, t in tot.items() if t["runs"])
        + (f"; pre-registration {full[:16]}" if full else "")
        + f"; plan sha256 {plan.sha256[:16]}; base seed {plan.seed}"
        + ("; the lab gate's lever check on every Verify" if plan.lever_check else ""))
    if a.dry_run:
        say("dry run: every check passed; nothing was written")
        return EXIT_OK
    _live_ok()
    try:
        b = batch.Batch(root, rec["id"], plan, mem_gb=a.mem_gb)
        n = b.open()
        say(f"{rec['id']}: batch opened ({n} attempt(s) planned and anchored)")
        return b.run()
    except batch.BatchError as e:
        raise Refusal(str(e)) from None


def cmd_resume(a, root):
    rec = _module(root, a.module)
    try:
        budget.check_anchors(root, rec["id"])
    except (budget.AnchorError, budget.LedgerError) as e:
        raise Refusal(str(e)) from None
    last = budget.last_anchor(root, rec["id"])
    if last is None or last["event"] != "open":
        raise Refusal(f"{rec['id']} has no open batch to resume")
    ledger = budget.Ledger(budget.ledger_path(root, rec["id"]))
    if a.dry_run and batch.batch_note(ledger) is not None:
        try:                                      # the plan's own max_reissue (DV5c)
            return batch.resume(root, rec["id"], dry_run=True, check_apparatus=False)
        except batch.BatchError as e:
            raise Refusal(str(e)) from None
    if a.dry_run:                                 # a batch fvh run did not open: no plan
        att = ledger.attempts()
        running = [i for i, x in att.items() if x.state == "running"]
        ids = budget.resume_order(ledger)
        say(f"{rec['id']}: {len(running)} running id(s) to settle, {len(ids)} id(s) to re-issue, "
            "in plan order (no plan note: the default max_reissue)")
        for i in running:
            print(f"  settle {i}")
        for i in ids:
            print(f"  {i}")
        return EXIT_OK
    _checks(root, rec, lab=False)                 # the apparatus drift, as for run (DV5c)
    _live_ok()
    try:
        return batch.resume(root, rec["id"], mem_gb=a.mem_gb,
                            after_overage_check=a.after_overage_check,
                            new_apparatus=a.new_apparatus)
    except batch.BatchError as e:
        raise Refusal(str(e)) from None


def cmd_ledger(a, root):
    rec = _module(root, a.module)
    try:
        n = budget.check_anchors(root, rec["id"])
    except (budget.AnchorError, budget.LedgerError) as e:
        raise Refusal(str(e)) from None
    ledger = budget.Ledger(budget.ledger_path(root, rec["id"]))
    att = ledger.attempts()
    by = {}
    for x in att.values():
        by[x.state] = by.get(x.state, 0) + 1
    used = ledger.used()
    say(f"{rec['id']}: {len(ledger.texts())} ledger line(s), chain intact, {n} anchor(s) "
        "checked")
    print("  attempts: " + (", ".join(f"{k} {v}" for k, v in sorted(by.items())) or "none"))
    for f, t in used.items():
        if t["runs"] or t["calls"]:
            print(f"  {f}: {t['calls']} calls planned or spent, {t['runs']} runs planned")
    return EXIT_OK


def cmd_report(a, root):
    rec = _module(root, a.module)
    if a.judge and a.reverify:
        raise Refusal("--judge and --reverify are two runs: name one")
    if bool(a.judge) != bool(a.truth):
        raise Refusal("--judge RUN|all goes with --truth ARCHIVE (the lab's sealed archive)")
    if a.judge:
        try:
            got = judging.judge(root, rec["id"], a.judge, archive=a.truth, mem_gb=a.mem_gb)
        except (ValueError, OSError) as e:
            raise Refusal(str(e)) from None
        for r in got:
            print(f"  {r.run_id} {r.card or '-'}: {r.verdict or 'not judged'}"
                  + (f" ({r.detail})" if r.detail else ""))
        considered = [r for r in got if not r.excluded]     # excluded runs: never counted
        judged = [r for r in considered if r.verdict]
        counts = {}
        for r in judged:
            counts[r.verdict] = counts.get(r.verdict, 0) + 1
        ex = len(got) - len(considered)
        say(f"judge {rec['id']}: {len(judged)}/{len(considered)} run(s) judged against the "
            "sealed reference" + (": " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
                                  if counts else "")
            + (f"; {ex} run(s) of an excluded outcome not judged" if ex else ""))
        return EXIT_OK if considered and len(judged) == len(considered) else EXIT_FAIL
    if a.reverify:
        try:
            got = report.reverify_all(root, rec["id"], mem_gb=a.mem_gb) if a.reverify == "all" \
                else [report.reverify(root, rec["id"], a.reverify, mem_gb=a.mem_gb)]
        except (ValueError, OSError) as e:
            raise Refusal(str(e)) from None
        except (tools.RunnerUnavailable, tools.PreflightError) as e:
            raise Refusal(f"the verification container cannot run: {e}") from None
        for r in got:
            mark = "ok " if r.ok else "NOT"
            print(f"  [{mark}] {r.run_id} {r.target or '-'}: recorded {r.recorded[0]} "
                  f"(holes {r.recorded[1]}, verified {r.recorded[2]}), re-verified "
                  f"{r.derived[0]} (holes {r.derived[1]}, verified {r.derived[2]})"
                  + (f" ({r.detail})" if r.detail else ""))
        n_ok = sum(r.ok for r in got)
        say(f"reverify {rec['id']}: {n_ok}/{len(got)} run(s) re-verified to their recorded "
            "verdict" + ("" if n_ok == len(got) else "; a difference is a report finding"))
        return EXIT_OK if n_ok == len(got) else EXIT_FAIL
    rep = report.build(root, rec["id"])
    sys.stdout.write(report.format_report(rep))
    if not rep.ledger_ok:
        return EXIT_REFUSED
    return EXIT_OK if rep.reproduced else EXIT_FAIL


def cmd_apparatus(a, root):
    try:
        app = apparatus.load(root=root)
    except apparatus.ApparatusError as e:
        raise Refusal(str(e)) from None
    if a.check:
        drift = apparatus.check(app, root)
        found = None
        if not drift:
            drift, found = _server_check(app)
        for d in drift:
            say(f"drift: {d.line()}", err=True)
        if drift:
            return EXIT_REFUSED
        if found:
            say(f"model server (found, not pinned): {found['base_url']}, model {found['model']}, "
                f"max_model_len {found['max_model_len']}, version {found['version']}")
        say("apparatus: the host matches the pins")
        return EXIT_OK
    print(json.dumps(apparatus.collect(app, root), indent=1, sort_keys=True))
    return EXIT_OK


def cmd_unseal(a, root):
    rec = _module(root, a.module)
    if rec.get("status") == "planned":
        raise Refusal(f"{rec['id']} is planned: not authored yet")
    try:
        got = statements.unseal(root, rec["id"], dry_run=a.dry_run)
    except statements.StatementsRefused as e:
        raise Refusal(str(e)) from None
    for path, sha in sorted(got["statements"].items()):
        say(f"{rec['id']}: {path} committed (sha256 {sha[:16]})")
    for s in got["strata"]:
        say(f"{s['stratum']}: archive {s['archive_sha256'][:16]}, manifest "
            f"{s['manifest_sha256'][:16]}: {s['files']} task file(s); "
            + (f"dry run: {s['written']} would be written, {s['kept']} already in place"
               if a.dry_run else f"{s['written']} written, {s['kept']} already in place"))
    return EXIT_OK


def cmd_contract_local(a, root):
    rec = _module(root, a.module)
    agentic = [p for p in rec.get("agentic", []) if not p.endswith("/")]
    if rec.get("solo") or not agentic:
        raise Refusal(f"{rec['id']} has no agentic exercise a contract can name")
    if a.file:
        if a.file not in agentic:
            raise Refusal(f"--file {a.file} is not in {rec['id']}'s agentic list")
        target = a.file
    elif len(agentic) == 1:
        target = agentic[0]
    else:
        raise Refusal(f"{rec['id']} lists {len(agentic)} agentic files: name one with --file")
    try:
        text = (Path(root) / target).read_text(encoding="utf-8")
        c = contract.parse_header(text)
        for p in c["allowed-files"]:
            why = contract.path_problem(p, rec)
            if why:
                raise contract.Refused(f"allowed file {p}: {why}")
        rev, snap = contract.starting_state(root, c, a.from_rev)
    except OSError as e:
        raise Refusal(f"{target}: {e}") from None
    except contract.Refused as e:
        raise Refusal(str(e)) from None
    say(f"{rec['id']} ({target}): starting state {rev}" + (f", snapshot {snap}" if snap else ""))
    for line in c["acceptance"]:
        form, _ = contract.classify_line(line)
        print(f"  - [{form}] {line[:100]}")
    if a.dry_run:
        return EXIT_OK
    raise Refusal("the replay runs through scripts/contract_local.sh, live from DV4 step 3b")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m fvh", allow_abbrev=False,
                                 description="The course's research harness.")
    ap.add_argument("--root", help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run", allow_abbrev=False)
    p.add_argument("module")
    p.add_argument("--plan", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--mem-gb", type=float)
    p = sub.add_parser("resume", allow_abbrev=False)
    p.add_argument("module")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--mem-gb", type=float)
    p.add_argument("--after-overage-check", action="store_true")
    p.add_argument("--new-apparatus", action="store_true")
    p = sub.add_parser("ledger", allow_abbrev=False)
    p.add_argument("module")
    p = sub.add_parser("report", allow_abbrev=False)
    p.add_argument("module")
    p.add_argument("--reverify", metavar="RUN")
    p.add_argument("--judge", metavar="RUN")
    p.add_argument("--truth", metavar="ARCHIVE")
    p.add_argument("--mem-gb", type=float)
    p = sub.add_parser("apparatus", allow_abbrev=False)
    p.add_argument("--check", action="store_true")
    p = sub.add_parser("unseal", allow_abbrev=False)
    p.add_argument("module")
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("contract-local", allow_abbrev=False)
    p.add_argument("module")
    p.add_argument("--file")
    p.add_argument("--from", dest="from_rev")
    p.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve() if a.root else ROOT
    fn = {"run": cmd_run, "resume": cmd_resume, "ledger": cmd_ledger, "report": cmd_report,
          "apparatus": cmd_apparatus, "unseal": cmd_unseal,
          "contract-local": cmd_contract_local}[a.cmd]
    try:
        return fn(a, root)
    except Refusal as e:
        say(f"refused: {e}", err=True)
        return EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
