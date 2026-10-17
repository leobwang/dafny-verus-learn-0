verus! {
fn frontend_r09(s:&Vec<char>,cap:u32)->(res:Result<(Syn,Re),PErr>)
 ensures match res {
  Ok((tree,lowered)) => wf(tree,s.len() as nat) && tree.span.lo==0 && tree.span.hi==s.len()
    && lowered==lower(tree) && node_count(lowered)<=cap,
  Err(e) => e.pos<=s.len(),
 },
 no_special_from(s@,0) && (if s.len()==0 {1int} else {2*s.len()-1})<=cap ==>
   res is Ok && matches(res->Ok_0.1,s@),
{
 let tree=parse(s)?;
 match checked_lowering_cost_r09(&tree,s.len(),cap) {
  None=>Err(PErr {pos:0,kind:ErrKind::ExpansionBudget}),
  Some(_)=>{
   let lowered=lowering_exec_r09(&tree,s.len());
   proof {lemma_lowering_nodes_r09(tree,s.len() as nat);}
   Ok((tree,lowered))
  },
 }
}
}
