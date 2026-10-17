from pathlib import Path
import sys,json,hashlib
root=Path.cwd();sys.path.insert(0,str(root/'tests/wrappers'));import test_tools_common as C
c=C.load_script('vcheck');b=Path('/tmp/dvl0-dvr2-r12/lab-prototypes');rows=[]
cache={(r['id'],r['case']):r for r in json.loads((b/'success-cache.json').read_text())}
for task in json.loads((b/'index.json').read_text()):
 lib=c.D if task['lang']=='d' else c.V
 for case,want in [('good','verified'),('form','failed')]:
  sha=hashlib.sha256(Path(task[case]).read_bytes()).hexdigest();old=cache.get((task['id'],case))
  if old and old['source_sha256']==sha:rows.append(old);continue
  r=lib.verify(task[case],gate=True);ok=r.verdict==want and r.stage=='verify' and not r.holes
  (b/(task['id']+'-'+case+'.json')).write_text(json.dumps(r.to_dict(),indent=2)+'\n');row=dict(id=task['id'],case=case,verdict=r.verdict,stage=r.stage,passed=ok,source_sha256=sha);rows.append(row)
  (b/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(row,flush=True)
  if ok:cache[(task['id'],case)]=row;(b/'success-cache.json').write_text(json.dumps(list(cache.values()),indent=2)+'\n')
  else:
   for d in r.diagnostics:
    if d.severity=='error':print(d.line,d.message,flush=True)
   raise SystemExit(1)
(b/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('Native proof/baseline controls:',len(rows),'passed',flush=True)
