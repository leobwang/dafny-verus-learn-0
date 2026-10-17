// item: R11.P3dv verdict
// Local changed rule then original canonical rule, D:<x>,<y> V:<x>,<y>.
// SLOT: CHECK P3dv
// item: R11.P5dv verdict
// Success-only producer promise then complete rejection promise, D:<x>,<y> V:<x>,<y>.
// SLOT: CHECK P5dv
/*! R11 — Theory. Standalone A1–A4, fixed relative certificate rules.
The core has T1 plus seven hand/project tasks in Dafny and nine in Verus;
the checkpoint has two tasks in each language. Preserve models and domains.
Compiled checks, metatheory and rule fidelity establish different properties.
Tracked evidence is proof data; runtime certificates are ordinary derivations.
*/
module R11_Kernel {
 // specfreeze: frozen-imports
 import opened RG_A1_Re
 import opened RG_A4_Norm
// item: R11.W2d
 datatype EvidenceR11=EvidenceR11(ghost expression:RG_A1_Re.Re,ghost word:seq<char>,ghost tree:RG_A4_Norm.Derivation)
 ghost function PackEvidenceR11(r:RG_A1_Re.Re,s:seq<char>,d:RG_A4_Norm.Derivation):(out:EvidenceR11)
  requires RG_A4_Norm.CheckDeriv(r,s,d)
  ensures RG_A4_Norm.CheckDeriv(out.expression,out.word,out.tree)
 {EvidenceR11(r,s,d)}
 // item: R11.H2d
// pair: R11.H2v
lemma {:induction false} CheckSoundR11(r: Re, s: seq<char>, d: Derivation)
    requires CheckDeriv(r, s, d)
    ensures Matches(r, s)
    decreases d
  { assume false; }
// item: R11.H3d
// pair: R11.H3v
lemma {:induction false} DirectCompleteR11(r: Re, s: seq<char>) returns (d: Derivation)
    requires Matches(r, s)
    ensures CheckDeriv(r, s, d)
    decreases r, |s|
  { assume false; }
// item: R11.H1d
// pair: R11.H1v
method CheckCertificateR11(r:Re,s:seq<char>,d:Derivation) returns (ok:bool)
 ensures ok==CheckDeriv(r,s,d)
 decreases d
{ assume false; }
}
module R11_Streaming {
 // specfreeze: frozen-imports
 import opened RG_A1_Re
 import opened RG_A1b_Facts
 import opened RG_A2_Deriv
 opaque ghost predicate ResidualR11(r:Re,current:Re,prefix:seq<char>) {
  forall tail:seq<char> :: Matches(current,tail)<==>Matches(r,prefix+tail)
 }
 // item: R11.W1d
lemma ResidualStartR11(r:Re)
  ensures ResidualR11(r,r,[])
 {
  // did: unfold the fixed model for this constructor obligation.
  reveal ResidualR11();
  forall tail:seq<char> ensures Matches(r,tail)<==>Matches(r,[]+tail) {assert []+tail==tail;}
 }
 // item: R11.W3d
lemma ResidualStepR11(r:Re,current:Re,prefix:seq<char>,c:char)
  requires ResidualR11(r,current,prefix)
  ensures ResidualR11(r,Deriv(current,c),prefix+[c])
 {
  // did: unfold the fixed model for this constructor obligation.
  reveal ResidualR11();
  forall tail:seq<char>
   ensures Matches(Deriv(current,c),tail)<==>Matches(r,(prefix+[c])+tail)
  {DerivCorrect(current,c,tail);assert prefix+([c]+tail)==(prefix+[c])+tail;}
 }
 lemma ResidualObserveR11(r:Re,current:Re,prefix:seq<char>)
  requires ResidualR11(r,current,prefix)
  ensures Nullable(current)==Matches(r,prefix)
 {reveal ResidualR11();NullableCorrect(current);assert prefix+[]==prefix;}
 // item: R11.H4d
// pair: R11.H4v
method PrefixMatchesR11(r:Re,s:seq<char>) returns (accepted:bool,trace:seq<bool>)
  ensures accepted==Matches(r,s)
  ensures |trace|==|s|
  ensures forall j |0<=j<|s| :: trace[j]==Matches(r,s[..j+1])
 { assume false; }
}
module R11_Search {
 // specfreeze: frozen-imports
 import opened RG_A1_Re
 import opened RG_A4_Norm
 datatype CertChoiceR11=NoCertR11|HasCertR11(value:Derivation)
 // item: R11.H5d
// pair: R11.H5v
method SearchR11(r:Re,s:seq<char>) returns (out:CertChoiceR11)
  ensures out.HasCertR11? ==> CheckDeriv(r,s,out.value)
  ensures out.NoCertR11? ==> !Matches(r,s)
  decreases r,|s|
 { assume false; }
 // item: R11.H6d
// pair: R11.H6v
method SearchCatR11(a:Re,b:Re,s:seq<char>,k:nat) returns(out:CertChoiceR11)
  requires k<=|s|+1
  requires forall i |0<=i<k && i<=|s| :: !(Matches(a,s[..i]) && Matches(b,s[i..]))
  ensures out.HasCertR11? ==> CheckDeriv(Cat(a,b),s,out.value)
  ensures out.NoCertR11? ==> !Matches(Cat(a,b),s)
  decreases Cat(a,b),|s|,|s|+1-k
 { assume false; }
 // item: R11.H7d
// pair: R11.H7v
method SearchStarR11(a:Re,s:seq<char>,k:nat) returns(out:CertChoiceR11)
  requires s!=[] && 1<=k<=|s|+1
  requires forall i |0<i<k && i<=|s| :: !(Matches(a,s[..i]) && Matches(Star(a),s[i..]))
  ensures out.HasCertR11? ==> CheckDeriv(Star(a),s,out.value)
  ensures out.NoCertR11? ==> !Matches(Star(a),s)
  decreases Star(a),|s|,|s|+1-k
 { assume false; }
}
module R11_WpReview {
 // specfreeze: frozen-imports
 // item: R11.T1d
// pair: R11.T1v
method WpIndexStepR11(i:nat,len:nat) returns(next:nat)
  requires i<len
  ensures next==i+1 && next<=len
 { assume false; }
}
