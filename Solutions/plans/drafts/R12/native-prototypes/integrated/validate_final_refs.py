from pathlib import Path
import subprocess,json
out=Path('/tmp/dvl0-dvr2-r12/final-references');out.mkdir(exist_ok=True);rows=[]
paths=['Solutions/dafny/R/R12_Driving/std/R12_Driving.dfy','Solutions/verus/r/r12_driving/src/lib.rs']
commands=[]
for i,path in enumerate(paths):
 commands.append((f'seeds-{i}',['scripts/vcheck','--ref','--brittleness','--json',path],'seeds'))
for i,path in enumerate(paths+['Solutions/harness/r/fvh_r/engine.py','Solutions/harness/r/fvh_r/environment.py','Solutions/harness/r/fvh_r/extractor.py','Solutions/harness/r/fvh_r/loop.py']):commands.append((f'audit-{i}',['scripts/vaudit','--ref','--json',path],'audit'))
for name,argv,kind in commands:
 p=subprocess.run(argv,text=True,capture_output=True);(out/(name+'.stdout')).write_text(p.stdout);(out/(name+'.stderr')).write_text(p.stderr)
 d=json.loads(p.stdout);ok=p.returncode==0 and ((d['stable'] and d['seeds']==[1,2,3] and all(x=='verified' for x in d['verdicts'].values())) if kind=='seeds' else not d['findings'])
 rows.append(dict(name=name,exit=p.returncode,passed=ok,document=d));(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,ok,flush=True)
 if not ok:raise SystemExit(1)
