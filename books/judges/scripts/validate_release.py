#!/usr/bin/env python3
"""Validate the installed ASV 1901 Judges release from repository root."""
from pathlib import Path
import sys,json,hashlib,re
import fitz
from jsonschema import Draft202012Validator
COUNTS=[36, 23, 31, 24, 31, 40, 25, 35, 57, 18, 40, 15, 25, 20, 20, 31, 13, 31, 30, 48, 25]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pos(s):
 assert re.fullmatch(r'JDG\.[1-9][0-9]*\.[1-9][0-9]*',s),s
 return tuple(map(int,s.split('.')[1:]))
def verify(root):
 root=Path(root).resolve();book=root/'books/judges';data=root/'data/asv1901/judges'
 manifest=json.loads((book/'RELEASE_MANIFEST.json').read_text())
 assert manifest['edition']=='ASV1901' and manifest['book']=='JDG' and manifest['chapter_count']==21 and manifest['verse_count']==618
 for rel,digest in manifest['files'].items():
  path=root/rel
  assert path.is_file() and sha(path)==digest, f'Missing/modified: {rel}'
 schema=json.loads((book/'schemas/asv1901-judges-chapter.schema.json').read_text())
 index_schema=json.loads((book/'schemas/facsimile-page-index.schema.json').read_text())
 refs=set();it=0
 for c,count in enumerate(COUNTS,1):
  fn=data/'chapters'/f'{c:02d}.json';obj=json.loads(fn.read_text());Draft202012Validator(schema).validate(obj)
  assert obj['edition_id']=='ASV1901' and obj['book_code']=='JDG' and obj['chapter']==c and len(obj['verses'])==count
  for i,v in enumerate(obj['verses'],1):
   ref=f'JDG.{c}.{i}'
   assert v['id']==ref and v['verse']==i and v['edition_verse_id']=='ASV1901:'+ref and ref not in refs
   assert v['spans'] and all(s['text'] and s['kind'] in ('text','supplied') for s in v['spans'])
   refs.add(ref);it+=sum(s['kind']=='supplied' for s in v['spans'])
 assert len(refs)==618 and it==62
 idx=json.loads((data/'page-index.json').read_text());Draft202012Validator(index_schema).validate(idx)
 pages=idx['pages'];assert [p['source_pdf_page'] for p in pages]==list(range(267,294))
 assert all(p['type']=='scripture' for p in pages) and [p['printed_page'] for p in pages]==list(range(239,266))
 assert len(idx['volumes'])==2
 volumes={v['filename']:v for v in idx['volumes']}
 for name,v in volumes.items():
  pdf=data/'facsimile'/name
  assert pdf.stat().st_size==v['bytes'] and sha(pdf)==v['sha256']
  doc=fitz.open(pdf);assert len(doc)==v['last_source_pdf_page']-v['first_source_pdf_page']+1;doc.close()
 for p in pages:
  assert p['volume'] in volumes
  assert p['volume_pdf_page']==p['source_pdf_page']-volumes[p['volume']]['first_source_pdf_page']+1
 pairs={}
 for ref in refs:
  where=[p['source_pdf_page'] for p in pages if pos(p['first_verse'])<=pos(ref)<=pos(p['last_verse'])]
  assert 1<=len(where)<=2,(ref,where)
  if len(where)==2:pairs[ref]=where
 assert len(pairs)==25 and 'JDG.18.13' not in pairs
 assert pairs==json.loads((book/'build-inputs/spanning-verses.json').read_text())['verse_page_pairs']
 catalog=json.loads((root/'data/asv1901/catalog-judges.json').read_text())
 assert catalog['book_code']=='JDG' and catalog['chapter_count']==21 and catalog['verse_count']==618 and catalog['reader']=='books/judges/site/index.html'
 print(json.dumps({'status':'PASS','chapters':21,'verses':618,'italic_spans':62,'historical_pages':27,'two_page_verses':25,'pdf_volumes':2,'hashed_files':len(manifest['files'])},indent=2))
if __name__=='__main__':verify(sys.argv[1] if len(sys.argv)>1 else '.')
