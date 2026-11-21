#!/usr/bin/env python3
from pathlib import Path
import argparse,base64,json,math,mimetypes,os,re,struct,sys,time,urllib.request,urllib.error,uuid,wave,yaml
ROOT=Path(__file__).resolve().parents[1]
def plain(s):
 s=re.sub(r'\\(?:d|t)?frac\s*\{\s*([^{}]+?)\s*\}\s*\{\s*([^{}]+?)\s*\}',lambda m:f'{m.group(1).strip()}/{m.group(2).strip()}',s)
 return s.replace(r'\%','%').replace('$$','').replace('$','').replace(r'\(','').replace(r'\)','').replace(r'\[','').replace(r'\]','')
def request(base,key,path,body=None,method=None,timeout=1800,headers=None):
 h={'Authorization':f'Bearer {key}',**(headers or {})};data=None
 if body is not None:data=json.dumps(body).encode();h['Content-Type']='application/json'
 q=urllib.request.Request(base+path,data=data,headers=h,method=method or ('POST' if body is not None else 'GET'))
 try:
  with urllib.request.urlopen(q,timeout=timeout) as r:return r.status,r.read(),dict(r.headers)
 except urllib.error.HTTPError as e:return e.code,e.read(),dict(e.headers)
def multipart(base,key,path,fields,file_field,file_path,timeout=1800):
 boundary='----localai'+uuid.uuid4().hex;chunks=[]
 for k,v in fields.items():chunks += [f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()]
 mime=mimetypes.guess_type(file_path.name)[0] or 'application/octet-stream';chunks += [f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\nContent-Type: {mime}\r\n\r\n'.encode(),file_path.read_bytes(),b'\r\n',f'--{boundary}--\r\n'.encode()];data=b''.join(chunks)
 q=urllib.request.Request(base+path,data=data,headers={'Authorization':f'Bearer {key}','Content-Type':f'multipart/form-data; boundary={boundary}'},method='POST')
 try:
  with urllib.request.urlopen(q,timeout=timeout) as r:return r.status,r.read(),dict(r.headers)
 except urllib.error.HTTPError as e:return e.code,e.read(),dict(e.headers)
def metrics(base,key):
 st,b,_=request(base,key,'/metrics',timeout=30);out={}
 if st==200:
  for line in b.decode().splitlines():
   if line.startswith('llamaswap_'):
    try:out[line.split('{')[0].split()[0]]=float(line.rsplit(' ',1)[1])
    except ValueError:pass
 return out
def unload(base,key):request(base,key,'/api/models/unload',method='POST');time.sleep(float(os.environ.get('PROTOCOL_UNLOAD_WAIT_SECONDS','4')))
def chat(base,key,mid,spec):
 content=spec['prompt']
 if 'fixture' in spec:
  enc=base64.b64encode((ROOT/spec['fixture']).read_bytes()).decode();content=[{'type':'text','text':content},{'type':'image_url','image_url':{'url':f'data:image/png;base64,{enc}'}}]
 return request(base,key,'/v1/chat/completions',{'model':mid,'messages':[{'role':'user','content':content}],'temperature':0,'max_tokens':spec['max_tokens'],'stream':False})
def cos(a,b):return sum(x*y for x,y in zip(a,b))/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)))
def validate(kind,d,s):
 if kind=='exact-chat':assert d['choices'][0]['finish_reason']=='stop' and d['choices'][0]['message'].get('content','').strip()==s['expected'] and not d['choices'][0]['message'].get('reasoning_content')
 elif kind=='python-code':
  c=d['choices'][0]['message']['content'];m=re.search(r'```(?:python)?\s*(.*?)```',c,re.S);assert m;code=m.group(1);assert code.count('assert ')==3;ns={};exec(code,ns,ns);f=ns['merge_intervals'];src=[(5,7),(1,3),(2,6)];cp=list(src);assert f(src)==[(1,7)] and src==cp
 elif kind=='bayes-reasoning':
  ch=d['choices'][0];c=plain(ch['message'].get('content') or '');assert ch['finish_reason']=='stop' and c and d['usage']['completion_tokens']<1536;assert re.search(r'(?<!\d)10\s*/\s*21(?!\d)',c) and re.search(r'47(?:\.6(?:19|2)?)?\s*%',c);assert not re.search(r'(?<!\d)5\s*/\s*42(?!\d)',c)
 elif kind=='vision-shape':c=d['choices'][0]['message'].get('content','').lower();assert 'red' in c and ('square' in c or 'rectangle' in c)
 elif kind=='embedding-similarity':v=[x['embedding'] for x in d['data']];assert len(v)==3 and len({len(x) for x in v})==1 and all(math.isfinite(n) for x in v for n in x) and cos(v[0],v[1])>cos(v[0],v[2])
 elif kind=='rerank':r=d.get('results',d.get('data'));assert len(r)>=2;by={x.get('index',i):x.get('relevance_score',x.get('score')) for i,x in enumerate(r)};assert all(math.isfinite(x) for x in by.values()) and by[0]>by[1]
def error_message(body):
 try:
  d=json.loads(body);return d.get('error',{}).get('message') or d.get('message') or str(d)
 except:return body.decode(errors='replace')[:1000]
def main():
 p=argparse.ArgumentParser();p.add_argument('model');p.add_argument('--spec-id');p.add_argument('--base',required=True);p.add_argument('--key',required=True);a=p.parse_args();spec_id=a.spec_id or a.model;spec=yaml.safe_load((ROOT/'tests/models.yaml').read_text())['tests'][spec_id];kind=spec['kind'];unload(a.base,a.key);before=metrics(a.base,a.key);start=time.monotonic()
 if kind in {'exact-chat','python-code','bayes-reasoning','vision-shape'}:st,b,_=chat(a.base,a.key,a.model,spec);data=json.loads(b);validate(kind,data,spec)
 elif kind=='embedding-similarity':st,b,_=request(a.base,a.key,'/v1/embeddings',{'model':a.model,'input':spec['inputs']});data=json.loads(b);validate(kind,data,spec)
 elif kind=='rerank':st,b,_=request(a.base,a.key,'/v1/rerank',{'model':a.model,'query':spec['query'],'documents':spec['documents']});data=json.loads(b);validate(kind,data,spec)
 elif kind=='tts':
  st,b,_=request(a.base,a.key,'/v1/audio/speech',{'model':a.model,'input':spec['text'],'voice':spec['voice']})
  if st!=200:raise RuntimeError(f'TTS HTTP {st}: {error_message(b)}')
  if b[:4]!=b'RIFF':raise RuntimeError(f'TTS returned non-WAV payload: {b[:120]!r}')
  out=ROOT/'tests/fixtures/local-speech-recognition-test.wav';out.write_bytes(b);w=wave.open(str(out));frames=w.readframes(w.getnframes());assert w.getnframes()/w.getframerate()>.3;width=w.getsampwidth();assert width in (1,2,4);fmt={1:'b',2:'h',4:'i'}[width];count=len(frames)//width;vals=struct.unpack('<'+fmt*count,frames);assert math.sqrt(sum(v*v for v in vals)/max(1,count))>10;data={'fixture':str(out),'seconds':w.getnframes()/w.getframerate()}
 elif kind=='transcription':
  fixture=ROOT/spec['fixture']
  if not fixture.exists():raise RuntimeError(f'STT fixture missing: {fixture}; run speech/kokoro first')
  st,b,_=multipart(a.base,a.key,'/v1/audio/transcriptions',{'model':a.model},'file',fixture)
  if st!=200:raise RuntimeError(f'STT HTTP {st}: {error_message(b)}')
  data=json.loads(b);text=re.sub(r'[^a-z ]',' ',(data.get('text') or '').lower());missing=[w for w in spec['expected_words'] if w not in text]
  if missing:raise RuntimeError(f'STT transcript missing words {missing}; transcript={data.get("text")!r}')
 elapsed=time.monotonic()-start;loaded=metrics(a.base,a.key);_,running,_=request(a.base,a.key,'/running');unload(a.base,a.key);_,after,_=request(a.base,a.key,'/running');assert not json.loads(after)['running'];result={'model':a.model,'spec_id':spec_id,'kind':kind,'status':st,'passed':True,'wall_seconds':round(elapsed,3),'before':before,'loaded':loaded,'running_loaded':json.loads(running),'running_after':json.loads(after),'effective_policy':{k:os.environ.get(k) for k in ('HEAVY_HOST_RESERVE_GB','LIGHT_HOST_RESERVE_GB','GPU_FIT_TARGET_MIB','MIN_FIT_CONTEXT','GLOBAL_CONCURRENCY_LIMIT','PROTOCOL_UNLOAD_WAIT_SECONDS','PROTOCOL_MEMORY_RETURN_TOLERANCE_GIB')},'response':data};out=ROOT/'benchmark-results'/f"{a.model.replace('/','__')}-{time.strftime('%Y%m%d-%H%M%S')}.json";out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='response'},indent=2));print('PASS',a.model,'result:',out)
if __name__=='__main__':main()
