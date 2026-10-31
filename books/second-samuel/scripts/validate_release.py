#!/usr/bin/env python3
"""Independent ASV1901 2 Samuel book-distribution validator."""
from pathlib import Path
import json,hashlib,re,sys
from jsonschema import Draft202012Validator
import fitz
COUNTS=[27, 32, 39, 12, 25, 23, 29, 18, 13, 19, 27, 31, 39, 33, 37, 23, 29, 33, 43, 26, 22, 51, 39, 25]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pos(r):
 assert re.fullmatch(r'2SA\.[1-9][0-9]*\.[1-9][0-9]*',r),r
 return tuple(map(int,r.split('.')[1:]))
def run(root):
 root=Path(root).resolve();book=root/'books/second-samuel';data=root/'data/asv1901/second-samuel'
 mf=json.loads((book/'RELEASE_MANIFEST.json').read_text());assert mf['book']=='2SA' and mf['chapter_count']==24 and mf['verse_count']==695
 for rel,h in mf['files'].items():
  p=root/rel; assert p.is_file() and sha(p)==h,('Missing or altered',rel)
 schema=json.loads((book/'schemas/asv1901-second-samuel-chapter.schema.json').read_text());iscr=json.loads((book/'schemas/facsimile-page-index.schema.json').read_text())
 refs=set();italic=0
 for ch,num in enumerate(COUNTS,1):
  obj=json.loads((data/'chapters'/f'{ch:02d}.json').read_text());Draft202012Validator(schema).validate(obj)
  assert obj['edition_id']=='ASV1901' and obj['book_code']=='2SA' and obj['chapter']==ch and len(obj['verses'])==num
  for vnum,row in enumerate(obj['verses'],1):
   ref=f'2SA.{ch}.{vnum}'; assert row['id']==ref and row['edition_verse_id']=='ASV1901:'+ref and row['verse']==vnum and ref not in refs
   assert row['spans'] and all(s['text'] and s['kind'] in ('text','supplied') for s in row['spans'])
   refs.add(ref); italic+=sum(s['kind']=='supplied' for s in row['spans'])
 assert len(refs)==695 and italic==76
 index=json.loads((data/'page-index.json').read_text());Draft202012Validator(iscr).validate(index)
 pages=index['pages'];assert [x['source_pdf_page'] for x in pages]==list(range(338,367))
 assert all(p['type']=='scripture' for p in pages) and [p['printed_page'] for p in pages]==list(range(304,333))
 assert len(index['volumes'])==2
 for vol in index['volumes']:
  f=data/'facsimile'/vol['filename'];assert f.is_file() and f.stat().st_size==vol['bytes'] and sha(f)==vol['sha256']
  with fitz.open(f) as pdf:assert len(pdf)==vol['last_source_pdf_page']-vol['first_source_pdf_page']+1
 for page in pages:
  assert pos(page['first_verse'])<=pos(page['last_verse'])
  assert page['volume'] and page['volume_pdf_page']>=1
 pairs={}
 for ref in refs:
  hits=[p['source_pdf_page'] for p in pages if pos(p['first_verse'])<=pos(ref)<=pos(p['last_verse'])]
  assert 1<=len(hits)<=2,(ref,hits)
  if len(hits)==2:pairs[ref]=hits
 assert len(pairs)==27 and pairs.get('2SA.18.3')==[356,357]
 assert pairs==json.loads((book/'build-inputs/spanning-verses.json').read_text())['verse_page_pairs']
 catalog=json.loads((root/'data/asv1901/catalog-second-samuel.json').read_text())
 assert catalog['book_code']=='2SA' and catalog['chapter_count']==24 and catalog['verse_count']==695
 assert catalog['reader']=='books/second-samuel/site/index.html'
 print(json.dumps({'status':'PASS','book':'2SA','chapters':24,'verses':695,'italic_spans':76,'historical_pages':29,'two_page_verses':27,'pdf_volumes':2,'hashed_files':len(mf['files'])},indent=2))
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else '.')
