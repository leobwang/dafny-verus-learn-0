from pathlib import Path
import json,sys,hashlib,importlib.util
root=Path.cwd();sys.path[:0]=[str(root/'tests/wrappers'),str(root/'harness'),str(root/'harness/r')]
import test_tools_common as C
from fvh_r.engine import source_task,Hint,check_source_frame
c=C.load_script('vcheck')
spec=importlib.util.spec_from_file_location('r12_form_checks',root/'tools/R12/admit_forms.py');forms=importlib.util.module_from_spec(spec);spec.loader.exec_module(forms)
b=Path('/tmp/dvl0-dvr2-r12/lab-prototypes');out=b/'admission';out.mkdir(exist_ok=True)
keys=['baseline-proof-fails','max-auto-empty-fails','reference-gate','reference-three-seeds','wrong-hints-fail','audit-clean','original-model-code-frame']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for task in json.loads((b/'index.json').read_text()):
 p=Path(task['form']);good=Path(task['good']);lang=task['lang'];lib=c.D if lang=='d' else c.V;native='dafny' if lang=='d' else 'verus';directory=out/task['id'];directory.mkdir(exist_ok=True)
 statefile=directory/'report.json';report=json.loads(statefile.read_text()) if statefile.exists() else {'id':task['id'],'source_sha256':sha(p),'reference_source_sha256':sha(good),'status':'authoring','checks':{k:False for k in keys},'evidence':{}}
 assert report['source_sha256']==sha(p) and report['reference_source_sha256']==sha(good),'admission input changed: do not reuse controls'
 def save():statefile.write_text(json.dumps(report,indent=2)+'\n')
 def checked(name,document):
  report['evidence'][name]=document;save()
  if document.get('passed') is not True:print(task['id'],name,'FAILED',flush=True);raise SystemExit(1)
 if not report['checks']['baseline-proof-fails'] or not report['checks']['reference-gate']:
  for kind,want in [('form','failed'),('good','verified')]:
   r=json.loads((b/(task['id']+'-'+kind+'.json')).read_text());captured=next(x for x in json.loads((b/'results.json').read_text()) if x['id']==task['id'] and x['case']==kind)
   assert captured['source_sha256']==sha(Path(task[kind])) and captured['passed']
   matches=[v for k,v in r['per_symbol'].items() if k==('R12_LabCase.LabTask' if lang=='d' else 'lab_task')]
   ok=r['verdict']==want and r['stage']=='verify' and not r['holes'] and (kind!='good' or matches==['verified'])
   checked(kind+'-gate',dict(passed=ok,document=r));report['checks']['baseline-proof-fails' if kind=='form' else 'reference-gate']=True;save()
 if not report['checks']['original-model-code-frame']:
  text=p.read_text();complete=good.read_text();t,spans=source_task(text);check_source_frame(t,complete)
  entry=forms.analyze_form(p,c,source_task)
  table=c.statement_table(p,lang,text=text)[0];skeleton=c.LC.skeleton(text,native,annotations=True,target='unused',witness='unused')
  assert table==c.statement_table(p,lang,text=complete)[0]
  assert skeleton==c.LC.skeleton(complete,native,annotations=True,target='unused',witness='unused')
  # Validate author-owned source spans against the actual native declaration.
  src=c.D.parse_source(text,str(p)) if lang=='d' else c.V.vs.parse(text)
  target=src.decl('R12_LabCase.LabTask') if lang=='d' else next(d for d in src.walk() if d.kind=='fn' and d.name=='lab_task')
  if lang=='d':start=target.line
  else:
   token=next(k for k in range(target.start,target.body[0]) if src.toks[k].text=='fn');start=text[:src.toks[token].start].count('\n')+1
  end=text[:src.toks[target.body[1]].start].count('\n')+1
  assert len(spans)==1 and spans[0]['start']==start and spans[0]['end']==end,(spans,start,end)
  checked('frame',dict(passed=True,native_form=entry,validated_span=spans[0]));report['checks']['original-model-code-frame']=True;save()
 if not report['checks']['audit-clean']:
  findings=lib.audit(str(good));checked('audit',dict(passed=not findings,findings=[f.to_dict() for f in findings]));report['checks']['audit-clean']=True;save()
 if not report['checks']['max-auto-empty-fails']:
  symbol='R12_LabCase.LabTask' if lang=='d' else 'lab_task'
  if lang=='d':r=lib.empty_body(str(good),symbol)
  else:
   header=good.read_text().split('fn lab_task',1)[1].split('{',1)[0]
   triv='{ Vec::new() }' if 'out:Vec<bool>' in header else '{ false }' if 'answer:bool' in header else '{ 0 }'
   r=lib.empty_body(str(good),symbol,modes=['E0','E0H','E1','E2','EM','INV','TRIV'],seeds=[1,2,3],triv_body=triv)
  statuses=list(r.per_symbol.values());ok=r.verdict=='failed' and bool(statuses) and all(v=='failed' or v.startswith('fails(') for v in statuses)
  checked('empty-automation',dict(passed=ok,document=r.to_dict()));report['checks']['max-auto-empty-fails']=True;save()
 if not report['checks']['reference-three-seeds']:
  for seed in [1,2,3]:
   name='seed-'+str(seed)
   if report['evidence'].get(name,{}).get('passed'):continue
   r=lib.verify(str(good),seed=seed);checked(name,dict(passed=r.verdict=='verified' and r.stage=='verify' and not r.holes,document=r.to_dict()))
  report['checks']['reference-three-seeds']=True;save()
 if not report['checks']['wrong-hints-fail']:
  text=p.read_text();t,_=source_task(text)
  for site in t.sites:text=text.replace(site.marker,'false',1)
  wrong=directory/('wrong'+p.suffix);wrong.write_text(text);r=lib.verify(str(wrong),gate=True)
  checked('wrong-hints',dict(passed=r.verdict=='failed' and r.stage=='verify' and not r.holes,document=r.to_dict()));report['checks']['wrong-hints-fail']=True;save()
 assert all(report['checks'].values())
 assert report['source_sha256']==sha(p) and report['reference_source_sha256']==sha(good)
 report['status']='admitted';save();rows.append(dict(id=task['id'],status=report['status'],source_sha256=report['source_sha256']));(out/'index.json').write_text(json.dumps(rows,indent=2)+'\n');print(task['id']+': admitted ('+str(len(rows))+'/40)',flush=True)
