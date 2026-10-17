// Reference Solution.
/* CONTRACT — R09 refactorer/port, R-v0
goal: preserve the complete Dafny escaped-atom cursor behavior while porting the Verus body
allowed-files:
  - dafny/R/R09_Effects/agent/R09_AgentRefactor.dfy
acceptance:
  - snapshot the original source, model, mirror and effects statement before editing
  - preserve all signatures, models, preconditions, postconditions, imports and error positions; body edits only
  - after every edit run scripts/vcheck dafny/R/R09_Effects/agent/R09_AgentRefactor.dfy and retain the native stage, holes and diagnostics
  - scripts/vcheck --gate dafny/R/R09_Effects/agent/R09_AgentRefactor.dfy exits0 with zero tool-counted holes and scripts/vaudit has no findings
  - scripts/specfreeze --against <snapshot> dafny/R/R09_Effects/agent/R09_AgentRefactor.dfy preserves the original model and statement
  - run the supplied fixed scalar-position differential harness; retain failed attempts and exact accept/error/mutation observations
  - separate mirror-relative implications, finite compiled agreement and a full grammar theorem in the report
  - retain costs, original exposure and the deferred D45 live-actor outcome; native author controls are not actor passes
*/
module R09_AgentRefactor {
 import opened RG_A3_Syntax
 class EscapedCursorR09 {
  var input:seq<char>
  var position:nat
  constructor(s:seq<char>,at:nat)
   requires at<=|s|
   ensures input==s && position==at
  {input:=s;position:=at;}
 }
 ghost function EscapedModelR09(s:seq<char>,at:nat):Res<(char,nat)>
  requires at<|s| && s[at]=='\\'
 {if at+1==|s| then Err(at+1,"escaped end") else Ok((s[at+1],at+2))}
 // Independent transcription; this equality is only relative to the mirror.
 ghost function EscapedMirrorR09(s:seq<char>,at:nat):Res<(char,nat)>
  requires at<|s| && s[at]=='\\'
 {if at+1<|s| then Ok((s[at+1],at+2)) else Err(|s|,"escaped end")}
 lemma {:induction false} MirrorImplicationR09(s:seq<char>,at:nat)
  requires at<|s| && s[at]=='\\'
  ensures EscapedModelR09(s,at)==EscapedMirrorR09(s,at)
 {if at+1==|s| {} else {}}
 // item: R09.A1d
 method EscapedAtomR09(cur:EscapedCursorR09) returns (out:Res<char>)
  requires cur.position<|cur.input| && cur.input[cur.position]=='\\'
  modifies cur
  ensures cur.input==old(cur.input)
  ensures out.Ok? ==> EscapedModelR09(old(cur.input),old(cur.position))==Ok((out.value,cur.position))
  ensures out.Err? ==> EscapedModelR09(old(cur.input),old(cur.position))==Err(out.pos,out.msg) && cur.position==old(cur.position)
 {
  var start:=cur.position;
  if start+1==|cur.input| {out:=Err(start+1,"escaped end");}
  else {var c:=cur.input[start+1];cur.position:=start+2;out:=Ok(c);}
 }
}
