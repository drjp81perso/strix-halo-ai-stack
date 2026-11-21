#!/usr/bin/env python3
"""Functionally test selected IDs advertised by /v1/models, aliases included."""
from pathlib import Path
import argparse,datetime,json,re,subprocess,sys,time,urllib.error,urllib.request,yaml
ROOT=Path(__file__).resolve().parents[1]
def req(base,key,path,timeout=30):
 q=urllib.request.Request(base+path,headers={'Authorization':f'Bearer {key}'})
 try:
  with urllib.request.urlopen(q,timeout=timeout) as r:return r.status,r.read()
 except urllib.error.HTTPError as e:return e.code,e.read()
def stamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def fmt(s):return f'{int(s)//60}m{int(s)%60:02d}s'
def reason(text):
 lines=[x.strip() for x in text.splitlines() if x.strip()]
 for line in reversed(lines):
  if any(k in line.lower() for k in ('error','assert','traceback','failed','unknown model','http')):return line[:500]
 return lines[-1][:500] if lines else 'test process exited without diagnostic output'
def main():
 p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--key',required=True);p.add_argument('--output');p.add_argument('--id',action='append',default=[],help='exact ID; repeatable');p.add_argument('--match',help='regex applied to ID');p.add_argument('--type',choices=['model','alias']);p.add_argument('--kind',action='append',default=[],help='test kind; repeatable');p.add_argument('--fail-fast',action='store_true');a=p.parse_args()
 st,b=req(a.base,a.key,'/v1/models');assert st==200,f'/v1/models returned {st}';catalog=json.loads(b)['data'];specs=yaml.safe_load((ROOT/'tests/models.yaml').read_text())['tests'];canonical={m['id'] for m in catalog if m.get('meta',{}).get('llamaswap',{}).get('type')=='model'}
 selected=[]
 for r in catalog:
  meta=r.get('meta',{}).get('llamaswap',{});typ=meta.get('type');target=r['id'] if typ=='model' else meta.get('modelID') if typ=='alias' else None;kind=specs.get(target,{}).get('kind')
  if a.id and r['id'] not in a.id:continue
  if a.match and not re.search(a.match,r['id']):continue
  if a.type and typ!=a.type:continue
  if a.kind and kind not in a.kind:continue
  selected.append((r,typ,target,kind))
 total=len(selected);start=time.monotonic();results=[];print(f'[{stamp()}] CATALOG returned={len(catalog)} selected={total} canonical={len(canonical)} aliases={len(catalog)-len(canonical)} filters={{"id":{a.id},"match":{a.match!r},"type":{a.type!r},"kind":{a.kind}}}',flush=True)
 if not total:raise SystemExit('No /v1/models IDs matched the filters')
 for index,(record,typ,target,kind) in enumerate(selected,1):
  mid=record['id'];item={'id':mid,'catalog_type':typ,'canonical_target':target,'name':record.get('name'),'test_kind':kind,'initial_status':record.get('status',{}).get('value')}
  pre_error=None
  if typ not in ('model','alias'):pre_error='unsupported catalog record type'
  elif target not in canonical:pre_error=f'canonical target not advertised: {target}'
  elif target not in specs:pre_error=f'canonical target has no executable test: {target}'
  if pre_error:
   item.update(status='fail',reason=pre_error);results.append(item);print(f'[{stamp()}] FAIL  {index:02d}/{total:02d} id={mid} reason={pre_error}',flush=True)
   if a.fail_fast:break
   continue
  run_stamp=time.strftime('%Y%m%d-%H%M%S');log=ROOT/'benchmark-results'/f"exposed__{mid.replace('/','__')}-{run_stamp}.log";t=time.monotonic();print(f'[{stamp()}] START {index:02d}/{total:02d} id={mid} type={typ} target={target} test={kind}',flush=True);cmd=[sys.executable,str(ROOT/'tests/run.py'),mid,'--spec-id',target,'--base',a.base,'--key',a.key];run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);combined=run.stdout+'\n'+run.stderr;log.parent.mkdir(exist_ok=True);log.write_text(combined);item.update(status='pass' if run.returncode==0 else 'fail',seconds=round(time.monotonic()-t,3),exit_code=run.returncode,log=str(log))
  if run.returncode:item['reason']=reason(combined);item['error_excerpt']=combined[-3000:]
  results.append(item);extra='' if run.returncode==0 else f' reason={item["reason"]}';print(f'[{stamp()}] {item["status"].upper():4}  {index:02d}/{total:02d} id={mid} elapsed={fmt(item["seconds"])} exit={run.returncode} log={log}{extra}',flush=True)
  if run.returncode and a.fail_fast:break
 summary={'catalog_count':len(catalog),'selected_count':total,'results':results,'passed_count':sum(r['status']=='pass' for r in results),'failed_count':sum(r['status']!='pass' for r in results),'elapsed_seconds':round(time.monotonic()-start,3),'filters':{'ids':a.id,'match':a.match,'type':a.type,'kinds':a.kind}};summary['untested_selected_count']=total-len(results);summary['passed']=summary['failed_count']==0 and summary['untested_selected_count']==0
 dest=Path(a.output) if a.output else ROOT/'benchmark-results'/f"exposed-summary-{time.strftime('%Y%m%d-%H%M%S')}.json";dest.parent.mkdir(exist_ok=True);dest.write_text(json.dumps(summary,indent=2));print(f'[{stamp()}] COMPLETE passed={summary["passed_count"]} failed={summary["failed_count"]} untested={summary["untested_selected_count"]} elapsed={fmt(summary["elapsed_seconds"])} report={dest}',flush=True);print(f"{'RESULT':<6} {'TYPE':<7} {'ID':<38} {'TARGET':<38} {'SECONDS':<8} REASON")
 for r in results:print(f"{r['status'].upper():<6} {str(r['catalog_type']):<7} {r['id']:<38} {str(r['canonical_target']):<38} {str(r.get('seconds','-')):<8} {r.get('reason','')}")
 if not summary['passed']:raise SystemExit(1)
if __name__=='__main__':main()
