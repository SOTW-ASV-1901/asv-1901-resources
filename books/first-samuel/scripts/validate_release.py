#!/usr/bin/env python3
"""Independent validator for the ASV1901 1 Samuel GitHub book installation."""
import json,hashlib,re,sys
from pathlib import Path
from jsonschema import Draft202012Validator
import fitz
COUNTS=[28, 36, 21, 22, 12, 21, 17, 22, 27, 27, 15, 25, 23, 52, 35, 23, 58, 30, 24, 42, 15, 23, 29, 22, 44, 25, 12, 25, 11, 31, 13]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pos(r):
 assert re.fullmatch(r'1SA\.[1-9][0-9]*\.[1-9][0-9]*',r),r
 return tuple(map(int,r.split('.')[1:]))
def run(root):
 root=Path(root).resolve();book=root/'books/first-samuel';data=root/'data/asv1901/first-samuel'
 mf=json.loads((book/'RELEASE_MANIFEST.json').read_text());assert mf['book']=='1SA' and mf['chapter_count']==31 and mf['verse_count']==810
 for rel,h in mf['files'].items():
  p=root/rel;assert p.is_file() and sha(p)==h,('Missing or changed',rel)
 schema=json.loads((book/'schemas/asv1901-first-samuel-chapter.schema.json').read_text());ischema=json.loads((book/'schemas/facsimile-page-index.schema.json').read_text())
 refs=set(); ital=0
 for c,count in enumerate(COUNTS,1):
  doc=json.loads((data/'chapters'/f'{c:02d}.json').read_text());Draft202012Validator(schema).validate(doc)
  assert doc['edition_id']=='ASV1901' and doc['book_code']=='1SA' and doc['chapter']==c and len(doc['verses'])==count
  for vnum,v in enumerate(doc['verses'],1):
   k=f'1SA.{c}.{vnum}';assert v['id']==k and v['edition_verse_id']=='ASV1901:'+k and v['verse']==vnum and k not in refs
   assert v['spans'] and all(s['text'] and s['kind'] in ('text','supplied') for s in v['spans'])
   refs.add(k);ital+=sum(s['kind']=='supplied' for s in v['spans'])
 assert len(refs)==810 and ital==80
 idx=json.loads((data/'page-index.json').read_text());Draft202012Validator(ischema).validate(idx)
 pages=idx['pages'];assert [p['source_pdf_page'] for p in pages]==list(range(300,338))
 assert len([p for p in pages if p['type']=='scripture'])==34 and len([p for p in pages if p['type']=='map'])==2 and len([p for p in pages if p['type']=='interleaf'])==2
 assert [p['printed_page'] for p in pages if p['type']=='scripture']==list(range(270,304))
 vols=idx['volumes'];assert len(vols)==2
 for vol in vols:
  p=data/'facsimile'/vol['filename']; assert p.is_file() and p.stat().st_size==vol['bytes'] and sha(p)==vol['sha256']
  with fitz.open(p) as pdf:assert len(pdf)==vol['last_source_pdf_page']-vol['first_source_pdf_page']+1
 for p in pages:
  assert p['volume'] and p['volume_pdf_page']>=1
  if p['type']=='scripture':assert pos(p['first_verse'])<=pos(p['last_verse'])
 pairs={}
 for k in refs:
  hits=[p['source_pdf_page'] for p in pages if p['type']=='scripture' and pos(p['first_verse'])<=pos(k)<=pos(p['last_verse'])]
  assert 1<=len(hits)<=2,(k,hits)
  if len(hits)==2:pairs[k]=hits
 assert len(pairs)==32 and pairs.get('1SA.8.9')==[306,309] and pairs.get('1SA.23.10')==[326,329]
 assert pairs==json.loads((book/'build-inputs/spanning-verses.json').read_text())['verse_page_pairs']
 catalog=json.loads((root/'data/asv1901/catalog-first-samuel.json').read_text())
 assert catalog['book_code']=='1SA' and catalog['chapter_count']==31 and catalog['verse_count']==810
 assert catalog['reader']=='books/first-samuel/site/index.html'
 print(json.dumps({'status':'PASS','book':'1SA','chapters':31,'verses':810,'italic_spans':80,'historical_pages':38,'two_page_verses':32,'historical_volumes':2,'hashed_files':len(mf['files'])},indent=2))
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else '.')
