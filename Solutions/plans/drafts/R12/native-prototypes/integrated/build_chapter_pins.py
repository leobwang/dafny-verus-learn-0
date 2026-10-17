from pathlib import Path
import json
entries=[]
def add(name,cmd,*,answers=(),scratch=None):
 e={'id':name,'cmd':cmd}
 if answers:e['answers']=list(answers)
 if scratch:e.update(cwd='scratch',inputs=['dafny/options/std.toml'] if next(iter(scratch)).endswith('.dfy') else [],scratch=scratch)
 entries.append(e)
for lang in 'dv':
 for mode in ['fast','full']:
  opts=['--symbol','R12_SelectionProbe.GoodR12' if lang=='d' else 'good_r12'] if mode=='fast' else []
  if lang=='d':add('selection-d-'+mode,['scripts/vcheck','--module','R12',*opts,'selection-d.dfy'],answers=['R12.P3dv'],scratch={'selection-d.dfy':{'copy':'specimens/R12/selection-d.dfy.specimen'}})
  else:add('selection-v-'+mode,['scripts/vcheck',*opts,'specimens/R12/selection-v.rs.specimen'],answers=['R12.P3dv'])
for lang,path in [('d','dafny/R/R12_Driving/std'),('v','verus/r/r12_driving')]:add('shipped-'+lang,['scripts/vcheck',path])
source=Path('dafny/checks/R12_checks.dfy').read_text().replace('// SLOT: expect line == ???;','expect line == 15;')
add('span-value',['scripts/vcheck','--module','R12','--test','span-value.dfy'],answers=['R12.P1d'],scratch={'span-value.dfy':{'text':source}})
source=Path('specimens/R12/P2v.rs.specimen').read_text().replace('// SLOT: assert(proof_fields_r12(ProbePhaseR12::Compilation,7,0)==???) by (compute_only);','assert(proof_fields_r12(ProbePhaseR12::Compilation,7,0)==false) by (compute_only);')
add('phase-value',['scripts/vcheck','--module','R12','phase-value.rs'],answers=['R12.P2v'],scratch={'phase-value.rs':{'text':source}})
add('count-labels',['scripts/vcheck','specimens/R12/P4v.rs.specimen'],answers=['R12.P4v'])
add('shipped-python',['scripts/vcheck','harness/r/fvh_r/engine.py'])
for lang in 'dv':
 for name in ['fields','bound']:
  if lang=='d':add(name+'-'+lang,['scripts/vcheck','--module','R12',name+'-d.dfy'],answers=['R12.P5dv'],scratch={name+'-d.dfy':{'copy':'specimens/R12/'+name+'-d.dfy.specimen'}})
  else:add(name+'-'+lang,['scripts/vcheck','specimens/R12/'+name+'-v.rs.specimen'],answers=['R12.P5dv'])
s='# R12 chapter native captures; generated metadata is written by scripts/pins.py.\nschema = 1\n'
for e in entries:
 s+='\n[[entry]]\n'
 for key,value in e.items():
  if key!='scratch':s+=key+' = '+json.dumps(value,ensure_ascii=False)+'\n'
 s+='[entry.normalize]\ndrop = ["^raw output: "]\n'
 for name,source in e.get('scratch',{}).items():
  s+='[entry.scratch.'+json.dumps(name)+']\n'
  for k,v in source.items():s+=k+' = '+json.dumps(v,ensure_ascii=False)+'\n'
Path('expected/R12.chapter.toml').write_text(s)
