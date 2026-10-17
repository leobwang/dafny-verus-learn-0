// item: R13.P3dv verdict
// Predict exact proof verdict/stage in each language.
// SLOT: CHECK P3dv
// item: R13.P6dv verdict
// Selected then full scope, exact D/V verdict and stage pairs.
// SLOT: CHECK P6dv
/*! R13 — Pipelines and trust. Four counted holes per language.
T1 is closed book. Repair H1–H3 without changing their original domains or
statements. Attribute the original failure, record two instruments, and keep
mathematical correctness separate from native pipeline and runtime evidence.
A model-level proof does not verify a wrapper, compiler, solver or agent.
*/
module R13_Repairs {
 import opened RG_A1_Re
 // specfreeze: frozen-imports
 // item: R13.T1d
 // pair: R13.T1v
 method ClampIndexR13(i:nat,bound:nat) returns(at:nat)
  requires bound>0
  ensures at<bound && at==(if i<bound then i else bound-1)
 {assume false;}
 // item: R13.H1d
 // pair: R13.H1v
 method SaturatingSumR13(a:nat,b:nat) returns(out:nat)
  requires a<=18446744073709551615 && b<=18446744073709551615
  ensures out==(if a+b<=18446744073709551615 then a+b else 18446744073709551615)
 {assume false;}
 // item: R13.H2d
 // pair: R13.H2v
 method RangeFitsR13(pos:nat,need:nat,limit:nat) returns(fits:bool)
  ensures fits <==> pos+need<=limit
 {assume false;}
 // item: R13.H3d
 // pair: R13.H3v
 method PairWitnessR13(c:char,d:char) returns(s:seq<char>)
  ensures |s|==2 && Matches(Cat(Chr(c),Chr(d)),s)
 {assume false;}
}
