/* CONTRACT — R09 refactorer/port, R-v0
goal: preserve the complete Dafny escaped-atom cursor behavior while porting the Verus body
allowed-files:
  - verus/r/r09_effects/src/agent.rs
acceptance:
  - snapshot the original source, model, mirror and effects statement before editing
  - preserve all signatures, models, preconditions, postconditions, imports and error positions; body edits only
  - after every edit run scripts/vcheck verus/r/r09_effects/src/agent.rs and retain the native stage, holes and diagnostics
  - scripts/vcheck --gate verus/r/r09_effects/src/agent.rs exits 0 with zero tool-counted holes and scripts/vaudit has no findings
  - scripts/specfreeze --against <snapshot> verus/r/r09_effects/src/agent.rs preserves the original model and statement
  - run the supplied fixed scalar-position differential harness; retain failed attempts and exact accept/error/mutation observations
  - separate mirror-relative implications, finite compiled agreement and a full grammar theorem in the report
  - retain costs, original exposure and the deferred D45 live-actor outcome; native author controls are not actor passes
*/
use vstd::prelude::*;
use rg_re_a3::*;

verus! {

pub struct EscapedCursorR09 {
    pub input: Vec<char>,
    pub position: usize,
}

pub open spec fn escaped_model_r09(s: Seq<char>, at: int) -> Result<(char, usize), PErr>
    recommends
        0 <= at < s.len() && s[at] == '\\',
{
    if at + 1 == s.len() {
        Err(PErr { pos: (at + 1) as usize, kind: ErrKind::UnexpectedEnd })
    } else {
        Ok((s[at + 1], (at + 2) as usize))
    }
}

// Independent transcription; equality establishes only agreement with this mirror.
pub open spec fn escaped_mirror_r09(s: Seq<char>, at: int) -> Result<(char, usize), PErr>
    recommends
        0 <= at < s.len() && s[at] == '\\',
{
    if at + 1 < s.len() {
        Ok((s[at + 1], (at + 2) as usize))
    } else {
        Err(PErr { pos: s.len() as usize, kind: ErrKind::UnexpectedEnd })
    }
}

proof fn mirror_implication_r09(s: Seq<char>, at: int)
    requires
        0 <= at < s.len() && s[at] == '\\',
    ensures
        escaped_model_r09(s, at) == escaped_mirror_r09(s, at),
{
    if at + 1 == s.len() {
    } else {
    }
}

// item: R09.A1v
#[verifier::external_body]
fn escaped_atom_r09(cur: &mut EscapedCursorR09) -> (out: Result<char, PErr>)
    requires
        old(cur).position < old(cur).input.len(),
        old(cur).input@[old(cur).position as int] == '\\',
    ensures
        final(cur).input@ == old(cur).input@,
        match out {
            Ok(c) => escaped_model_r09(old(cur).input@, old(cur).position as int) == Ok::<(char, usize), PErr>((c, final(cur).position)),
            Err(e) => escaped_model_r09(old(cur).input@, old(cur).position as int) == Err::<(char, usize), PErr>(e) && final(cur).position == old(cur).position,
        },
{
    unimplemented!()
}

} // verus!
