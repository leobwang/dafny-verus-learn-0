from pathlib import Path
import sys,json,tomllib,hashlib
root=Path.cwd();sys.path.insert(0,str(root/'tests/wrappers'));import test_tools_common as C
c=C.load_script('vcheck');out=Path('/tmp/dvl0-dvr2-r12/corpus-witnesses');out.mkdir(exist_ok=True);rows=[]
# Mathematical expected observations independent of the supplied implementations.
observations={
 'accepted-ledger':('[true,false,true]','vec![true,false,true]',2),
 'first-rejection':('[true,true,false,true]','vec![true,true,false,true]',2),
 'last-acceptance':('[false,true,false]','vec![false,true,false]',2),
 'exhaust-credit':('3','3',3),'double-progress':('3','3',6),
 'all-accepted':('[true,true]','vec![true,true]',True),'any-accepted':('[false,true]','vec![false,true]',True),
 'copy-ledger':('[true,false]','vec![true,false]',[True,False]),
 'reverse-ledger':('[true,false,false]','vec![true,false,false]',[False,False,True]),
 'negate-ledger':('[true,false]','vec![true,false]',[False,True]),
 'concat-ledgers':('[true],[false,true]',('vec![true]','vec![false,true]'),[True,False,True]),
 'rotate-ledger':('[true,false,false]','vec![true,false,false]',[False,False,True]),
 'sum-prefix-indices':('4','4',6),'sum-prefix-odds':('4','4',16),'repeat-increment':('3,4','3,4',12),
 'quotient-three':('8','8',2),'remainder-three':('8','8',2),
 'first-mismatch':('[true,false],[true,true]',('vec![true,false]','vec![true,true]'),1),
 'minimum-value':('[5,2,9]','vec![5usize,2usize,9usize]',2),'maximum-value':('[5,2,9]','vec![5usize,2usize,9usize]',9)}
cards=tomllib.loads((root/'bench/local/r/labalpha/STRATUM.toml').read_text())['card']
for card in cards:
 case=card['cluster'];dargs,vargs,value=observations[case];directory=out/card['id'];directory.mkdir(exist_ok=True)
 code=(root/'Solutions'/card['path']).read_text();expected=str(value).lower();lang=card['lang'];reference_hash=hashlib.sha256(code.encode()).hexdigest()
 if lang=='dafny':
  source=directory/'witness.dfy';source.write_text(code+'\nmodule R12_CorpusObservation {import P=R12_LabCase\n @Test method OriginalDomain() {var actual:=P.LabTask('+dargs+');expect actual=='+expected+';}\n}\n');target=source;lib=c.D
 else:
  if isinstance(vargs,tuple):setup='let left='+vargs[0]+';let right='+vargs[1]+';';args='&left,&right'
  elif vargs.startswith('vec!'):setup='let values='+vargs+';';args='&values'
  else:setup='';args=vargs
  ty='Vec<bool>' if isinstance(value,list) else 'bool' if type(value)is bool else 'usize'
  literal='vec!'+expected if isinstance(value,list) else expected
  code+='\nverus! {fn original_domain_witness()->'+ty+' {'+setup+'lab_task('+args+')}}\n'
  code+='#[cfg(test)]mod r12_observe {use super::*;#[test]fn original_domain(){assert_eq!(original_domain_witness(),'+literal+');}}\n'
  target=directory/'crate';(target/'src').mkdir(parents=True,exist_ok=True);(target/'src/lib.rs').write_text(code)
  (target/'Cargo.toml').write_text('[package]\nname="r12_corpus_witness"\nversion="0.1.0"\nedition="2021"\nbuild=false\n[dependencies]\nvstd="=0.0.0-2026-09-20-0158"\n[package.metadata.verus]\nverify=true\n[workspace]\n');source=target/'src/lib.rs';lib=c.V
 report={'id':card['id'],'scope':'one original-domain actual-source compiled observation; not a live model result','reference_source_sha256':reference_hash,'observation_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'expected':value}
 gate=lib.verify(str(target),gate=True);report['gate']=gate.to_dict();ok=gate.verdict=='verified' and not gate.holes
 if ok:
  tested=lib.test(str(target));report['test']=tested.to_dict();ok=tested.verdict=='verified' and tested.stage=='test' and not tested.holes and len(tested.per_symbol)==1 and all(v=='passed' for v in tested.per_symbol.values())
 report['passed']=ok;(directory/'report.json').write_text(json.dumps(report,indent=2)+'\n');rows.append({'id':card['id'],'passed':ok});(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(card['id'],ok,flush=True)
 if not ok:
  print(json.dumps(report,indent=2),flush=True);raise SystemExit(1)
assert len(rows)==40
print('40/40actual-source original-domain compiled observations passed.',flush=True)
