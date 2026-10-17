/* CONTRACT
goal: prove every statement under STATEMENTS, which are the statements of research/q17_statements.dfy copied here unchanged; change no statement
allowed-files:
  - dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy
acceptance:
  - re-verify after every edit with `scripts/vcheck dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy`; never stack unverified edits
  - `scripts/vcheck --gate dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy` exits 0, with zero tool-counted holes
  - `scripts/specfreeze --against research/q17_statements.dfy dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy` reports no change
  - `scripts/vaudit dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy` reports no finding
  - new lemmas only under HELPERS; a statement you cannot prove is reported, never changed
*/
/*!
# Q17 The metatheory contractor — rung 13 (`/contract Q17`)

What this file ships: the language and the VC generator of
std/Q17_Vcgen.dfy (unchanged), an empty STATEMENTS section, an empty
HELPERS section and the AUDIT block at the end. As shipped it is green with
no hole: `scripts/vcheck --gate` passes on it. Check command:

    scripts/vcheck dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy

The file is outside every build: no unit includes it.

Before the run (yours, by hand, the end of H3's 35 minutes):
1. Copy this file, as shipped, to research/q17_statements.dfy, and paste
   your statements (the lemmas, still without bodies, and their witnesses)
   from the STATEMENTS section of std/Q17_Vcgen.dfy under its STATEMENTS.
   Commit it: it is the freeze reference of the run.
2. Paste the same statements under STATEMENTS here.

Learner follow-up (after the contractor delivers; THIS is the exercise, 15
minutes):
1. In a FRESH session, run /contract Q17 on this file.
2. Audit the delivery: was each statement as strong as your prose meant (a
   statement the contractor proved too easily is a finding), and did the
   contractor stop and report one it could not prove? Re-run the
   acceptance commands yourself. Fill AUDIT.
3. Copy the delivered proofs and helper lemmas back into std/Q17_Vcgen.dfy
   (H3's step 3).
*/
module Q17_AgentMetatheory {

  // Given (not an item): the language and the generator of std/Q17_Vcgen.dfy
  // (its worked example W2), unchanged.
  datatype Expr = Const(n: int) | Var(x: nat) | Plus(a: Expr, b: Expr)

  datatype BExp = Lt(l: Expr, r: Expr) | And(p: BExp, q: BExp) | Not(p: BExp) | Imp(p: BExp, q: BExp)

  datatype Cmd = Skip | Assign(x: nat, e: Expr) | Seq(c1: Cmd, c2: Cmd) | If(b: BExp, c1: Cmd, c2: Cmd)
               | While(b: BExp, inv: BExp, body: Cmd)

  datatype Outcome = Stuck | Done(s: State)

  type State = nat -> int

  function Eval(e: Expr, s: State): int
  {
    match e
    case Const(n) => n
    case Var(x) => s(x)
    case Plus(a, b) => Eval(a, s) + Eval(b, s)
  }

  predicate Holds(p: BExp, s: State)
  {
    match p
    case Lt(l, r) => Eval(l, s) < Eval(r, s)
    case And(p1, p2) => Holds(p1, s) && Holds(p2, s)
    case Not(p1) => !Holds(p1, s)
    case Imp(p1, p2) => Holds(p1, s) ==> Holds(p2, s)
  }

  function Update(s: State, x: nat, v: int): State
  {
    (y: nat) => if y == x then v else s(y)
  }

  function Exec(c: Cmd, s: State, fuel: nat): Outcome
    decreases fuel, c
  {
    match c
    case Skip => Done(s)
    case Assign(x, e) => Done(Update(s, x, Eval(e, s)))
    case Seq(c1, c2) =>
      (match Exec(c1, s, fuel)
       case Stuck => Stuck
       case Done(s1) => Exec(c2, s1, fuel))
    case If(b, c1, c2) => if Holds(b, s) then Exec(c1, s, fuel) else Exec(c2, s, fuel)
    case While(b, inv, body) =>
      if fuel == 0 then Stuck
      else if !Holds(b, s) then Done(s)
      else
        (match Exec(body, s, fuel - 1)
         case Stuck => Stuck
         case Done(s1) => Exec(While(b, inv, body), s1, fuel - 1))
  }

  function SubstE(t: Expr, x: nat, e: Expr): Expr
  {
    match t
    case Const(n) => Const(n)
    case Var(y) => if y == x then e else Var(y)
    case Plus(a, b) => Plus(SubstE(a, x, e), SubstE(b, x, e))
  }

  function SubstB(p: BExp, x: nat, e: Expr): BExp
  {
    match p
    case Lt(l, r) => Lt(SubstE(l, x, e), SubstE(r, x, e))
    case And(p1, p2) => And(SubstB(p1, x, e), SubstB(p2, x, e))
    case Not(p1) => Not(SubstB(p1, x, e))
    case Imp(p1, p2) => Imp(SubstB(p1, x, e), SubstB(p2, x, e))
  }

  function Pre(c: Cmd, q: BExp): BExp
  {
    match c
    case Skip => q
    case Assign(x, e) => SubstB(q, x, e)
    case Seq(c1, c2) => Pre(c1, Pre(c2, q))
    case If(b, c1, c2) => And(Imp(b, Pre(c1, q)), Imp(Not(b), Pre(c2, q)))
    case While(b, inv, body) => inv
  }

  function Vcs(c: Cmd, q: BExp): set<BExp>
  {
    match c
    case Skip => {}
    case Assign(x, e) => {}
    case Seq(c1, c2) => Vcs(c1, Pre(c2, q)) + Vcs(c2, q)
    case If(b, c1, c2) => Vcs(c1, q) + Vcs(c2, q)
    case While(b, inv, body) =>
      {Imp(And(inv, b), Pre(body, inv)), Imp(And(inv, Not(b)), q)} + Vcs(body, inv)
  }

  ghost predicate Valid(p: BExp)
  {
    forall s :: Holds(p, s)
  }

  // item: Q17.A1d S8

  // ### STATEMENTS (yours, copied unchanged from research/q17_statements.dfy)

  // ### HELPERS (the contractor's lemmas, only here)
}

// AUDIT (learner-owned; after the contract run)
//   each statement as strong as the prose meant? (proved too easily = a finding):
//   did the contractor stop and report a statement, or change one, or touch another file:
//   the helpers it added, and which of them you would have stated yourself:
