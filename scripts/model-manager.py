#!/usr/bin/env python3
"""Registry-driven model inventory, download and safe quarantine pruning."""
from pathlib import Path
import argparse,datetime,fnmatch,hashlib,json,os,shutil,subprocess,sys,yaml
ROOT=Path(__file__).resolve().parents[1]
IGNORED={'.cache','.locks','.trash','.staging','.gitkeep'}
def load_env():
 d={}
 p=ROOT/'.env'
 if p.exists():
  for line in p.read_text().splitlines():
   line=line.strip()
   if line and not line.startswith('#') and '=' in line:
    k,v=line.split('=',1);d[k]=v.strip().strip('"').strip("'")
 return d
def registry():return yaml.safe_load((ROOT/'registry/models.yaml').read_text())['models']
def root_dir():return Path(os.environ.get('MODEL_DIR') or load_env().get('MODEL_DIR') or ROOT/'models').expanduser().resolve()
def rel_local(m):
 p=Path(m.get('local_dir',f"models/{m['id']}"));parts=p.parts
 return Path(*parts[1:]) if parts and parts[0]=='models' else p
def selected(track,ids):
 out=[]
 for m in registry():
  if ids and m['id'] not in ids:continue
  if track=='active' and not m.get('enabled'):continue
  if track not in ('all','active') and m.get('track',m.get('registry_track'))!=track:continue
  out.append(m)
 return out
def expected_patterns(m):return list(m.get('files',[]))+list(m.get('include',[]))+list(m.get('artifacts',[]))
def paths_for(m,base):
 dest=base/rel_local(m);out=[]
 for pat in expected_patterns(m):
  # Artifact entries that are HF repo names rather than file paths cannot be managed yet.
  if isinstance(pat,str) and ('*' in pat or '?' in pat):out.extend(x for x in dest.glob(pat) if x.is_file())
  elif isinstance(pat,str):
   p=dest/(Path(pat).name if m.get('flatten') else pat)
   if p.is_file():out.append(p)
 return out
def expected_set(models,base):
 files=set();dirs=set()
 for m in models:
  d=(base/rel_local(m)).resolve();dirs.add(d);files.update(p.resolve() for p in paths_for(m,base))
 return files,dirs
def size(p):return p.stat().st_size if p.is_file() else sum(x.stat().st_size for x in p.rglob('*') if x.is_file())
def human(n):
 for u in ('B','KiB','MiB','GiB','TiB'):
  if n<1024:return f'{n:.1f} {u}'
  n/=1024
 return f'{n:.1f} PiB'
def all_payload_files(base):
 for p in base.rglob('*'):
  if not p.is_file():continue
  if any(part in IGNORED for part in p.relative_to(base).parts):continue
  if p.name=='.gitkeep':continue
  yield p.resolve()
def status(models,base,as_json=False):
 expected,_=expected_set(models,base);rows=[]
 for m in models:
  found=paths_for(m,base);patterns=expected_patterns(m);missing=[]
  for pat in patterns:
   if '*' in str(pat) or '?' in str(pat):
    if not list((base/rel_local(m)).glob(str(pat))):missing.append(str(pat))
   else:
    p=base/rel_local(m)/(Path(str(pat)).name if m.get('flatten') else str(pat))
    if not p.is_file():missing.append(str(pat))
  rows.append({'id':m['id'],'enabled':bool(m.get('enabled')),'directory':str(rel_local(m)),'patterns':patterns,'found_files':len(found),'bytes':sum(size(p) for p in found),'missing':missing,'managed':bool(patterns)})
 orphan=sorted(set(all_payload_files(base))-expected);result={'model_dir':str(base),'models':rows,'orphan_files':[{'path':str(p.relative_to(base)),'bytes':size(p)} for p in orphan],'orphan_bytes':sum(size(p) for p in orphan),'managed_bytes':sum(r['bytes'] for r in rows)}
 if as_json:print(json.dumps(result,indent=2));return result
 print(f"MODEL_DIR {base}\n{'STATE':<9} {'MODEL':<38} {'FILES':>5} {'SIZE':>10} MISSING")
 for r in rows:print(f"{('OK' if r['managed'] and not r['missing'] else 'MISSING' if r['managed'] else 'UNMANAGED'):<9} {r['id']:<38} {r['found_files']:>5} {human(r['bytes']):>10} {','.join(r['missing'])}")
 print(f"\nManaged: {human(result['managed_bytes'])}; unreferenced files: {len(orphan)} ({human(result['orphan_bytes'])})")
 for x in result['orphan_files'][:30]:print(' ORPHAN',human(x['bytes']),x['path'])
 if len(orphan)>30:print(' ...',len(orphan)-30,'more')
 return result
def missing_patterns(m,base):
 dest=base/rel_local(m);missing=[]
 for pat in expected_patterns(m):
  text=str(pat)
  if any(c in text for c in '*?'):
   if not any(x.is_file() for x in dest.glob(text)):missing.append(text)
  else:
   target=dest/(Path(text).name if m.get('flatten') else text)
   if not target.is_file():missing.append(text)
 return missing
def hf_download(m,base,force=False):
 pats=expected_patterns(m)
 if not pats:print('SKIP unmanaged artifact specification:',m['id']);return
 missing=missing_patterns(m,base)
 if not force and not missing:
  print('REUSE',m['id'],'all registered artifacts are present')
  return
 source=m.get('source');
 if not source or '/' not in source:raise RuntimeError(f"{m['id']}: no downloadable Hugging Face source")
 dest=base/rel_local(m);stage=base/'.staging'/m['id'].replace('/','__');shutil.rmtree(stage,ignore_errors=True);stage.mkdir(parents=True,exist_ok=True)
 cmd=['hf','download',source]
 exact=[x for x in pats if '*' not in str(x) and '?' not in str(x)];globs=[x for x in pats if x not in exact]
 cmd += [str(x) for x in exact]
 for g in globs:cmd += ['--include',str(g)]
 cmd += ['--local-dir',str(stage)]
 print('DOWNLOAD',m['id'],source,'->',dest);subprocess.run(cmd,check=True)
 dest.mkdir(parents=True,exist_ok=True)
 for pat in pats:
  matches=list(stage.glob(str(pat))) if any(c in str(pat) for c in '*?') else [stage/str(pat)]
  for src in matches:
   if not src.is_file():continue
   target=dest/src.name if m.get('flatten') else dest/src.relative_to(stage);target.parent.mkdir(parents=True,exist_ok=True);os.replace(src,target)
 shutil.rmtree(stage,ignore_errors=True)
def quarantine(base,models,apply):
 expected,_=expected_set(models,base);orphans=sorted(set(all_payload_files(base))-expected);total=sum(size(p) for p in orphans);stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S');trash=base/'.trash'/stamp
 print(('QUARANTINE' if apply else 'DRY-RUN'),len(orphans),'files',human(total))
 for p in orphans:print(' ',p.relative_to(base))
 if apply:
  for p in orphans:
   target=trash/p.relative_to(base);target.parent.mkdir(parents=True,exist_ok=True);os.replace(p,target)
  manifest={'created':stamp,'bytes':total,'files':[str(p.relative_to(base)) for p in orphans]};trash.mkdir(parents=True,exist_ok=True);(trash/'manifest.json').write_text(json.dumps(manifest,indent=2));print('Moved to',trash)
def purge(base,older,apply):
 trash=base/'.trash';targets=[];now=datetime.datetime.now()
 if trash.exists():
  for d in trash.iterdir():
   if not d.is_dir():continue
   age=(now-datetime.datetime.fromtimestamp(d.stat().st_mtime)).days
   if age>=older:targets.append(d)
 total=sum(size(d) for d in targets);print(('PURGE' if apply else 'DRY-RUN'),len(targets),'quarantines',human(total))
 for d in targets:print(' ',d.name)
 if apply:
  for d in targets:shutil.rmtree(d)
def main():
 p=argparse.ArgumentParser();p.add_argument('--track',default='active',choices=['active','balanced','experimental','staged','all']);p.add_argument('--id',action='append',default=[]);sub=p.add_subparsers(dest='cmd',required=True)
 s=sub.add_parser('status');s.add_argument('--json',action='store_true')
 sync=sub.add_parser('sync');sync.add_argument('--force',action='store_true');q=sub.add_parser('prune');q.add_argument('--apply',action='store_true');u=sub.add_parser('purge');u.add_argument('--older-than-days',type=int,default=14);u.add_argument('--apply',action='store_true')
 a=p.parse_args();base=root_dir();base.mkdir(parents=True,exist_ok=True);models=selected(a.track,a.id)
 if a.cmd=='status':status(models,base,a.json)
 elif a.cmd=='sync':
  if shutil.which('hf') is None:raise SystemExit('Install huggingface_hub CLI: python3 -m pip install -U huggingface_hub')
  for m in models:hf_download(m,base,a.force)
  status(models,base)
 elif a.cmd=='prune':quarantine(base,models,a.apply)
 elif a.cmd=='purge':purge(base,a.older_than_days,a.apply)
if __name__=='__main__':main()
