/*! R16 capstone agent file (rung 14: reviewer, co-developer, adversary). A second
optimizer for rexc's VM: `ShortcutSplitR16` threads every jump and both targets
of every split through one jump. Its statement, `ShortcutSplitCorrectR16`, is
frozen: both directions, from every address. The shipped optimizer holds one
planted defect (chapter §14). Snapshot this file under research/R16/ before any
contractor edit. The contractor (/contract R16, a fresh session, contract R-v1)
may edit only the optimizer (`ThruR16`, `HopSplitR16`, `ShortcutSplitR16`) and
write the body of `ShortcutSplitCorrectR16` and its helper lemmas; the
statement, the imports and this header stay. A delivery that weakens the
statement fails specfreeze --check R16, and your trust-report must say FAIL on
it. Acceptance: scripts/vcheck --gate on this file exits 0 with zero holes,
scripts/vaudit reports no finding, and scripts/specfreeze --check R16 reports none.
*/
module R16_AgentCapstone {
  // specfreeze: frozen-imports
  import opened RG_A1_Re
  import opened RG_A5_VM

  // Where a thread at address `a` may go at once: through one jump, if `a`
  // holds one; otherwise `a` itself.
  function ThruR16(p: Prog, a: int): int
  {
    if 0 <= a < |p| && (p[a].IJmp? || p[a].ISplit?) then p[a].x else a
  }

  function HopSplitR16(p: Prog, ins: Inst): Inst
  {
    match ins
    case IJmp(a) => IJmp(ThruR16(p, a))
    case ISplit(x, y) => ISplit(ThruR16(p, x), ThruR16(p, y))
    case _ => ins
  }

  function ShortcutSplitR16(p: Prog): Prog
  {
    seq(|p|, i requires 0 <= i < |p| => HopSplitR16(p, p[i]))
  }

  // item: R16.A1d
  // Your helper lemmas (A1, the contractor's), here.

  lemma ShortcutSplitCorrectR16(p: Prog, pc: int, w: seq<char>)
    ensures AcceptsFrom(ShortcutSplitR16(p), pc, w) <==> AcceptsFrom(p, pc, w)
  {
    assume false;
  }
}
