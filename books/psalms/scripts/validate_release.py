#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,sys
import fitz
from jsonschema import Draft202012Validator
COUNT=[6, 12, 8, 8, 12, 10, 17, 9, 20, 18, 7, 8, 6, 7, 5, 11, 15, 50, 14, 9, 13, 31, 6, 10, 22, 12, 14, 9, 11, 12, 24, 11, 22, 22, 28, 12, 40, 22, 13, 17, 13, 11, 5, 26, 17, 11, 9, 14, 20, 23, 19, 9, 6, 7, 23, 13, 11, 11, 17, 12, 8, 12, 11, 10, 13, 20, 7, 35, 36, 5, 24, 20, 28, 23, 10, 12, 20, 72, 13, 19, 16, 8, 18, 12, 13, 17, 7, 18, 52, 17, 16, 15, 5, 23, 11, 13, 12, 9, 9, 5, 8, 28, 22, 35, 45, 48, 43, 13, 31, 7, 10, 10, 9, 8, 18, 19, 2, 29, 176, 7, 8, 9, 4, 8, 5, 6, 5, 6, 8, 8, 3, 18, 3, 3, 21, 26, 9, 8, 24, 13, 10, 7, 12, 15, 21, 10, 20, 14, 9, 6];CODE='PSA';SLUG='psalms'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(root):
 root=Path(root);bk=root/'books'/SLUG;data=root/'data/asv1901'/SLUG
 mf=json.loads((bk/'RELEASE_MANIFEST.json').read_text());assert mf['book']==CODE and mf['chapter_count']==len(COUNT) and mf['verse_count']==sum(COUNT)
 for rel,h in mf['files'].items():assert sha(root/rel)==h,rel
 schema=json.loads((bk/'schemas'/f'asv1901-{SLUG}-chapter.schema.json').read_text())
 pschema=json.loads((bk/'schemas/facsimile-page-index.schema.json').read_text())
 for ch,n in enumerate(COUNT,1):
  d=json.loads((data/'chapters'/f'{ch:02d}.json').read_text());Draft202012Validator(schema).validate(d);assert len(d['verses'])==n
  for v,entry in enumerate(d['verses'],1):assert entry['id']==f'{CODE}.{ch}.{v}' and entry['edition_verse_id']=='ASV1901:'+entry['id']
 idx=json.loads((data/'page-index.json').read_text());Draft202012Validator(pschema).validate(idx)
 assert [p['source_pdf_page'] for p in idx['pages']]==list(range(580,671))
 for vol in idx['volumes']:
  p=data/'facsimile'/vol['filename'];assert p.stat().st_size==vol['bytes'] and sha(p)==vol['sha256']
  with fitz.open(p) as dd:assert len(dd)==vol['last_source_pdf_page']-vol['first_source_pdf_page']+1
 print(json.dumps({'status':'PASS','book':CODE,'chapters':len(COUNT),'verses':sum(COUNT),'pages':len(idx['pages'])},indent=2))
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else '.')
