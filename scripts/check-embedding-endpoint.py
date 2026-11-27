#!/usr/bin/env python3
"""Validate the configured OpenAI-compatible RAG embedding model."""
from pathlib import Path
import argparse,json,math,os,re,sys,urllib.error,urllib.request
ROOT=Path(__file__).resolve().parents[1]
def env_file():
 out={}
 for name in ('.env.example','.env'):
  p=ROOT/name
  if not p.exists():continue
  for line in p.read_text().splitlines():
   if line.strip() and not line.lstrip().startswith('#') and '=' in line:
    k,v=line.split('=',1);out[k]=v.strip().strip('"').strip("'")
 return out
def call(base,key,path,body=None):
 data=json.dumps(body).encode() if body is not None else None
 headers={'Authorization':'Bearer '+key}
 if data:headers['Content-Type']='application/json'
 q=urllib.request.Request(base+path,data=data,headers=headers)
 try:
  with urllib.request.urlopen(q,timeout=600) as r:return r.status,json.loads(r.read())
 except urllib.error.HTTPError as e:
  raw=e.read();
  try:payload=json.loads(raw)
  except:payload={'raw':raw.decode(errors='replace')}
  return e.code,payload
def cos(a,b):return sum(x*y for x,y in zip(a,b))/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)))
def main():
 p=argparse.ArgumentParser();p.add_argument('--model');p.add_argument('--base');p.add_argument('--key');p.add_argument('--discovery-only',action='store_true');a=p.parse_args();v={**env_file(),**os.environ};model=a.model or v.get('RAG_EMBEDDING_MODEL','');key=a.key or v.get('AI_API_KEY','');bind=v.get('AI_BIND','127.0.0.1');bind='127.0.0.1' if bind in ('0.0.0.0','::') else bind;base=a.base or f"http://{bind}:{v.get('AI_PORT','9292')}"
 if not model:raise SystemExit('RAG_EMBEDDING_MODEL is missing')
 if model.startswith('aistation.'):
  raise SystemExit(f"Invalid provider-qualified model ID: {model!r}. Use 'retrieval/embedding'.")
 if model!='retrieval/embedding':print(f'NOTICE: validating non-reference embedding model {model!r}',file=sys.stderr)
 if not key:raise SystemExit('AI_API_KEY is missing')
 status,catalog=call(base,key,'/v1/models')
 if status!=200:raise SystemExit(f'/v1/models HTTP {status}: {catalog}')
 ids={row.get('id') for row in catalog.get('data',[])}
 if model not in ids:
  similar=sorted(x for x in ids if x and 'embedding' in x.lower())
  raise SystemExit(f"Configured model {model!r} is not advertised. Embedding candidates: {similar}")
 print(f'DISCOVERY PASS model={model}')
 if a.discovery_only:return
 inputs=['A domestic cat rests on a sofa.','A kitten sleeps on a couch.','PostgreSQL database schema migration.']
 status,data=call(base,key,'/v1/embeddings',{'model':model,'input':inputs})
 if status!=200:
  message=data.get('error',{}).get('message',data)
  raise SystemExit(f'/v1/embeddings HTTP {status}: {message}')
 rows=sorted(data.get('data',[]),key=lambda x:x.get('index',-1));vectors=[x.get('embedding',[]) for x in rows]
 if len(vectors)!=3 or not vectors[0] or len({len(x) for x in vectors})!=1:raise SystemExit('Invalid vector response')
 near=cos(vectors[0],vectors[1]);far=cos(vectors[0],vectors[2])
 if near<=far:raise SystemExit(f'Semantic ordering failed: related={near:.6f}, unrelated={far:.6f}')
 print(f'EMBEDDING PASS vectors=3 dimensions={len(vectors[0])} related={near:.6f} unrelated={far:.6f}')
if __name__=='__main__':main()
