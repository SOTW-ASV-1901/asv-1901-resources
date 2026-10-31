#!/usr/bin/env python3
"""Validate this installed ASV 1901 Ruth release from repository root."""
import json,hashlib,re,sys
from pathlib import Path
from jsonschema import Draft202012Validator
import fitz
COUNTS=[22,23,18,22]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def versepos(s):
 assert re.fullmatch(r'RUT\.[1-9][0-9]*\.[1-9][0-9]*',s),s
 return tuple(map(int,s.split('.')[1:]))
def verify(root):
 root=Path(root).resolve(); book=root/'books/ruth';data=root/'data/asv1901/ruth'
 mf=json.loads((book/'RELEASE_MANIFEST.json').read_text())
 assert mf['edition']=='ASV1901' and mf['book']=='RUT' and mf['chapter_count']==4 and mf['verse_count']==85
 for rel,digest in mf['files'].items():
  path=root/rel;assert path.is_file() and sha(path)==digest,f'Missing/modified file: {rel}'
 schema=json.loads((book/'schemas/asv1901-ruth-chapter.schema.json').read_text())
 ischema=json.loads((book/'schemas/facsimile-page-index.schema.json').read_text())
 refs=set();it=0
 for c,count in enumerate(COUNTS,1):
  j=json.loads((data/'chapters'/f'{c:02d}.json').read_text());Draft202012Validator(schema).validate(j)
  assert j['book_code']=='RUT' and j['edition_id']=='ASV1901' and j['chapter']==c and len(j['verses'])==count
  for vnum,v in enumerate(j['verses'],1):
   ref=f'RUT.{c}.{vnum}';assert v['id']==ref and v['verse']==vnum and v['edition_verse_id']=='ASV1901:'+ref and ref not in refs
   assert v['spans'] and all(s['text'] and s['kind'] in ('text','supplied') for s in v['spans'])
   refs.add(ref);it+=sum(s['kind']=='supplied' for s in v['spans'])
 assert len(refs)==85 and it==5
 idx=json.loads((data/'page-index.json').read_text());Draft202012Validator(ischema).validate(idx)
 pages=idx['pages'];assert [p['source_pdf_page'] for p in pages]==list(range(294,300))
 assert [p['type'] for p in pages]==['scripture','map','interleaf','scripture','scripture','scripture']
 assert [p['printed_page'] for p in pages if p['type']=='scripture']==[266,267,268,269]
 assert len(idx['volumes'])==1
 vol=idx['volumes'][0];f=data/'facsimile'/vol['filename'];assert f.stat().st_size==vol['bytes'] and sha(f)==vol['sha256']
 d=fitz.open(f);assert len(d)==6;d.close()
 for p in pages:assert p['volume']==vol['filename'] and p['volume_pdf_page']==p['source_pdf_page']-293
 pairs={}
 for ref in refs:
  hits=[p['source_pdf_page'] for p in pages if p['type']=='scripture' and versepos(p['first_verse'])<=versepos(ref)<=versepos(p['last_verse'])]
  assert 1<=len(hits)<=2,(ref,hits)
  if len(hits)==2:pairs[ref]=hits
 assert pairs=={'RUT.1.22':[294,297],'RUT.2.22':[297,298],'RUT.4.5':[298,299]}
 assert pairs==json.loads((book/'build-inputs/spanning-verses.json').read_text())['verse_page_pairs']
 catalog=json.loads((root/'data/asv1901/catalog-ruth.json').read_text())
 assert catalog['book_code']=='RUT' and catalog['chapter_count']==4 and catalog['verse_count']==85 and catalog['reader']=='books/ruth/site/index.html'
 print(json.dumps({'status':'PASS','chapters':4,'verses':85,'italic_spans':5,'source_pdf_pages':6,'printed_scripture_pages':4,'two_page_verses':3,'pdf_volumes':1,'hashed_files':len(mf['files'])},indent=2))
if __name__=='__main__':verify(sys.argv[1] if len(sys.argv)>1 else '.')
