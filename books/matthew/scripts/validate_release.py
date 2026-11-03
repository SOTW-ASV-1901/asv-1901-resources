#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,sys
import fitz
from jsonschema import Draft202012Validator
OMIT={(17,21),(18,11),(23,14)}
COUNT=[25, 23, 17, 25, 48, 34, 29, 34, 38, 42, 30, 50, 58, 36, 39, 28, 27, 35, 30, 34, 46, 46, 39, 51, 46, 75, 66, 20];CODE='MAT';SLUG='matthew'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(root):
 root=Path(root);bk=root/'books'/SLUG;data=root/'data/asv1901'/SLUG
 mf=json.loads((bk/'RELEASE_MANIFEST.json').read_text());assert mf['book']==CODE and mf['chapter_count']==len(COUNT) and mf['verse_count']==sum(COUNT)-len(OMIT)
 for rel,h in mf['files'].items():assert sha(root/rel)==h,rel
 schema=json.loads((bk/'schemas'/f'asv1901-{SLUG}-chapter.schema.json').read_text())
 pschema=json.loads((bk/'schemas/facsimile-page-index.schema.json').read_text())
 for ch,n in enumerate(COUNT,1):
  d=json.loads((data/'chapters'/f'{ch:02d}.json').read_text());Draft202012Validator(schema).validate(d);assert len(d['verses'])==n-sum(c==ch for c,v in OMIT)
  for entry in d['verses']:
   v=entry['verse'];assert (ch,v) not in OMIT and entry['id']==f'{CODE}.{ch}.{v}' and entry['edition_verse_id']=='ASV1901:'+entry['id']
 idx=json.loads((data/'page-index.json').read_text());Draft202012Validator(pschema).validate(idx)
 assert [p['source_pdf_page'] for p in idx['pages']]==list(range(976,1011))
 for vol in idx['volumes']:
  p=data/'facsimile'/vol['filename'];assert p.stat().st_size==vol['bytes'] and sha(p)==vol['sha256']
  with fitz.open(p) as dd:assert len(dd)==vol['last_source_pdf_page']-vol['first_source_pdf_page']+1
 print(json.dumps({'status':'PASS','book':CODE,'chapters':len(COUNT),'verses':sum(COUNT)-len(OMIT),'pages':len(idx['pages'])},indent=2))
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else '.')
