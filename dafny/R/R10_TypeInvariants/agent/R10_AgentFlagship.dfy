/*! R10 flagship: human statement design, then contractor proof bodies.
Before actor work, write original-domain contracts for all three constructors,
record nonvacuous input/output examples, and snapshot those statements.
The provided output type promises normal shape. Design and justify the
additional language promise yourself. The actor may edit only bodies and
reference-only helpers in its delivery; it must preserve your snapshot.
*/
module R10_AgentFlagship {
 import opened RG_A1_Re
 import opened RG_A1b_Facts
 import opened RG_A4_Norm
 
 
 
 
 // item: R10.A1d
 method BuildAltR10(a:NormRe,b:NormRe) returns (out:NormRe)
  { assume false; }
 method BuildCatR10(a:NormRe,b:NormRe) returns (out:NormRe)
  { assume false; }
 method BuildStarR10(a:NormRe) returns (out:NormRe)
  { assume false; }
}
