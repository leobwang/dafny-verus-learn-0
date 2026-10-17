use vstd::prelude::*;
use rg_re_a3::*;
use parser_canonical::{parse_counted,counted_node};
verus! {
pub struct EffectCursorR09 {pub text:Vec<char>,pub position:usize}
fn read_bound_r09(c:char,pos:usize,len:usize)->(res:Result<u32,PErr>)
 requires pos<=len,
 ensures match res {Ok(n)=>is_bound_char(c) && n==bound_value(c),Err(e)=>!is_bound_char(c) && e.pos==pos},
{
 if c<'0' || c>'9' {Err(PErr {pos,kind:ErrKind::UnexpectedChar})}
 else {Ok((c as u32)-('0' as u32))}
}
fn read_bound_cursor_r09(cur:&mut EffectCursorR09)->(res:Result<u32,PErr>)
 requires old(cur).position<old(cur).text.len(),
 ensures final(cur).text@==old(cur).text@,
 final(cur).position==old(cur).position+1,
 match res {
  Ok(n)=>is_bound_char(old(cur).text@[old(cur).position as int]) && n==bound_value(old(cur).text@[old(cur).position as int]),
  Err(e)=>!is_bound_char(old(cur).text@[old(cur).position as int]) && e.pos==old(cur).position,
 },
{
 let start=cur.position;let c=cur.text[start];let len=cur.text.len();
 cur.position=start+1;
 let n=read_bound_r09(c,start,len)?;
 Ok(n)
}
fn counted_cursor_r09(cur:&mut EffectCursorR09,x:Syn)->(res:Result<Syn,PErr>)
 requires old(cur).position<old(cur).text.len(),old(cur).text@[old(cur).position as int]=='{',
 wf(x,old(cur).text.len() as nat),x.span.hi==old(cur).position,x.span.lo<old(cur).position,
 ensures final(cur).text@==old(cur).text@,
 old(cur).position<=final(cur).position<=final(cur).text.len(),
 match res {
  Ok(y)=>wf(y,final(cur).text.len() as nat) && y.span.lo==x.span.lo && y.span.hi==final(cur).position && old(cur).position<final(cur).position,
  Err(e)=>final(cur).position==old(cur).position && e.pos<=final(cur).text.len(),
 },
 forall|n:nat,m:nat,k:int| #[trigger] counted_at(old(cur).text@,old(cur).position as int,n,m,k) ==> res==Ok::<Syn,PErr>(counted_node(x,n,m,k)) && final(cur).position==k,
{
 let start=cur.position;
 let (y,k)=parse_counted(&cur.text,start,x)?;
 cur.position=k;
 Ok(y)
}
}
