#!/usr/bin/env python3
"""Validate the published standalone ASV1901 Second Chronicles release (read only)."""
from pathlib import Path
import json,hashlib,re,sys
from jsonschema import Draft202012Validator
import fitz
COUNTS=[17, 18, 17, 22, 14, 42, 22, 18, 31, 19, 23, 16, 22, 15, 19, 14, 19, 34, 11, 37, 20, 12, 21, 27, 28, 23, 9, 27, 36, 27, 21, 33, 25, 33, 27, 23]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def pos(s):
 assert re.fullmatch(r'2CH\.[1-9][0-9]*\.[1-9][0-9]*',s),s
 return tuple(map(int,s.split('.')[1:]))
def run(root):
 root=Path(root).resolve();book=root/'books/second-chronicles';data=root/'data/asv1901/second-chronicles'
 mf=json.loads((book/'RELEASE_MANIFEST.json').read_text());assert mf['book']=='2CH' and mf['chapter_count']==36 and mf['verse_count']==822
 for rel,h in mf['files'].items():
  p=root/rel;assert p.is_file() and sha(p)==h,('missing or altered',rel)
 schema=json.loads((book/'schemas/asv1901-second-chronicles-chapter.schema.json').read_text())
 pschema=json.loads((book/'schemas/facsimile-page-index.schema.json').read_text())
 refs=set();italic=0
 for ch,num in enumerate(COUNTS,1):
  obj=json.loads((data/'chapters'/f'{ch:02d}.json').read_text());Draft202012Validator(schema).validate(obj)
  assert obj['edition_id']=='ASV1901' and obj['book_code']=='2CH' and obj['chapter']==ch and len(obj['verses'])==num
  for vnum,row in enumerate(obj['verses'],1):
   ref=f'2CH.{ch}.{vnum}'
   assert row['id']==ref and row['edition_verse_id']=='ASV1901:'+ref and row['verse']==vnum and ref not in refs
   assert row['spans'] and all(s['text'] and s['kind'] in ('text','supplied') for s in row['spans'])
   refs.add(ref);italic+=sum(s['kind']=='supplied' for s in row['spans'])
 assert len(refs)==822 and italic==118
 index=json.loads((data/'page-index.json').read_text());Draft202012Validator(pschema).validate(index)
 pages=index['pages'];assert len(pages)==37 and [p['source_pdf_page'] for p in pages]==list(range(466,503))
 assert all(p['type']=='scripture' for p in pages)
 assert [p['printed_page'] for p in pages]==list(range(428,465))
 assert len(index['volumes'])==2
 for vol in index['volumes']:
  f=data/'facsimile'/vol['filename'];assert f.is_file() and f.stat().st_size==vol['bytes'] and sha(f)==vol['sha256']
  with fitz.open(f) as pdf:assert len(pdf)==vol['last_source_pdf_page']-vol['first_source_pdf_page']+1
 for p in pages:
  assert pos(p['first_verse'])<=pos(p['running_head_first_verse'])<=pos(p['last_verse'])
  assert p['volume'] and p['volume_pdf_page']>=1
 pairs={}
 for ref in refs:
  hits=[p['source_pdf_page'] for p in pages if pos(p['first_verse'])<=pos(ref)<=pos(p['last_verse'])]
  assert 1<=len(hits)<=2,(ref,hits)
  if len(hits)==2:pairs[ref]=hits
 assert len(pairs)==32 and pairs.get('2CH.2.3')==[466,467]
 assert pairs==json.loads((book/'build-inputs/spanning-verses.json').read_text())['verse_page_pairs']
 catalog=json.loads((root/'data/asv1901/catalog-second-chronicles.json').read_text())
 assert catalog['book_code']=='2CH' and catalog['chapter_count']==36 and catalog['verse_count']==822 and catalog['book_order']==14
 assert catalog['reader']=='books/second-chronicles/site/index.html'
 resolution=json.loads((book/'build-inputs/source-differences-resolved.json').read_text())
 assert resolution=={}
 print(json.dumps({'status':'PASS','book':'2CH','chapters':36,'verses':822,'italic_spans':118,'historical_pages':37,'two_page_verses':32,'pdf_volumes':2,'hashed_files':len(mf['files'])},indent=2))
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else '.')
