module R12_HintSites {
 ghost function AcceptedCountR12(flags:seq<bool>):nat
  decreases |flags|
 {if flags==[] then 0 else AcceptedCountR12(flags[..|flags|-1])+(if flags[|flags|-1] then 1 else 0)}
 lemma AcceptedStepR12(flags:seq<bool>,i:nat)
  requires i<|flags|
  ensures AcceptedCountR12(flags[..i+1])==AcceptedCountR12(flags[..i])+(if flags[i] then 1 else 0)
 {assert flags[..i+1][..i]==flags[..i];}
 // item: R12.T1d
 method RemainingBudgetR12(spent:nat,limit:nat) returns(out:nat)
  requires spent<=limit
  ensures out+spent==limit
 {out:=limit-spent;}
 // item: R12.H1d
 method CountAcceptedR12(flags:seq<bool>) returns(accepted:nat)
  ensures accepted==AcceptedCountR12(flags) && accepted<=|flags|
 {
  var i:=0;accepted:=0;
  while i<|flags|
   // @hole-begin R12.H1d
   invariant 0<=i<=|flags| && accepted<=i
   invariant accepted==AcceptedCountR12(flags[..i])
   // @hole-end R12.H1d
  {
   // @hole-begin R12.H1d
   AcceptedStepR12(flags,i);
   // @hole-end R12.H1d
   if flags[i] {accepted:=accepted+1;}
   i:=i+1;
  }
  // @hole-begin R12.H1d
  assert i==|flags|;
  assert flags[..i]==flags;
  // @hole-end R12.H1d
 }
 // item: R12.H2d
 method FirstRejectionR12(flags:seq<bool>) returns(at:nat)
  ensures at<=|flags|
  ensures forall j |0<=j<at :: flags[j]
  ensures at==|flags| || !flags[at]
 {
  at:=0;
  while at<|flags| && flags[at]
   // @hole-begin R12.H2d
   invariant 0<=at<=|flags|
   invariant forall j |0<=j<at :: flags[j]
   // @hole-end R12.H2d
  {at:=at+1;}
 }
}
