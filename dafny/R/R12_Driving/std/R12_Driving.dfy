// item: R12.P3dv verdict
// Same source: selected good declaration then full target, D:<x>,<y> V:<x>,<y>.
// SLOT: CHECK P3dv
// item: R12.P5dv verdict
// Synthetic fields-only then original-revision-bound consumer, D:<x>,<y> V:<x>,<y>.
// SLOT: CHECK P5dv
/*! R12 — Driving the verifier + Lab α.
T1 is bounded remaining-budget arithmetic. H1/H2 keep provided executable bodies:
remove their counted assumptions and write only the loop-invariant hints. The
count-step and final slice equality are supplied worked facts. Verifier outcome
flags are input data; counting them does not establish a program's proof status.
*/
module R12_HintSites {
 // specfreeze: frozen-imports
 // item: R12.W1d
 ghost function AcceptedCountR12(flags:seq<bool>):nat
  decreases |flags|
 {if flags==[] then 0 else AcceptedCountR12(flags[..|flags|-1])+(if flags[|flags|-1] then 1 else 0)}
 lemma AcceptedStepR12(flags:seq<bool>,i:nat)
  requires i<|flags|
  ensures AcceptedCountR12(flags[..i+1])==AcceptedCountR12(flags[..i])+(if flags[i] then 1 else 0)
 {assert flags[..i+1][..i]==flags[..i];}
 // item: R12.T1d
// pair: R12.T1v
 method RemainingBudgetR12(spent:nat,limit:nat) returns(out:nat)
  requires spent<=limit
  ensures out+spent==limit
 {assume false;}
 // item: R12.H1d
// pair: R12.H1v
 method CountAcceptedR12(flags:seq<bool>) returns(accepted:nat)
  ensures accepted==AcceptedCountR12(flags) && accepted<=|flags|
 {
  var i:=0;accepted:=0;
  assume false;
  while i<|flags|
   // @hole-begin R12.H1d


   // @hole-end R12.H1d
  {
   AcceptedStepR12(flags,i);
   if flags[i] {accepted:=accepted+1;}
   i:=i+1;
  }
  assert i==|flags|;
  // did: connect the consumed-prefix slice to the original flags at exit.
  assert flags[..i]==flags;
 }
 // item: R12.H2d
// pair: R12.H2v
 method FirstRejectionR12(flags:seq<bool>) returns(at:nat)
  ensures at<=|flags|
  ensures forall j |0<=j<at :: flags[j]
  ensures at==|flags| || !flags[at]
 {
  at:=0;
  assume false;
  while at<|flags| && flags[at]
   // @hole-begin R12.H2d


   // @hole-end R12.H2d
  {at:=at+1;}
 }
}
