#!/usr/bin/env python3
"""Show, change, and apply per-model runtime policy from .env."""
from pathlib import Path
import argparse,json,os,re,subprocess,sys,time,urllib.error,urllib.parse,urllib.request
ROOT=Path(__file__).resolve().parents[1]
MODELS={
 'llm/fast':{'context':'LLM_FAST_CONTEXT_SIZE'},
 'llm/reasoning':{'context':'LLM_REASONING_CONTEXT_SIZE','fit_context':'LLM_REASONING_FIT_CONTEXT','reasoning_budget':'LLM_REASONING_BUDGET'},
 'llm/coder':{'context':'LLM_CODER_CONTEXT_SIZE','fit_context':'LLM_CODER_FIT_CONTEXT'},
 'llm/vision':{'context':'LLM_VISION_CONTEXT_SIZE','fit_context':'LLM_VISION_FIT_CONTEXT'},
}
def read_env(path):
 out={}
 if path.exists():
  for line in path.read_text().splitlines():
   if line.strip() and not line.lstrip().startswith('#') and '=' in line:
    k,v=line.split('=',1);out[k]=v.strip().strip('"').strip("'")
 return out
def values():return {**read_env(ROOT/'.env.example'),**os.environ,**read_env(ROOT/'.env')}
def positive(name,value):
 try:n=int(value)
 except (TypeError,ValueError):raise SystemExit(f'{name} must be a positive integer')
 if n<=0:raise SystemExit(f'{name} must be a positive integer')
 return n
def show(mid,as_json=False):
 cfg=MODELS[mid];v=values();row={'model':mid,'context_size':positive(cfg['context'],v.get(cfg['context'])),'fit_context':positive(cfg['fit_context'],v.get(cfg['fit_context'])) if 'fit_context' in cfg else None,'reasoning_budget':positive(cfg['reasoning_budget'],v.get(cfg['reasoning_budget'])) if 'reasoning_budget' in cfg else None,'source':'.env'}
 if as_json:print(json.dumps(row,indent=2));return
 print(f"Model:            {row['model']}\nContext size:     {row['context_size']} tokens")
 if row['fit_context'] is not None:print(f"Minimum fit:      {row['fit_context']} tokens")
 if row['reasoning_budget'] is not None:print(f"Reasoning budget: {row['reasoning_budget']} tokens")
def update_env(changes):
 path=ROOT/'.env'
 if not path.exists():raise SystemExit('Missing .env. Copy .env.example to .env first.')
 lines=path.read_text().splitlines();seen=set();out=[]
 for line in lines:
  if '=' in line and not line.lstrip().startswith('#'):
   key=line.split('=',1)[0]
   if key in changes:out.append(f'{key}={changes[key]}');seen.add(key);continue
  out.append(line)
 if changes.keys()-seen:
  out += ['', '# Per-model runtime policy.']+[f'{k}={changes[k]}' for k in changes if k not in seen]
 path.write_text('\n'.join(out)+'\n')
def api(mid):
 v=values();bind=v.get('AI_BIND','127.0.0.1');bind='127.0.0.1' if bind in ('0.0.0.0','::') else bind;port=v.get('AI_PORT','9292');key=v.get('AI_API_KEY')
 if not key:raise SystemExit('AI_API_KEY is missing')
 url=f'http://{bind}:{port}/api/models/unload/'+urllib.parse.quote(mid,safe='')
 req=urllib.request.Request(url,method='POST',headers={'Authorization':f'Bearer {key}'})
 try:
  with urllib.request.urlopen(req,timeout=30) as r:return r.read().decode(errors='replace')
 except urllib.error.HTTPError as e:
  if e.code==404:return 'Model was not loaded.'
  raise SystemExit(f'Unload failed: HTTP {e.code}: {e.read().decode(errors="replace")}')
def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 for command in ('show','set','apply'):
  q=sub.add_parser(command);q.add_argument('model',choices=sorted(MODELS))
  if command=='show':q.add_argument('--json',action='store_true')
  if command=='set':q.add_argument('--context',type=int);q.add_argument('--fit-context',type=int);q.add_argument('--reasoning-budget',type=int)
 a=p.parse_args();cfg=MODELS[a.model]
 if a.command=='show':show(a.model,a.json);return
 if a.command=='set':
  changes={}
  if a.context is not None:changes[cfg['context']]=positive('--context',a.context)
  if a.fit_context is not None:
   if 'fit_context' not in cfg:raise SystemExit(f'{a.model} does not use automatic context fitting')
   changes[cfg['fit_context']]=positive('--fit-context',a.fit_context)
  if a.reasoning_budget is not None:
   if 'reasoning_budget' not in cfg:raise SystemExit(f'{a.model} does not use a reasoning budget')
   changes[cfg['reasoning_budget']]=positive('--reasoning-budget',a.reasoning_budget)
  if not changes:raise SystemExit('Specify at least one setting')
  current=values();context=int(changes.get(cfg['context'],current[cfg['context']]));fit=int(changes.get(cfg.get('fit_context',''),current.get(cfg.get('fit_context',''),context)))
  if fit>context:raise SystemExit('fit context cannot be larger than preferred context')
  update_env(changes);show(a.model);print('Run model-config apply to activate this policy.');return
 subprocess.run(['./scripts/generate-config'],cwd=ROOT,check=True)
 subprocess.run(['./scripts/validate'],cwd=ROOT,check=True)
 time.sleep(2);print(api(a.model));time.sleep(1);show(a.model);print('Applied. The next request loads the model with this policy.')
if __name__=='__main__':main()
