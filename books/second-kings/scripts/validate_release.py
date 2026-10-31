#!/usr/bin/env python3
"""Validate all ASV1901 2 Kings release files without changing them."""
from pathlib import Path
import json,hashlib,re,sys
from jsonschema import Draft202012Validator
import fitz
COUNTS=[18, 25, 27, 44, 27, 33, 20, 29, 37, 36, 21, 21, 25, 29, 38, 20, 41, 37, 37, 21, 26, 20, 37, 20, 30]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pos(r):
 assert re.fullmatch(r'2KI\.[1-9][0-9]*\.[1-9][0-9]*',r),r
 return tuple(map(int,r.split('.')[1:]))
def run(root):
 root=Path(root).resolve();book=root/'books/second-kings';data=root/'data/asv1901/second-kings'
 mf=json.loads((book/'RELEASE_MANIFEST.json').read_text());assert mf['book']=='2KI' and mf['chapter_count']==25 and mf['verse_count']==719
 for rel,h in mf['files'].items():
  p=root/rel;assert p.is_file() and sha(p)==h,('Missing or altered',rel)
 schema=json.loads((book/'schemas/asv1901-second-kings-chapter.schema.json').read_text());iscr=json.loads((book/'schemas/facsimile-page-index.schema.json').read_text())
 refs=set();italic=0
 for ch,num in enumerate(COUNTS,1):
  obj=json.loads((data/'chapters'/f'{ch:02d}.json').read_text());Draft202012Validator(schema).validate(obj)
  assert obj['edition_id']=='ASV1901' and obj['book_code']=='2KI' and obj['chapter']==ch and len(obj['verses'])==num
  for vnum,row in enumerate(obj['verses'],1):
   ref=f'2KI.{ch}.{vnum}'
   assert row['id']==ref and row['edition_verse_id']=='ASV1901:'+ref and row['verse']==vnum and ref not in refs
   assert row['spans'] and all(s['text'] and s['kind'] in ('text','supplied') for s in row['spans'])
   refs.add(ref);italic+=sum(s['kind']=='supplied' for s in row['spans'])
 assert len(refs)==719 and italic==67
 index=json.loads((data/'page-index.json').read_text());Draft202012Validator(iscr).validate(index)
 pages=index['pages'];assert [p['source_pdf_page'] for p in pages]==list(range(400,436))
 script=[p for p in pages if p['type']=='scripture'];assert len(script)==32 and [p['printed_page'] for p in script]==list(range(366,398))
 assert [p['source_pdf_page'] for p in pages if p['type']=='map']==[401,421]
 assert [p['source_pdf_page'] for p in pages if p['type']=='interleaf']==[402,422]
 assert len(index['volumes'])==2
 for vol in index['volumes']:
  f=data/'facsimile'/vol['filename'];assert f.is_file() and f.stat().st_size==vol['bytes'] and sha(f)==vol['sha256']
  with fitz.open(f) as pdf:assert len(pdf)==vol['last_source_pdf_page']-vol['first_source_pdf_page']+1
 for p in script:
  assert pos(p['first_verse'])<=pos(p['last_verse'])
  assert p['volume'] and p['volume_pdf_page']>=1
 pairs={}
 for ref in refs:
  hits=[p['source_pdf_page'] for p in script if pos(p['first_verse'])<=pos(ref)<=pos(p['last_verse'])]
  assert 1<=len(hits)<=2,(ref,hits)
  if len(hits)==2:pairs[ref]=hits
 assert len(pairs)==27 and pairs.get('2KI.16.13')==[420,423] and pairs.get('2KI.23.15')==[431,432]
 assert pairs==json.loads((book/'build-inputs/spanning-verses.json').read_text())['verse_page_pairs']
 catalog=json.loads((root/'data/asv1901/catalog-second-kings.json').read_text())
 assert catalog['book_code']=='2KI' and catalog['chapter_count']==25 and catalog['verse_count']==719
 assert catalog['reader']=='books/second-kings/site/index.html'
 print(json.dumps({'status':'PASS','book':'2KI','chapters':25,'verses':719,'italic_spans':67,'historical_pages':36,'two_page_verses':27,'pdf_volumes':2,'hashed_files':len(mf['files'])},indent=2))
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else '.')
