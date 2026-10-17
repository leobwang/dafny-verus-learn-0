use vstd::prelude::*;
verus! {
pub struct ArenaNodeR11 {pub label:char,pub first:Option<usize>,pub second:Option<usize>}
pub struct ArenaR11 {pub nodes:Vec<ArenaNodeR11>}
pub open spec fn targets_valid_r11(node:ArenaNodeR11,len:int)->bool {
 (match node.first {Some(k)=>k<len,None=>true}) && (match node.second {Some(k)=>k<len,None=>true})
}
pub open spec fn arena_valid_r11(arena:ArenaR11)->bool {
 forall|i:int| 0<=i<arena.nodes@.len() ==> targets_valid_r11(#[trigger] arena.nodes@[i],arena.nodes@.len() as int)
}
proof fn targets_monotone_r11(node:ArenaNodeR11,old_len:int,new_len:int)
 requires targets_valid_r11(node,old_len),old_len<=new_len,
 ensures targets_valid_r11(node,new_len),
 {}
fn empty_arena_r11()->(out:ArenaR11)
 ensures arena_valid_r11(out),out.nodes@.len()==0,
 {ArenaR11{nodes:Vec::new()}}
fn append_node_r11(arena:&mut ArenaR11,label:char)->(index:usize)
 requires arena_valid_r11(*old(arena)),old(arena).nodes.len()<usize::MAX,
 ensures arena_valid_r11(*final(arena)),
 final(arena).nodes@.len()==old(arena).nodes@.len()+1,
 final(arena).nodes@.take(old(arena).nodes@.len() as int)==old(arena).nodes@,
 index==old(arena).nodes@.len(),
 final(arena).nodes@[index as int].label==label,
 final(arena).nodes@[index as int].first is None,final(arena).nodes@[index as int].second is None,
{
 let ghost before=arena.nodes@;let index=arena.nodes.len();
 arena.nodes.push(ArenaNodeR11{label,first:None,second:None});
 proof {
  assert(arena.nodes@.take(before.len() as int)=~=before);
  assert forall|i:int| 0<=i<arena.nodes@.len() implies targets_valid_r11(#[trigger] arena.nodes@[i],arena.nodes@.len() as int) by {
   if i<index {targets_monotone_r11(before[i],before.len() as int,arena.nodes@.len() as int);}
  }
 }
 index
}
fn link_first_r11(arena:&mut ArenaR11,index:usize,target:usize)
 requires arena_valid_r11(*old(arena)),index<old(arena).nodes.len(),target<old(arena).nodes.len(),
 ensures arena_valid_r11(*final(arena)),final(arena).nodes@.len()==old(arena).nodes@.len(),
 final(arena).nodes@[index as int].label==old(arena).nodes@[index as int].label,
 final(arena).nodes@[index as int].first==Some(target),
 final(arena).nodes@[index as int].second==old(arena).nodes@[index as int].second,
 forall|j:int| 0<=j<old(arena).nodes@.len() && j!=index ==> final(arena).nodes@[j]==old(arena).nodes@[j],
{
 let ghost before=arena.nodes@;
 let label=arena.nodes[index].label;let second=arena.nodes[index].second;
 arena.nodes.set(index,ArenaNodeR11{label,first:Some(target),second});
 proof {
  assert forall|j:int| 0<=j<arena.nodes@.len() implies targets_valid_r11(#[trigger] arena.nodes@[j],arena.nodes@.len() as int) by {
   if j==index {} else {assert(arena.nodes@[j]==before[j]);}
  }
 }
}
}
