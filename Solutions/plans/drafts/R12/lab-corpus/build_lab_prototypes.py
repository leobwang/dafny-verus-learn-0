from pathlib import Path
import json,re,sys
ROOT=Path.cwd();B=Path('/tmp/dvl0-dvr2-r12/lab-prototypes');B.mkdir(exist_ok=True)
sys.path[:0]=[str(ROOT/'harness'),str(ROOT/'harness/r')]
from fvh_r.engine import source_task,HintSite,HintTask,Hint,check_source_frame
# Templates and correct hints are author-only construction data; no learner card
# or native proof result is manufactured by this generator.
TASKS=[]
def task(name,description,dhead,vhead,dbody,vbody,dinv,vinv,dh='',vh=''):
 TASKS.append(dict(name=name,statement=description,dhead=dhead,vhead=vhead,dbody=dbody,vbody=vbody,dinv=dinv,vinv=vinv,dh=dh,vh=vh))
DH='''ghost function LedgerCount(flags:seq<bool>):nat decreases |flags|
 {if flags==[] then 0 else LedgerCount(flags[..|flags|-1])+(if flags[|flags|-1] then 1 else 0)}
 lemma LedgerStep(flags:seq<bool>,i:nat)
 requires i<|flags|
 ensures LedgerCount(flags[..i+1])==LedgerCount(flags[..i])+(if flags[i] then 1 else 0)
 {assert flags[..i+1][..i]==flags[..i];}
'''
VH='''pub open spec fn ledger_count(flags:Seq<bool>)->nat decreases flags.len(),
 {if flags.len()==0 {0} else {ledger_count(flags.take(flags.len() as int-1))+(if flags[flags.len() as int-1] {1nat} else {0nat})}}
 proof fn ledger_step(flags:Seq<bool>,i:int)
 requires 0<=i<flags.len(),
 ensures ledger_count(flags.take(i+1))==ledger_count(flags.take(i))+(if flags[i] {1nat} else {0nat}),
 {assert(flags.take(i+1).take(i)=~=flags.take(i));}
'''
task('accepted-ledger','Count every true flag in the original ordered ledger; preserve the provided code and count model.',
 'method LabTask(flags:seq<bool>) returns(accepted:nat) ensures accepted==LedgerCount(flags) && accepted<=|flags|',
 'fn lab_task(flags:&Vec<bool>)->(accepted:usize) ensures accepted==ledger_count(flags@),accepted<=flags.len(),',
 '''var i:=0;accepted:=0;
 while i<|flags|
 invariant @SITE@
 {LedgerStep(flags,i);if flags[i] {accepted:=accepted+1;} i:=i+1;}
 assert flags[..i]==flags;''',
 '''let mut i:usize=0;let mut accepted:usize=0;
 while i<flags.len()
 invariant @SITE@
 decreases flags.len()-i,
 {proof {ledger_step(flags@,i as int);}if flags[i] {accepted=accepted+1;}i=i+1;}
 proof {assert(flags@.take(i as int)=~=flags@);}
 accepted''',
 ['0<=i<=|flags| && accepted<=i && accepted==LedgerCount(flags[..i])'],
 ['i<=flags.len() && accepted<=i && accepted==ledger_count(flags@.take(i as int))'],DH,VH)
task('first-rejection','Return the first false flag, or the original length when every flag is true.',
 'method LabTask(flags:seq<bool>) returns(at:nat) ensures at<=|flags| ensures forall j:nat :: j<at ==> flags[j] ensures at==|flags| || !flags[at]',
 'fn lab_task(flags:&Vec<bool>)->(at:usize) ensures at<=flags.len(),forall|j:int|0<=j<at ==> flags@[j],at==flags.len() || !flags@[at as int],',
 '''at:=0;while at<|flags| && flags[at]
 invariant @SITE@
 {at:=at+1;}''',
 '''let mut at:usize=0;while at<flags.len() && flags[at]
 invariant @SITE@
 decreases flags.len()-at,
 {at=at+1;}at''',
 ['0<=at<=|flags| && (forall j:nat :: j<at ==> flags[j])'],
 ['at<=flags.len() && (forall|j:int|0<=j<at ==> flags@[j])'])
task('last-acceptance','Return one plus the last true index, or0if none; every flag after the returned prefix must be false.',
 'method LabTask(flags:seq<bool>) returns(last:nat) ensures last<=|flags| ensures last>0 ==> flags[last-1] ensures forall j:nat :: last<=j<|flags| ==> !flags[j]',
 'fn lab_task(flags:&Vec<bool>)->(last:usize) ensures last<=flags.len(),last>0 ==> flags@[(last as int)-1],forall|j:int|last<=j<flags.len() ==> !flags@[j],',
 '''var i:=0;last:=0;while i<|flags|
 invariant @SITE@
 {if flags[i] {last:=i+1;}i:=i+1;}''',
 '''let mut i:usize=0;let mut last:usize=0;while i<flags.len()
 invariant @SITE@
 decreases flags.len()-i,
 {if flags[i] {last=i+1;}i=i+1;}last''',
 ['0<=last<=i<=|flags| && (last>0 ==> flags[last-1]) && (forall j:nat :: last<=j<i ==> !flags[j])'],
 ['last<=i && i<=flags.len() && (last>0 ==> flags@[(last as int)-1]) && (forall|j:int|last<=j<i ==> !flags@[j])'])
task('exhaust-credit','Consume one credit per iteration and return the exact number consumed without changing the original limit.',
 'method LabTask(limit:nat) returns(spent:nat) ensures spent==limit',
 'fn lab_task(limit:usize)->(spent:usize) ensures spent==limit,',
 '''spent:=0;var remaining:=limit;while remaining>0
 invariant @SITE@
 decreases remaining
 {remaining:=remaining-1;spent:=spent+1;}''',
 '''let mut spent:usize=0;let mut remaining:usize=limit;while remaining>0
 invariant @SITE@
 decreases remaining,
 {remaining=remaining-1;spent=spent+1;}spent''',
 ['spent+remaining==limit'],['spent+remaining==limit'])
task('double-progress','Advance a counter and its doubled output together under the original n<=1000 domain.',
 'method LabTask(n:nat) returns(out:nat) requires n<=1000 ensures out==2*n',
 'fn lab_task(n:usize)->(out:usize) requires n<=1000, ensures out==2*n,',
 '''var i:=0;out:=0;while i<n
 invariant @SITE@
 {out:=out+2;i:=i+1;}''',
 '''let mut i:usize=0;let mut out:usize=0;while i<n
 invariant @SITE@
 decreases n-i,
 {out=out+2;i=i+1;}out''',
 ['0<=i<=n && out==2*i'],['i<=n && out==2*i'])

# Separate decisions over a growing input prefix.
for name,initial,op,quant in [('all-accepted','true','&&','forall'),('any-accepted','false','||','exists')]:
 dmodel='(forall j:nat :: j<@N@ ==> flags[j])' if quant=='forall' else '(exists j:nat :: j<@N@ && flags[j])'
 vmodel='(forall|j:int|0<=j<@N@ ==> flags@[j])' if quant=='forall' else '(exists|j:int|0<=j<@N@ && flags@[j])'
 task(name,'Return the '+('universal' if quant=='forall' else 'existential')+' truth of flags over the original full ledger, including empty input.',
 'method LabTask(flags:seq<bool>) returns(answer:bool) ensures answer=='+dmodel.replace('@N@','|flags|'),
 'fn lab_task(flags:&Vec<bool>)->(answer:bool) ensures answer=='+vmodel.replace('@N@','flags.len()')+',',
 'var i:=0;answer:='+initial+';while i<|flags|\n invariant @SITE@\n {answer:=answer '+op+' flags[i];i:=i+1;}',
 'let mut i:usize=0;let mut answer:bool='+initial+';while i<flags.len()\n invariant @SITE@\n decreases flags.len()-i,\n {answer=answer '+op+' flags[i];i=i+1;}answer',
 ['0<=i<=|flags| && answer=='+dmodel.replace('@N@','i')],['i<=flags.len() && answer=='+vmodel.replace('@N@','i')])

# Three output ledgers: identity, reversal and Boolean complementation.
for name,di,vi,exprd,exprv in [('copy-ledger','j','j','flags[i]','flags[i]'),('reverse-ledger','|flags|-1-j','flags.len()-1-j','flags[|flags|-1-i]','flags[flags.len()-1-i]'),('negate-ledger','j','j','!flags[i]','!flags[i]')]:
 drel=('!flags['+di+']') if name=='negate-ledger' else 'flags['+di+']'
 vrel=('!flags@['+vi+']') if name=='negate-ledger' else 'flags@['+vi+']'
 task(name,'Produce the specified output ledger from the immutable original flags, preserving its length and every indexed relation.',
 'method LabTask(flags:seq<bool>) returns(out:seq<bool>) ensures |out|==|flags| ensures forall j:nat :: j<|flags| ==> out[j]=='+drel,
 'fn lab_task(flags:&Vec<bool>)->(out:Vec<bool>) ensures out.len()==flags.len(),forall|j:int|0<=j<flags.len() ==> out@[j]=='+vrel+',',
 'var i:=0;out:=[];while i<|flags|\n invariant @SITE@\n {out:=out+['+exprd+'];i:=i+1;}',
 'let mut i:usize=0;let mut out:Vec<bool>=Vec::new();while i<flags.len()\n invariant @SITE@\n decreases flags.len()-i,\n {out.push('+exprv+');i=i+1;}out',
 ['0<=i<=|flags| && |out|==i && (forall j:nat :: j<i ==> out[j]=='+drel+')'],
 ['i<=flags.len() && out.len()==i && (forall|j:int|0<=j<i ==> out@[j]=='+vrel+')'])

task('concat-ledgers','Concatenate two immutable flag ledgers, preserving both ordered input segments. Verus requires the combined length to be representable.',
 'method LabTask(left:seq<bool>,right:seq<bool>) returns(out:seq<bool>) ensures |out|==|left|+|right| ensures forall j:nat :: j<|left| ==> out[j]==left[j] ensures forall j:nat :: j<|right| ==> out[|left|+j]==right[j]',
 'fn lab_task(left:&Vec<bool>,right:&Vec<bool>)->(out:Vec<bool>) requires left.len()+right.len()<=usize::MAX, ensures out.len()==left.len()+right.len(),forall|j:int|0<=j<left.len() ==> out@[j]==left@[j],forall|j:int|0<=j<right.len() ==> out@[left.len()+j]==right@[j],',
 '''var i:=0;out:=[];while i<|left|
 invariant @SITE@
 {out:=out+[left[i]];i:=i+1;}
 var k:=0;while k<|right|
 invariant @SITE@
 {out:=out+[right[k]];k:=k+1;}''',
 '''let mut i:usize=0;let mut out:Vec<bool>=Vec::new();while i<left.len()
 invariant @SITE@
 decreases left.len()-i,
 {out.push(left[i]);i=i+1;}
 let mut k:usize=0;while k<right.len()
 invariant @SITE@
 decreases right.len()-k,
 {out.push(right[k]);k=k+1;}out''',
 ['0<=i<=|left| && |out|==i && (forall j:nat :: j<i ==> out[j]==left[j])','0<=k<=|right| && |out|==|left|+k && (forall j:nat :: j<|left| ==> out[j]==left[j]) && (forall j:nat :: j<k ==> out[|left|+j]==right[j])'],
 ['i<=left.len() && out.len()==i && (forall|j:int|0<=j<i ==> out@[j]==left@[j])','k<=right.len() && out.len()==left.len()+k && (forall|j:int|0<=j<left.len() ==> out@[j]==left@[j]) && (forall|j:int|0<=j<k ==> out@[left.len()+j]==right@[j])'])

drel='((j+1<|flags| ==> out[j]==flags[j+1]) && (j+1==|flags| ==> out[j]==flags[0]))'
vrel='((j+1<flags.len() ==> out@[j]==flags@[j+1]) && (j+1==flags.len() ==> out@[j]==flags@[0]))'
task('rotate-ledger','Rotate a nonempty immutable flag ledger left by one position, retaining the last-to-first boundary case.',
 'method LabTask(flags:seq<bool>) returns(out:seq<bool>) requires |flags|>0 ensures |out|==|flags| ensures forall j:nat :: j<|flags| ==> '+drel,
 'fn lab_task(flags:&Vec<bool>)->(out:Vec<bool>) requires flags.len()>0, ensures out.len()==flags.len(),forall|j:int|0<=j<flags.len() ==> '+vrel+',',
 '''var i:=0;out:=[];while i<|flags|
 invariant @SITE@
 {var value:=if i+1<|flags| then flags[i+1] else flags[0];out:=out+[value];i:=i+1;}''',
 '''let mut i:usize=0;let mut out:Vec<bool>=Vec::new();while i<flags.len()
 invariant @SITE@
 decreases flags.len()-i,
 {let value=if i+1<flags.len() {flags[i+1]} else {flags[0]};out.push(value);i=i+1;}out''',
 ['0<=i<=|flags| && |out|==i && (forall j:nat :: j<i ==> '+drel+')'],
 ['i<=flags.len() && out.len()==i && (forall|j:int|0<=j<i ==> '+vrel+')'])

# Recursive arithmetic models, with their one-step equations explicitly given.
for name,model,dparams,vparams,dsummand,vsummand,extra in [
 ('sum-prefix-indices','IndexSum','n:nat','n:usize','i','i',False),
 ('sum-prefix-odds','OddSum','n:nat','n:usize','2*i+1','2*i+1',False),
 ('repeat-increment','RepeatSum','n:nat,amount:nat','n:usize,amount:usize','amount','amount',True)]:
 low=2000 if name=='sum-prefix-odds' else 1000
 dargs='amount,' if extra else '';vargs='amount,' if extra else ''
 modelv={'IndexSum':'index_sum','OddSum':'odd_sum','RepeatSum':'repeat_sum'}[model]
 dtype='amount:nat,k:nat' if extra else 'k:nat';vtype='amount:nat,k:nat' if extra else 'k:nat'
 dterm='amount' if extra else ('2*(k-1)+1' if name=='sum-prefix-odds' else 'k-1')
 vterm='amount' if extra else ('2*(k-1)+1' if name=='sum-prefix-odds' else 'k-1')
 dh='ghost function '+model+'('+dtype+'):nat decreases k {if k==0 then 0 else '+model+'('+dargs+'k-1)+'+dterm+'}\n'
 dh+='lemma StepModel('+('amount:nat,' if extra else '')+'i:nat) ensures '+model+'('+dargs+'i+1)=='+model+'('+dargs+'i)+'+dsummand+' {}\n'
 vh='pub open spec fn '+modelv+'('+vtype+')->nat decreases k, {if k==0 {0} else {'+modelv+'('+vargs+'(k-1) as nat)+(('+vterm+') as nat)}}\n'
 vh+='proof fn step_model('+('amount:nat,' if extra else '')+'i:nat) ensures '+modelv+'('+vargs+'i+1)=='+modelv+'('+vargs+'i)+'+vsummand+', {}\n'
 task(name,'Compute the original recursive arithmetic model by a provided bounded executable loop; keep the original n<=1000'+(' and amount<=1000' if extra else '')+' domain.',
 'method LabTask('+dparams+') returns(out:nat) requires n<=1000'+(' && amount<=1000' if extra else '')+' ensures out=='+model+'('+dargs+'n)',
 'fn lab_task('+vparams+')->(out:usize) requires n<=1000'+(',amount<=1000' if extra else '')+', ensures out=='+modelv+'('+('amount as nat,' if extra else '')+'n as nat),',
 'var i:=0;out:=0;while i<n\n invariant @SITE@\n {StepModel('+dargs+'i);out:=out+'+dsummand+';i:=i+1;}',
 'let mut i:usize=0;let mut out:usize=0;while i<n\n invariant @SITE@\n decreases n-i,\n {proof {step_model('+('amount as nat,' if extra else '')+'i as nat);}out=out+'+vsummand+';i=i+1;}out',
 ['0<=i<=n && out<='+str(low)+'*i && out=='+model+'('+dargs+'i)'],
 ['i<=n && out<='+str(low)+'*i && out=='+modelv+'('+('amount as nat,' if extra else '')+'i as nat)'],dh,vh)

task('quotient-three','Compute division by3by repeatedly consuming three credits; return the exact Euclidean quotient.',
 'method LabTask(n:nat) returns(q:nat) ensures q==n/3',
 'fn lab_task(n:usize)->(q:usize) ensures q==n/3,',
 '''q:=0;var rest:=n;while rest>=3
 invariant @SITE@
 decreases rest
 {rest:=rest-3;q:=q+1;}''',
 '''let mut q:usize=0;let mut rest:usize=n;while rest>=3
 invariant @SITE@
 decreases rest,
 {rest=rest-3;q=q+1;}q''',
 ['3*q+rest==n'],['3*q+rest==n'])
task('remainder-three','Advance a cyclic0/1/2counter for every original input position and return n modulo3.',
 'method LabTask(n:nat) returns(rest:nat) ensures rest==n%3',
 'fn lab_task(n:usize)->(rest:usize) ensures rest==n%3,',
 '''var i:=0;rest:=0;while i<n
 invariant @SITE@
 {if rest==2 {rest:=0;}else{rest:=rest+1;}i:=i+1;}''',
 '''let mut i:usize=0;let mut rest:usize=0;while i<n
 invariant @SITE@
 decreases n-i,
 {if rest==2 {rest=0;}else{rest=rest+1;}i=i+1;}rest''',
 ['0<=i<=n && rest<3 && rest==i%3'],['i<=n && rest<3 && rest==i%3'])
task('first-mismatch','Compare equally long original flag ledgers and return the first unequal position, or their length.',
 'method LabTask(left:seq<bool>,right:seq<bool>) returns(at:nat) requires |left|==|right| ensures at<=|left| ensures forall j:nat :: j<at ==> left[j]==right[j] ensures at==|left| || left[at]!=right[at]',
 'fn lab_task(left:&Vec<bool>,right:&Vec<bool>)->(at:usize) requires left.len()==right.len(), ensures at<=left.len(),forall|j:int|0<=j<at ==> left@[j]==right@[j],at==left.len() || left@[at as int]!=right@[at as int],',
 '''at:=0;while at<|left| && left[at]==right[at]
 invariant @SITE@
 {at:=at+1;}''',
 '''let mut at:usize=0;while at<left.len() && left[at]==right[at]
 invariant @SITE@
 decreases left.len()-at,
 {at=at+1;}at''',
 ['0<=at<=|left| && (forall j:nat :: j<at ==> left[j]==right[j])'],
 ['at<=left.len() && (forall|j:int|0<=j<at ==> left@[j]==right@[j])'])
for name,cmp in [('minimum-value','<='),('maximum-value','>=')]:
 branch='<' if cmp=='<=' else '>'
 task(name,'Return an extremal element of the original nonempty sequence; preserve both the bound and an actual membership witness.',
 'method LabTask(values:seq<nat>) returns(best:nat) requires |values|>0 ensures forall j:nat :: j<|values| ==> best'+cmp+'values[j] ensures exists j:nat :: j<|values| && best==values[j]',
 'fn lab_task(values:&Vec<usize>)->(best:usize) requires values.len()>0, ensures forall|j:int|0<=j<values.len() ==> best'+cmp+'values@[j],exists|j:int|0<=j<values.len() && best==values@[j],',
 'var i:=1;best:=values[0];while i<|values|\n invariant @SITE@\n {if values[i]'+branch+'best {best:=values[i];}i:=i+1;}',
 'let mut i:usize=1;let mut best:usize=values[0];while i<values.len()\n invariant @SITE@\n decreases values.len()-i,\n {if values[i]'+branch+'best {best=values[i];}i=i+1;}best',
 ['1<=i<=|values| && (forall j:nat :: j<i ==> best'+cmp+'values[j]) && (exists j:nat :: j<i && best==values[j])'],
 ['1<=i && i<=values.len() && (forall|j:int|0<=j<i ==> best'+cmp+'values@[j]) && (exists|j:int|0<=j<i && best==values@[j])'])

def render(row,lang):
 inv=row[lang+'inv'];body=row[lang+'body'];sites=[]
 for i,hint in enumerate(inv):
  ids=tuple(sorted(set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*',hint))-{'forall','exists','as','int','nat','bool','true','false'}))
  sites.append(HintSite('loop'+str(i+1),ids))
  body=body.replace('@SITE@',sites[-1].marker,1)
 if '@SITE@' in body:raise ValueError('missing loop hint')
 text=('module R12_LabCase {\n'+row['dh']+' '+row['dhead']+'\n {\n'+body+'\n }\n}\n') if lang=='d' else ('use vstd::prelude::*;\nverus! {\n'+row['vh']+' #[verifier::loop_isolation(false)]\n '+row['vhead']+'\n {\n'+body+'\n }\n}\n')
 head=row[lang+'head'];start=text[:text.index(head)].count('\n')+3;end=len(text.splitlines())+1
 meta='// R12_HINT_SITES: '+json.dumps([dict(name=s.name,identifiers=list(s.identifiers)) for s in sites],separators=(',',':'))+'\n'
 meta+='// R12_SOURCE_SPANS: '+json.dumps([dict(symbol='R12_LabCase.LabTask' if lang=='d' else 'lab_task',start=start,end=end)],separators=(',',':'))+'\n'
 source=meta+text;task,_=source_task(source)
 good=source
 for site,hint in zip(task.sites,inv):good=good.replace(site.marker,'('+hint+')',1)
 check_source_frame(task,good)
 return source,good

rows=[]
for row in TASKS:
 for lang in 'dv':
  source,good=render(row,lang);name=row['name']+'-'+lang;ext='.dfy' if lang=='d' else '.rs'
  for kind,text in [('form',source),('good',good)]:
   path=B/kind/(name+ext);path.parent.mkdir(exist_ok=True);path.write_text(text)
  rows.append(dict(id=name,lang=lang,form=str(B/'form'/(name+ext)),good=str(B/'good'/(name+ext)),statement=row['statement']))
(B/'index.json').write_text(json.dumps(rows,indent=2)+'\n');print('Private native forms/completions:',len(rows))
