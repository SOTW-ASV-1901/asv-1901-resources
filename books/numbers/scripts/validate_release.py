#!/usr/bin/env python3
"""Validate book content, page indices, local chapter schemas, original PDF volume hashes and manifest."""
from pathlib import Path
import sys,json,hashlib,collections,re
from jsonschema import Draft202012Validator
import fitz
COUNTS=[54, 34, 51, 49, 31, 27, 89, 26, 23, 36, 35, 16, 33, 45, 41, 50, 13, 32, 22, 29, 35, 41, 30, 25, 18, 65, 23, 31, 40, 16, 54, 42, 56, 29, 34, 13]
def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root):
 root=Path(root).resolve();book=root/'books/numbers';data=root/'data/asv1901/numbers'
 m=json.loads((book/'RELEASE_MANIFEST.json').read_text())
 assert m['edition']=='ASV1901' and m['book']=='NUM' and m['chapter_count']==36 and m['verse_count']==1288
 for rel,v in m['files'].items():
  p=root/rel
  assert p.is_file() and hashfile(p)==v,f'Missing/changed manifest file: {rel}'
 schema=json.loads((book/'schemas/asv1901-numbers-chapter.schema.json').read_text())
 idxschema=json.loads((book/'schemas/facsimile-page-index.schema.json').read_text())
 refs=set();italics=0
 for c,n in enumerate(COUNTS,1):
  obj=json.loads((data/'chapters'/f'{c:02d}.json').read_text());Draft202012Validator(schema).validate(obj)
  assert obj['edition_id']=='ASV1901' and obj['book_code']=='NUM' and obj['chapter']==c
  assert len(obj['verses'])==n
  for vno,v in enumerate(obj['verses'],1):
   ref=f'NUM.{c}.{vno}'
   assert v['id']==ref and v['verse']==vno and v['edition_verse_id']=='ASV1901:'+ref and ref not in refs
   refs.add(ref)
   assert v['spans'] and all(s['text'] and s['kind'] in ('text','supplied') for s in v['spans'])
   italics+=sum(s['kind']=='supplied' for s in v['spans'])
 assert len(refs)==1288 and italics==110
 pi=json.loads((data/'page-index.json').read_text());Draft202012Validator(idxschema).validate(pi)
 pages=pi['pages']
 assert [p['source_pdf_page'] for p in pages]==list(range(155,200))
 assert [p['printed_page'] for p in pages]==list(range(129,174))
 assert all(p['type']=='scripture' for p in pages)
 assert len(pi['volumes'])==2
 vols={v['filename']:v for v in pi['volumes']}
 for name,item in vols.items():
  p=data/'facsimile'/name;assert p.stat().st_size==item['bytes'] and hashfile(p)==item['sha256']
  d=fitz.open(p);assert len(d)==item['last_source_pdf_page']-item['first_source_pdf_page']+1;d.close()
 for p in pages:
  assert p['volume'] in vols and p['volume_pdf_page']==p['source_pdf_page']-vols[p['volume']]['first_source_pdf_page']+1
 def pos(s):
  assert re.fullmatch(r'NUM\.[0-9]+\.[0-9]+',s),s
  return tuple(map(int,s.split('.')[1:]))
 pairs={}
 for ref in refs:
  pair=pos(ref)
  match=[p['source_pdf_page'] for p in pages if pos(p['first_verse'])<=pair<=pos(p['last_verse'])]
  assert 1<=len(match)<=2,(ref,match)
  if len(match)==2:
   assert match[1]==match[0]+1,(ref,match)
   pairs[ref]=match
 assert len(pairs)==37
 source_pairs=json.loads((book/'build-inputs/spanning-verses.json').read_text())['verse_page_pairs']
 assert pairs==source_pairs
 catalog=json.loads((root/'data/asv1901/catalog-numbers.json').read_text())
 assert catalog['book_code']=='NUM' and catalog['chapter_count']==36 and catalog['verse_count']==1288
 assert catalog['reader']=='books/numbers/site/index.html'
 print(json.dumps({'status':'PASS','chapters':36,'verses':1288,'italic_spans':110,'historical_pages':45,'two_page_verses':37,'pdf_volumes':2,'hashed_files':len(m['files'])},indent=2))
if __name__=='__main__':verify(sys.argv[1] if len(sys.argv)>1 else '.')
