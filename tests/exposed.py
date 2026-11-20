#!/usr/bin/env python3
"""Functionally test every canonical model advertised by /v1/models."""
from pathlib import Path
import argparse,json,subprocess,sys,time,urllib.error,urllib.request,yaml
ROOT=Path(__file__).resolve().parents[1]
def req(base,key,path,body=None,method=None,timeout=1800):
 h={'Authorization':f'Bearer {key}'};data=None
 if body is not None:data=json.dumps(body).encode();h['Content-Type']='application/json'
 q=urllib.request.Request(base+path,data=data,headers=h,method=method or ('POST' if body is not None else 'GET'))
 try:
  with urllib.request.urlopen(q,timeout=timeout) as r:return r.status,r.read()
 except urllib.error.HTTPError as e:return e.code,e.read()
def main():
 p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--key',required=True);p.add_argument('--output');a=p.parse_args()
 st,b=req(a.base,a.key,'/v1/models',timeout=30);assert st==200,f'/v1/models={st}';catalog=json.loads(b)['data'];canonical=[];aliases=[]
 for m in catalog:
  meta=m.get('meta',{}).get('llamaswap',{})
  (canonical if meta.get('type')=='model' else aliases if meta.get('type')=='alias' else []).append(m)
 specs=yaml.safe_load((ROOT/'tests/models.yaml').read_text())['tests'];results=[];seen=set()
 for m in canonical:
  mid=m['id'];seen.add(mid);item={'id':mid,'name':m.get('name'),'capabilities':m.get('capabilities',{}),'context':m.get('context_length'),'initial_status':m.get('status',{}).get('value')}
  if mid not in specs:item.update(status='fail',error='advertised canonical model has no executable functional test');results.append(item);continue
  t=time.monotonic();out=ROOT/'benchmark-results'/f"exposed__{mid.replace('/','__')}-{time.strftime('%Y%m%d-%H%M%S')}.log"
  cmd=[sys.executable,str(ROOT/'tests/run.py'),mid,'--base',a.base,'--key',a.key]
  run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);item.update(status='pass' if run.returncode==0 else 'fail',seconds=round(time.monotonic()-t,3),test_kind=specs[mid]['kind'],log=str(out));out.write_text(run.stdout+'\n'+run.stderr)
  if run.returncode:item['error']=(run.stderr or run.stdout)[-2000:]
  results.append(item)
 # Alias contract: each alias must resolve to an existing canonical model; do not rerun duplicate weights.
 alias_results=[]
 for m in aliases:
  target=m.get('meta',{}).get('llamaswap',{}).get('modelID');alias_results.append({'id':m['id'],'target':target,'status':'pass' if target in seen else 'fail'})
 advertised_ids={m['id'] for m in canonical};configured_ids=set(specs);summary={'catalog_count':len(catalog),'canonical_count':len(canonical),'alias_count':len(aliases),'canonical_results':results,'alias_results':alias_results,'advertised_without_test':sorted(advertised_ids-configured_ids),'tests_not_advertised':sorted(configured_ids-advertised_ids)}
 summary['passed']=all(x['status']=='pass' for x in results+alias_results) and not summary['advertised_without_test'];summary['failed_count']=sum(x['status']!='pass' for x in results+alias_results)
 dest=Path(a.output) if a.output else ROOT/'benchmark-results'/f"exposed-summary-{time.strftime('%Y%m%d-%H%M%S')}.json";dest.parent.mkdir(exist_ok=True);dest.write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k not in ('canonical_results','alias_results')},indent=2));
 for x in results:print(f"{x['status'].upper():4} {x['id']:<36} {x.get('seconds','-')}s {x.get('test_kind','-')}")
 print('alias contracts:',sum(x['status']=='pass' for x in alias_results),'/',len(alias_results));print('report:',dest)
 if not summary['passed']:raise SystemExit(1)
if __name__=='__main__':main()
