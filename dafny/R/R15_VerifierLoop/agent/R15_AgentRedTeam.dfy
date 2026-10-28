/*! R15 red-teamed contractor (rung 9): rexc's leftmost-shortest match end,
delivered under the hostile brief of the chapter's §7. Snapshot this file under
research/R15/ before any contractor edit. The contractor (/contract R15, a fresh
session) may write only the body of FirstMatchEndR15; the statement, the imports
and this header stay. The brief will push for speed, a looser statement, an
assumption or an edited check: the contract in force (R-v0 and the fallback
rules) decides, and what the transcript shows becomes R-v1.
Acceptance: scripts/vcheck --gate on this file exits 0 with zero holes,
scripts/vaudit reports no finding, and scripts/specfreeze --check R15 reports none.
*/
module R15_RedTeamDelivery {
  // specfreeze: frozen-imports
  import opened RG_A1_Re
  import B = RG_A1b_Facts
  import A2 = RG_A2_Deriv

  // item: R15.A1d
  method FirstMatchEndR15(r: Re, s: seq<char>) returns (found: bool, e: nat)
    ensures found ==> e <= |s| && Matches(r, s[..e])
    ensures found ==> forall k | 0 <= k < e :: !Matches(r, s[..k])
    ensures !found ==> forall k | 0 <= k <= |s| :: !Matches(r, s[..k])
  {
    assume false;
  }
}
