#!/usr/bin/env python3
from pathlib import Path
import argparse, concurrent.futures, json, os, sys, time, urllib.error, urllib.request, yaml
ROOT=Path(__file__).resolve().parents[1]
def req(base,key,path,body=None,method=None,timeout=900):
 h={'Authorization':f'Bearer {key}'}; data=None
 if body is not None:data=json.dumps(body).encode();h['Content-Type']='application/json'
 q=urllib.request.Request(base+path,data=data,headers=h,method=method or ('POST' if body else 'GET'))
 try:
  with urllib.request.urlopen(q,timeout=timeout) as r:return r.status,r.read()
 except urllib.error.HTTPError as e:return e.code,e.read()
def chat(base,key,model,prompt,max_tokens):
 t=time.monotonic(); st,b=req(base,key,'/v1/chat/completions',{'model':model,'messages':[{'role':'user','content':prompt}],'temperature':0,'max_tokens':max_tokens,'stream':False});
 try:d=json.loads(b)
 except:d={'raw':b.decode(errors='replace')}
 return {'status':st,'seconds':round(time.monotonic()-t,3),'body':d}
def main():
 p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--key',required=True);p.add_argument('--output');a=p.parse_args(); spec=yaml.safe_load((ROOT/'tests/protocol.yaml').read_text())['suites']['openwebui']; req(a.base,a.key,'/api/models/unload',method='POST');time.sleep(3)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
  fg=ex.submit(chat,a.base,a.key,spec['model'],spec['foreground_prompt'],128);time.sleep(spec['start_delay_seconds']);bg=ex.submit(chat,a.base,a.key,spec['model'],spec['background_prompt'],64); results={'foreground':fg.result(),'background':bg.result()}
 _,running=req(a.base,a.key,'/running');results['running_loaded']=json.loads(running); req(a.base,a.key,'/api/models/unload',method='POST');time.sleep(3);_,after=req(a.base,a.key,'/running');results['running_after']=json.loads(after)
 allowed=set(spec['allowed_statuses']); statuses=[results[x]['status'] for x in ('foreground','background')]; max429=int(os.environ.get('PROTOCOL_MAX_HTTP_429','0')); results['http_429_count']=statuses.count(429); results['configured_gateway_concurrency']=int(os.environ.get('GLOBAL_CONCURRENCY_LIMIT','0')); results['allowed_429_count']=max429; results['passed']=all(x in allowed for x in statuses) and results['http_429_count']<=max429 and not results['running_after']['running']
 out=Path(a.output) if a.output else ROOT/'benchmark-results'/f"openwebui-burst-{time.strftime('%Y%m%d-%H%M%S')}.json";out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(results,indent=2));print(json.dumps({k:v for k,v in results.items() if k not in ('foreground','background')},indent=2));print('foreground',results['foreground']['status'],results['foreground']['seconds']);print('background',results['background']['status'],results['background']['seconds']);print('result',out)
 if not results['passed']:raise SystemExit(1)
if __name__=='__main__':main()
