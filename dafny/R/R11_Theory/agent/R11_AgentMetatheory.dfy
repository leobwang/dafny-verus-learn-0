/*! R11 metatheory contractor: prove the fixed forward replacement theorem.
Snapshot original models/rules before body edits; verify rule fidelity against
canonical A4 separately. A transport theorem about changed rules can be true
while those rules accept invalid certificates. No model edits are authorized.
*/
module R11_AgentMetatheory {
 // specfreeze: frozen-imports
 import opened RG_A1_Re
 import opened RG_A4_Norm
 ghost function RenameCharR11(c:char,from:char,to:char):char {if c==from then to else c}
 ghost function RenameWordR11(s:seq<char>,from:char,to:char):seq<char> {seq(|s|,i requires 0<=i<|s| =>RenameCharR11(s[i],from,to))}
 ghost function RenamePatternR11(r:RG_A1_Re.Re,from:char,to:char):RG_A1_Re.Re
  decreases r
 {
  match r
  case Empty=>Empty
  case Eps=>Eps
  case Chr(c)=>Chr(RenameCharR11(c,from,to))
  case Alt(a,b)=>Alt(RenamePatternR11(a,from,to),RenamePatternR11(b,from,to))
  case Cat(a,b)=>Cat(RenamePatternR11(a,from,to),RenamePatternR11(b,from,to))
  case Star(a)=>Star(RenamePatternR11(a,from,to))
 }
 ghost predicate RulesR11(r:RG_A1_Re.Re,s:seq<char>,d:RG_A4_Norm.Derivation) {
  RG_A4_Norm.CheckDeriv(r,s,d)
 }
 lemma RenameSplitR11(s:seq<char>,k:nat,from:char,to:char)
  requires k<=|s|
  ensures |RenameWordR11(s,from,to)|==|s|
  ensures RenameWordR11(s,from,to)[..k]==RenameWordR11(s[..k],from,to)
  ensures RenameWordR11(s,from,to)[k..]==RenameWordR11(s[k..],from,to)
 {
  assert RenameWordR11(s,from,to)[..k]==RenameWordR11(s[..k],from,to);
  assert RenameWordR11(s,from,to)[k..]==RenameWordR11(s[k..],from,to);
 }
 // item: R11.A1d
lemma {:induction false} RenameTransportR11(r:RG_A1_Re.Re,s:seq<char>,d:RG_A4_Norm.Derivation,from:char,to:char)
  requires RulesR11(r,s,d)
  ensures RulesR11(RenamePatternR11(r,from,to),RenameWordR11(s,from,to),d)
  decreases d
 { assume false; }
}
