#!/usr/bin/env python3
"""Read-only verification for ASV1901 Ezra local installed release."""
from pathlib import Path
import json,hashlib,sys,re
import fitz
from jsonschema import Draft202012Validator
COUNT=[11, 70, 13, 24, 17, 22, 28, 36, 15, 44]
NAME='Ezra';CODE='EZR';SLUG='ezra'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(root):
 root=Path(root).resolve();bk=root/'books'/SLUG;data=root/'data/asv1901'/SLUG
 mf=json.loads((bk/'RELEASE_MANIFEST.json').read_text());assert mf['book']==CODE and mf['chapter_count']==len(COUNT) and mf['verse_count']==sum(COUNT)
 for rel,h in mf['files'].items():assert sha(root/rel)==h,rel
 schema=json.loads((bk/'schemas'/('asv1901-'+SLUG+'-chapter.schema.json')).read_text())
 pschema=json.loads((bk/'schemas/facsimile-page-index.schema.json').read_text())
 for ch,n in enumerate(COUNT,1):
  d=json.loads((data/'chapters'/f'{ch:02d}.json').read_text());Draft202012Validator(schema).validate(d);assert len(d['verses'])==n
  for v,row in enumerate(d['verses'],1):assert row['id']==f'{CODE}.{ch}.{v}' and row['edition_verse_id']=='ASV1901:'+row['id']
 idx=json.loads((data/'page-index.json').read_text());Draft202012Validator(pschema).validate(idx)
 assert [p['source_pdf_page'] for p in idx['pages']]==list(range(503,516))
 for vol in idx['volumes']:
  f=data/'facsimile'/vol['filename'];assert f.stat().st_size==vol['bytes'] and sha(f)==vol['sha256']
  with fitz.open(f) as d:assert len(d)==vol['last_source_pdf_page']-vol['first_source_pdf_page']+1
 print(json.dumps({'status':'PASS','book':CODE,'chapters':len(COUNT),'verses':sum(COUNT),'facsimile_pages':len(idx['pages']),'volumes':len(idx['volumes'])},indent=2))
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else '.')
