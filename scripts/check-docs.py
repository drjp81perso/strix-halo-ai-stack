#!/usr/bin/env python3
"""Check common simplified-technical-English and repository documentation rules."""
from pathlib import Path
import re,sys,yaml
ROOT=Path(__file__).resolve().parents[1]
files=[ROOT/'README.md',ROOT/'CONTRIBUTING.md',ROOT/'SECURITY.md',ROOT/'CODE_OF_CONDUCT.md']+sorted((ROOT/'docs').glob('*.md'))+sorted((ROOT/'profiles').glob('*.md'))+sorted((ROOT/'registry').glob('*.md'))
errors=[];warnings=[]
for p in files:
 text=p.read_text(encoding='utf-8');rel=p.relative_to(ROOT)
 if not text.startswith('# '):errors.append(f'{rel}: missing level-1 title')
 # Remove code blocks before prose checks.
 prose=re.sub(r'```[\s\S]*?```','',text)
 for token,replacement in ((r"\bcan't\b",'cannot'),(r"\bdon't\b",'do not'),(r"\bdoesn't\b",'does not'),(r"\bwon't\b",'will not'),(r"\be\.g\.\b",'for example'),(r"\bi\.e\.\b",'that is')):
  for m in re.finditer(token,prose,re.I):errors.append(f'{rel}: use {replacement!r} instead of {m.group(0)!r}')
 # Flag likely long prose lines. Tables, links, HTML and headings are exempt.
 for n,line in enumerate(prose.splitlines(),1):
  s=line.strip()
  if not s or s.startswith(('#','|','- ','* ','>','[','<')) or re.match(r'^\d+\. ',s):continue
  words=re.findall(r"\b[\w'-]+\b",s)
  if len(words)>35:warnings.append(f'{rel}:{n}: long prose line ({len(words)} words)')
 # Check local Markdown links.
 for target in re.findall(r'\[[^]]+\]\(([^)]+)\)',text):
  if re.match(r'^(https?://|mailto:|#)',target):continue
  clean=target.split('#',1)[0]
  if clean and not (p.parent/clean).resolve().exists():errors.append(f'{rel}: broken local link {target}')
print(f'DOCS checked={len(files)} errors={len(errors)} warnings={len(warnings)}')
for x in errors:print('ERROR',x)
for x in warnings[:50]:print('WARN ',x)
if len(warnings)>50:print('WARN ',len(warnings)-50,'more long lines')
if errors:raise SystemExit(1)
