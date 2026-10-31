#!/usr/bin/env python3
"""Validate source-locked ASV 1901 Joshua release in any repository root."""
from pathlib import Path
import sys,json,hashlib,re,collections
import fitz
from jsonschema import Draft202012Validator
COUNTS=[18, 24, 17, 24, 15, 27, 26, 35, 27, 43, 23, 24, 33, 15, 63, 10, 18, 28, 51, 9, 45, 34, 16, 33]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pos(s):
 assert re.fullmatch(r'JOS\.[1-9][0-9]*\.[1-9][0-9]*',s),s
 return tuple(map(int,s.split('.')[1:]))
def verify(root):
 root=Path(root).resolve();b=root/'books/joshua';data=root/'data/asv1901/joshua'
 manifest=json.loads((b/'RELEASE_MANIFEST.json').read_text())
 assert manifest['edition']=='ASV1901' and manifest['book']=='JOS' and manifest['chapter_count']==24 and manifest['verse_count']==658
 for rel,v in manifest['files'].items():
  p=root/rel
  assert p.is_file() and sha(p)==v, f'Missing/modified: {rel}'
 schema=json.loads((b/'schemas/asv1901-joshua-chapter.schema.json').read_text());indexschema=json.loads((b/'schemas/facsimile-page-index.schema.json').read_text())
 refs=set();it=0
 for ch,count in enumerate(COUNTS,1):
  fn=data/'chapters'/f'{ch:02d}.json';obj=json.loads(fn.read_text());Draft202012Validator(schema).validate(obj)
  assert obj['edition_id']=='ASV1901' and obj['book_code']=='JOS' and obj['chapter']==ch and len(obj['verses'])==count
  for i,verse in enumerate(obj['verses'],1):
   ref=f'JOS.{ch}.{i}'
   assert verse['id']==ref and verse['verse']==i and verse['edition_verse_id']=='ASV1901:'+ref and ref not in refs
   refs.add(ref);assert verse['spans'] and all(s['text'] and s['kind'] in ('text','supplied') for s in verse['spans'])
   it+=sum(s['kind']=='supplied' for s in verse['spans'])
 assert len(refs)==658 and it==43
 idx=json.loads((data/'page-index.json').read_text());Draft202012Validator(indexschema).validate(idx)
 pages=idx['pages'];assert [p['source_pdf_page'] for p in pages]==list(range(239,267))
 sp=[p for p in pages if p['type']=='scripture'];assert len(sp)==26
 assert [p['printed_page'] for p in sp]==list(range(213,239))
 assert len([p for p in pages if p['type']=='map'])==1 and len([p for p in pages if p['type']=='interleaf'])==1
 assert len(idx['volumes'])==2
 vols={v['filename']:v for v in idx['volumes']}
 for name,v in vols.items():
  p=data/'facsimile'/name
  assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256']
  d=fitz.open(p);assert len(d)==v['last_source_pdf_page']-v['first_source_pdf_page']+1;d.close()
 for p in pages:
  assert p['volume'] in vols and p['volume_pdf_page']==p['source_pdf_page']-vols[p['volume']]['first_source_pdf_page']+1
 pairs={}
 for ref in refs:
  where=[p['source_pdf_page'] for p in sp if pos(p['first_verse'])<=pos(ref)<=pos(p['last_verse'])]
  assert 1<=len(where)<=2,(ref,where)
  if len(where)==2:pairs[ref]=where
 assert len(pairs)==23 and pairs['JOS.7.13']==[244,247]
 assert pairs==json.loads((b/'build-inputs/spanning-verses.json').read_text())['verse_page_pairs']
 bookcatalog=json.loads((root/'data/asv1901/catalog-joshua.json').read_text())
 assert bookcatalog['book_code']=='JOS' and bookcatalog['chapter_count']==24 and bookcatalog['verse_count']==658
 assert bookcatalog['reader']=='books/joshua/site/index.html'
 print(json.dumps({'status':'PASS','chapters':24,'verses':658,'italic_spans':43,'historical_pages':28,'scripture_pages':26,'two_page_verses':23,'pdf_volumes':2,'hashed_files':len(manifest['files'])},indent=2))
if __name__=='__main__':verify(sys.argv[1] if len(sys.argv)>1 else '.')
