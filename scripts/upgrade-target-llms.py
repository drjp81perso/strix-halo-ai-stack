#!/usr/bin/env python3
"""Prepare, qualify, and promote the two hardware-screened text-model candidates."""
from pathlib import Path
import argparse,copy,datetime,json,os,shutil,subprocess,sys,time,yaml
ROOT=Path(__file__).resolve().parents[1]
TARGETS={
 'llm/qwen38-27b-q5':{'stable_id':'llm/coder','replace_ids':['llm/coder'],'name':'Qwen 3.8 27B Q5 — Coding and Agents','description':'16K coding, agents, chat and vision model','model':'/models/llm/qwen38-27b-q5/Qwen3.8-27B-UD-Q5_K_M.gguf','mmproj':'/models/llm/qwen38-27b-q5/mmproj-BF16.gguf','profile':'coder','tests':['upgrade/coder','upgrade/chat','upgrade/vision'],'min_tps':7.5,'ttl':900},
 'llm/gemma4-31b-q5':{'stable_id':'llm/vision','replace_ids':['llm/vision'],'name':'Gemma 4 31B Q5 — Vision and Documents','description':'16K chat, vision and documents model','model':'/models/llm/gemma4-31b-q5/gemma-4-31B-it-Q5_K_M.gguf','mmproj':'/models/llm/gemma4-31b-q5/mmproj-BF16.gguf','profile':'vision','tests':['upgrade/vision','upgrade/chat'],'min_tps':7.5,'ttl':900},
}
def run(cmd,check=True,capture=False,env=None):
 print('+',' '.join(map(str,cmd)),flush=True);return subprocess.run(cmd,cwd=ROOT,check=check,text=True,capture_output=capture,env=env)
def envfile():
 d=os.environ.copy();p=ROOT/'.env'
 if p.exists():
  for l in p.read_text().splitlines():
   if l.strip() and not l.lstrip().startswith('#') and '=' in l:
    k,v=l.split('=',1);d[k]=v.strip().strip('"').strip("'")
 return d
def block(mid,s):
 # Candidate profiles are role-specific. Basic coder and vision contracts require visible final output.
 reasoning=' --reasoning off' if s['profile'] in {'coder','vision'} else ''
 mm=f" --mmproj {s['mmproj']}" if s.get('mmproj') else ''
 return {'name':s['name'],'description':s['description'],'capabilities':{'in':['text','image'],'out':['text'],'tools':True,'context':16384},'cmd':f"admit-run ${{env.HEAVY_HOST_RESERVE_GB}} ${{env.HEAVY_MAX_CURRENT_GTT_GB}} -- llama-server --host 127.0.0.1 --port ${{PORT}} --model {s['model']}{mm} --ctx-size 16384 --parallel 1 --n-gpu-layers auto --fit on --fit-target ${{env.GPU_FIT_TARGET_MIB}} --fit-ctx ${{env.MIN_FIT_CONTEXT}} --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 --jinja{reasoning}",'ttl':s['ttl']}
def edit_template(candidates,promote=False):
 p=ROOT/'templates/llama-swap.yaml';d=yaml.safe_load(p.read_text());models=d['models'];groups=d['routing']['router']['settings']['groups']['heavyweight-exclusive']['members']
 for cid in candidates:
  spec=TARGETS[cid];candidate='candidate/'+cid.split('/',1)[1];serve=spec['stable_id'] if promote else candidate
  models[serve]=block(serve,spec)
  if serve not in groups:groups.append(serve)
  if promote:
   models.pop(candidate,None)
   groups[:]=[x for x in groups if x!=candidate]
 p.write_text(yaml.safe_dump(d,sort_keys=False,allow_unicode=True,width=140))
def edit_tests(candidates,promote=False):
 # Upgrade tests use permanent role contracts in tests/models.yaml.
 return
def edit_registry(candidates,promote=False):
 if not promote:return
 p=ROOT/'registry/models.yaml';d=yaml.safe_load(p.read_text());models=d['models'];byid={m['id']:m for m in models}
 for cid in candidates:
  spec=TARGETS[cid];candidate=byid[cid];stable=byid[spec['stable_id']]
  # Keep the stable public ID. Replace its artifact and runtime metadata.
  keep={'id':stable['id'],'role':stable['role'],'ttl_seconds':spec['ttl'],'enabled':True,'track':'active','lifecycle':'executable','test_status':'implemented'}
  for key in ('engine','source','files','include','local_dir','license','approximate_weight_gib','target_context','estimated_tokens_per_second','selection_sources'):
   if key in candidate:keep[key]=copy.deepcopy(candidate[key])
  stable.clear();stable.update(keep);candidate.update(enabled=False,track='retired',lifecycle='retired',test_status='planned',promoted_as=spec['stable_id'])
 p.write_text(yaml.safe_dump(d,sort_keys=False,allow_unicode=True,width=140))
def qualify(cid,spec,env,out):
 serve='candidate/'+cid.split('/',1)[1];base=f"http://127.0.0.1:{env.get('AI_PORT','9292')}";key=env['AI_API_KEY'];results=[]
 for testid in spec['tests']:
  start=time.monotonic();started_at=time.time();before={p.resolve() for p in (ROOT/'benchmark-results').glob(serve.replace('/','__')+'-*.json')};r=run([sys.executable,'tests/run.py',serve,'--spec-id',testid,'--base',base,'--key',key],check=False,capture=True,env=env);log=out/f"{serve.replace('/','__')}--{testid.replace('/','__')}.log";log.write_text(r.stdout+'\n'+r.stderr);latest=[]
  for p in (ROOT/'benchmark-results').glob(serve.replace('/','__')+'-*.json'):
   if p.resolve() in before:continue
   if p.stat().st_mtime+1<started_at:continue
   try:data=json.loads(p.read_text())
   except json.JSONDecodeError:continue
   if data.get('model')==serve and data.get('spec_id')==testid:latest.append(p)
  latest.sort(key=lambda p:p.stat().st_mtime)
  tps=None
  state='runtime-fail';qualification={} ; error=None
  if latest:
   data=json.loads(latest[-1].read_text());tps=data.get('response',{}).get('timings',{}).get('predicted_per_second');state=data.get('qualification_state','pass' if data.get('passed') else 'semantic-fail');qualification=data.get('qualification',{});error=data.get('error')
  results.append({'test':testid,'role':spec['profile'],'passed':r.returncode==0,'state':state,'qualification':qualification,'error':error,'seconds':round(time.monotonic()-start,2),'generation_tps':tps,'log':str(log)})
  if r.returncode:return False,results
 # Speed gate uses any text-generation test with timings.
 speeds=[x['generation_tps'] for x in results if x['generation_tps'] is not None]
 return bool(speeds and min(speeds)>=spec['min_tps']),results
def model_ready(cid,env):
 r=subprocess.run([sys.executable,'scripts/model-manager.py','--track','all','--id',cid,'status','--json'],cwd=ROOT,text=True,capture_output=True,env=env)
 if r.returncode!=0:return False
 try:rows=json.loads(r.stdout).get('models',[])
 except json.JSONDecodeError:return False
 return bool(rows and rows[0].get('managed') and not rows[0].get('missing'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--no-prune',action='store_true');p.add_argument('--refresh-models',action='store_true',help='download registered artifacts again');p.add_argument('--minimum-free-gib',type=int,default=80);a=p.parse_args();candidates=list(TARGETS);env=envfile();ready={cid:model_ready(cid,env) for cid in candidates};stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S');work=ROOT/'upgrade-results'/stamp;files=['templates/llama-swap.yaml','config/llama-swap.yaml','tests/models.yaml','tests/planned-models.yaml','registry/models.yaml']
 print('UPGRADE PLAN',*candidates,sep='\n - ')
 print(f' - minimum free disk for downloads: {a.minimum_free_gib} GiB')
 for cid in candidates:print(f" - {cid}: {'refresh' if a.refresh_models else 'reuse' if ready[cid] else 'download'}")
 print(' - old coder and vision files move to quarantine only after all tests pass')
 if not a.apply:print('\nDry run only. Re-run with --apply.');return
 # Runtime scripts must work in an rsync deployment with no Git metadata.
 missing=[f for f in files if not (ROOT/f).is_file()]
 if missing:raise SystemExit('Required deployment files are missing: '+', '.join(missing))
 model_dir=Path(env.get('MODEL_DIR',ROOT/'models'));free=shutil.disk_usage(model_dir).free/1024**3
 if (a.refresh_models or not all(ready.values())) and free<a.minimum_free_gib:raise SystemExit(f'Need at least {a.minimum_free_gib} GiB free for model downloads; found {free:.1f} GiB')
 work.mkdir(parents=True);backup=work/'backup';backup.mkdir()
 # Save a complete transaction snapshot. This is the rollback source in a deployment directory.
 manifest={'created':stamp,'root':str(ROOT),'model_dir':str(model_dir),'files':files,'candidates':candidates}
 for f in files:
  src=ROOT/f;dst=backup/f;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 (backup/'transaction.json').write_text(json.dumps(manifest,indent=2))
 try:
  run(['./scripts/ai-stack','protocol','exposed'])
  for cid in candidates:
   cmd=[sys.executable,'scripts/model-manager.py','--track','all','--id',cid,'sync']
   if a.refresh_models:cmd.append('--force')
   run(cmd,env=env)
  edit_template(candidates);edit_tests(candidates);run(['./scripts/generate-config']);run(['./scripts/validate']);run(['docker','compose','up','-d','--force-recreate','gateway']);time.sleep(5)
  qualification={};ok=True
  for cid in candidates:
   good,res=qualify(cid,TARGETS[cid],env,work);qualification[cid]={'passed':good,'results':res};ok &= good
  (work/'qualification.json').write_text(json.dumps(qualification,indent=2))
  if not ok:raise RuntimeError('A candidate failed its semantic or 7.5 tok/s qualification gate')
  edit_template(candidates,True);edit_tests(candidates,True);edit_registry(candidates,True);run(['./scripts/generate-config']);run(['./scripts/validate']);run(['docker','compose','up','-d','--force-recreate','gateway']);time.sleep(5);run(['./scripts/ai-stack','protocol','exposed']);run(['./scripts/ai-stack','protocol','openwebui'])
  if not a.no_prune:
   # Quarantine only the two replaced model directories. Do not touch other downloaded candidates.
   trash=model_dir/'.trash'/stamp
   old_dirs=[model_dir/'llm/coder',model_dir/'vision/qwen3vl']
   moved=[]
   for old in old_dirs:
    if old.exists():
     target=trash/old.relative_to(model_dir);target.parent.mkdir(parents=True,exist_ok=True);os.replace(old,target);moved.append(str(old.relative_to(model_dir)))
   if moved:
    trash.mkdir(parents=True,exist_ok=True);(trash/'upgrade-manifest.json').write_text(json.dumps({'created':stamp,'reason':'replaced by qualified target LLMs','files':moved},indent=2));print('QUARANTINED',*moved,sep='\n - ')
  print('UPGRADE PASS. Results:',work)
 except Exception as e:
  print('UPGRADE FAILED:',e,file=sys.stderr);print('RESTORING CONFIGURATION',file=sys.stderr)
  for f in files:
   src=backup/f;dst=ROOT/f
   if src.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  run(['./scripts/generate-config'],check=False);run(['docker','compose','up','-d','--force-recreate','gateway'],check=False);raise
if __name__=='__main__':main()
