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
 if kind=='exact-chat':
  ch=d.get('choices',[{}])[0];content=(ch.get('message',{}).get('content') or '').strip();reasoning=ch.get('message',{}).get('reasoning_content')
  if ch.get('finish_reason')!='stop':raise RuntimeError(f'exact-chat finish_reason={ch.get("finish_reason")!r}, expected stop')
  if content!=s['expected']:raise RuntimeError(f'exact-chat content mismatch: expected {s["expected"]!r}, got {content!r}')
  if reasoning:raise RuntimeError('exact-chat returned unexpected reasoning_content')
 elif kind=='python-code':
  ch=d.get('choices',[{}])[0];content=ch.get('message',{}).get('content') or ''
  match=re.search(r'```(?:python)?\s*(.*?)```',content,re.S)
  if not match:raise RuntimeError(f'python-code response has no fenced Python block; response={content[:1000]!r}')
  code=match.group(1);count=code.count('assert ')
  if count!=3:raise RuntimeError(f'python-code expected exactly 3 assert statements, found {count}; code={code[:1500]!r}')
  namespace={}
  try:exec(code,namespace,namespace)
  except Exception as exc:raise RuntimeError(f'python-code execution failed: {type(exc).__name__}: {exc}; code={code[:1500]!r}') from exc
  func=namespace.get('merge_intervals')
  if not callable(func):raise RuntimeError('python-code did not define callable merge_intervals')
  source=[(5,7),(1,3),(2,6)];original=list(source)
  try:actual=func(source)
  except Exception as exc:raise RuntimeError(f'merge_intervals raised {type(exc).__name__}: {exc}') from exc
  if actual!=[(1,7)]:raise RuntimeError(f'merge_intervals returned {actual!r}; expected [(1, 7)]')
  if source!=original:raise RuntimeError(f'merge_intervals mutated input: before={original!r}, after={source!r}')
 elif kind=='bayes-reasoning':
  ch=d['choices'][0];content=plain(ch['message'].get('content') or '')
  if ch['finish_reason']!='stop' or not content or d['usage']['completion_tokens']>=1536:raise RuntimeError('bayes-reasoning did not produce a complete final answer within the token limit')
  if not re.search(r'(?<!\d)10\s*/\s*21(?!\d)',content) or not re.search(r'47(?:\.6(?:19|2)?)?\s*%',content):raise RuntimeError(f'bayes-reasoning final answer is incorrect: {content[:1200]!r}')
  if re.search(r'(?<!\d)5\s*/\s*42(?!\d)',content):raise RuntimeError('bayes-reasoning contains known incorrect answer 5/42')
 elif kind=='vision-shape':
  content=(d['choices'][0]['message'].get('content') or '').lower()
  if 'red' not in content or not ('square' in content or 'rectangle' in content):raise RuntimeError(f'vision-shape did not identify a red square/rectangle: {content[:1000]!r}')
 elif kind=='embedding-similarity':
  vectors=[x['embedding'] for x in d['data']]
  if len(vectors)!=3 or len({len(x) for x in vectors})!=1 or not all(math.isfinite(n) for x in vectors for n in x):raise RuntimeError('embedding response has invalid vectors')
  if cos(vectors[0],vectors[1])<=cos(vectors[0],vectors[2]):raise RuntimeError('embedding semantic ordering failed')
 elif kind=='rerank':
  rows=d.get('results',d.get('data'))
  if not rows or len(rows)<2:raise RuntimeError('rerank returned fewer than 2 results')
  scores={x.get('index',i):x.get('relevance_score',x.get('score')) for i,x in enumerate(rows)}
  if not all(math.isfinite(x) for x in scores.values()):raise RuntimeError(f'rerank returned invalid scores: {scores!r}')
  if scores[0]<=scores[1]:raise RuntimeError(f'rerank ordering failed: {scores!r}')
def error_message(body):
 try:
  d=json.loads(body);return d.get('error',{}).get('message') or d.get('message') or str(d)
 except:return body.decode(errors='replace')[:1000]
def save_result(model,spec_id,kind,status,elapsed,before,loaded,running,after,data,passed,error=None):
 result={'model':model,'spec_id':spec_id,'kind':kind,'status':status,'passed':passed,'error':error,'wall_seconds':round(elapsed,3),'before':before,'loaded':loaded,'running_loaded':running,'running_after':after,'effective_policy':{k:os.environ.get(k) for k in ('HEAVY_HOST_RESERVE_GB','LIGHT_HOST_RESERVE_GB','GPU_FIT_TARGET_MIB','MIN_FIT_CONTEXT','GLOBAL_CONCURRENCY_LIMIT','PROTOCOL_UNLOAD_WAIT_SECONDS','PROTOCOL_MEMORY_RETURN_TOLERANCE_GIB')},'response':data}
 out=ROOT/'benchmark-results'/f"{model.replace('/','__')}-{time.strftime('%Y%m%d-%H%M%S')}.json";out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(result,indent=2));return out,result
def main():
 p=argparse.ArgumentParser();p.add_argument('model');p.add_argument('--spec-id');p.add_argument('--base',required=True);p.add_argument('--key',required=True);a=p.parse_args();spec_id=a.spec_id or a.model;spec=yaml.safe_load((ROOT/'tests/models.yaml').read_text())['tests'][spec_id];kind=spec['kind'];unload(a.base,a.key);before=metrics(a.base,a.key);start=time.monotonic();st=0;data={};loaded={};running={'running':[]};after={'running':[]};error=None
 try:
  if kind in {'exact-chat','python-code','bayes-reasoning','vision-shape'}:st,b,_=chat(a.base,a.key,a.model,spec);data=json.loads(b)
  elif kind=='embedding-similarity':st,b,_=request(a.base,a.key,'/v1/embeddings',{'model':a.model,'input':spec['inputs']});data=json.loads(b)
  elif kind=='rerank':st,b,_=request(a.base,a.key,'/v1/rerank',{'model':a.model,'query':spec['query'],'documents':spec['documents']});data=json.loads(b)
  elif kind=='tts':
   st,b,_=request(a.base,a.key,'/v1/audio/speech',{'model':a.model,'input':spec['text'],'voice':spec['voice']})
   if st!=200:raise RuntimeError(f'TTS HTTP {st}: {error_message(b)}')
   if b[:4]!=b'RIFF':raise RuntimeError(f'TTS returned non-WAV payload: {b[:120]!r}')
   wav=ROOT/'tests/fixtures/local-speech-recognition-test.wav';wav.write_bytes(b);w=wave.open(str(wav));frames=w.readframes(w.getnframes());duration=w.getnframes()/w.getframerate();width=w.getsampwidth();
   if duration<=.3:raise RuntimeError(f'TTS audio is too short: {duration:.3f} seconds')
   if width not in (1,2,4):raise RuntimeError(f'TTS unsupported sample width: {width}')
   fmt={1:'b',2:'h',4:'i'}[width];count=len(frames)//width;vals=struct.unpack('<'+fmt*count,frames);rms=math.sqrt(sum(v*v for v in vals)/max(1,count))
   if rms<=10:raise RuntimeError(f'TTS audio is silent or too quiet: RMS={rms}')
   data={'fixture':str(wav),'seconds':duration,'rms':rms}
  elif kind=='transcription':
   fixture=ROOT/spec['fixture']
   if not fixture.exists():raise RuntimeError(f'STT fixture missing: {fixture}; run speech/kokoro first')
   st,b,_=multipart(a.base,a.key,'/v1/audio/transcriptions',{'model':a.model},'file',fixture)
   if st!=200:raise RuntimeError(f'STT HTTP {st}: {error_message(b)}')
   data=json.loads(b);text=re.sub(r'[^a-z ]',' ',(data.get('text') or '').lower());missing=[w for w in spec['expected_words'] if w not in text]
   if missing:raise RuntimeError(f'STT transcript missing words {missing}; transcript={data.get("text")!r}')
  loaded=metrics(a.base,a.key);_,raw_running,_=request(a.base,a.key,'/running');running=json.loads(raw_running)
  # Save the raw response before semantic validation so failures remain inspectable.
  elapsed=time.monotonic()-start;save_result(a.model,spec_id,kind,st,elapsed,before,loaded,running,{'running':[]},data,False,'semantic validation pending')
  if kind in {'exact-chat','python-code','bayes-reasoning','vision-shape','embedding-similarity','rerank'}:validate(kind,data,spec)
 except Exception as exc:
  error=f'{type(exc).__name__}: {exc}'
  raise
 finally:
  elapsed=time.monotonic()-start
  if not loaded:loaded=metrics(a.base,a.key)
  try:
   _,raw_running,_=request(a.base,a.key,'/running');running=json.loads(raw_running)
  except Exception:pass
  try:
   unload(a.base,a.key);_,raw_after,_=request(a.base,a.key,'/running');after=json.loads(raw_after)
  except Exception as exc:
   after={'error':f'{type(exc).__name__}: {exc}'}
  passed=error is None and not after.get('running',[])
  out,result=save_result(a.model,spec_id,kind,st,elapsed,before,loaded,running,after,data,passed,error)
  print(json.dumps({k:v for k,v in result.items() if k!='response'},indent=2));print(('PASS' if passed else 'FAIL'),a.model,'result:',out)
if __name__=='__main__':main()
