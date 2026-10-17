from pathlib import Path
import sys,json
r=Path.cwd();b=Path('/tmp/dvl0-dvr3-r14');sys.path.insert(0,str(r/'tests/wrappers'));import test_tools_common as C
c=C.load_script('vcheck');res=c.V.verify(str(b/'trigger-probe.rs'),extra_args=['--triggers-mode','verbose']);d=res.to_dict();(b/'trigger-report-v.json').write_text(json.dumps(d,indent=2)+'\n');print(d['verdict'],d['stage'],d['verified_count'],'raw',d['raw_dir'],flush=True)
for x in d['diagnostics']:print(x['severity'],x['line'],x['message'][:500],flush=True)
assert d['verdict']=='failed' and d['stage']=='verify' and not d['holes']
print('log refusal',c.V.check_args(['--log','smt']),flush=True)
