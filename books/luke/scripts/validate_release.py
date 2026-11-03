#!/usr/bin/env python3
"""Independently validate an extracted, add-only ASV 1901 Luke release.
Usage: python books/luke/scripts/validate_release.py ROOT [OPTIONAL_ORIGINAL_1901_PDF]
"""
import hashlib,json,re,sys
from pathlib import Path
import fitz
from jsonschema import Draft202012Validator
TRAD=[80,52,38,44,39,49,50,56,62,42,54,59,35,35,32,31,37,43,48,47,38,71,56,53]
OMIT={(17,36),(23,17)}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def run(root,original=None):
 root=Path(root);bk=root/'books/luke';data=root/'data/asv1901/luke'
 manifest=load(bk/'RELEASE_MANIFEST.json');assert manifest['book']=='LUK' and manifest['chapter_count']==24 and manifest['verse_count']==1149
 for path,h in manifest['files'].items():assert sha(root/path)==h,('MANIFEST_SHA',path)
 assert len(manifest['files'])<99
 catalog=load(root/'data/asv1901/catalog-luke.json');assert catalog['chapter_count']==24 and catalog['book_order']==42
 assert catalog['verse_count']==1149 and catalog['predecessor_book_code']=='MRK' and catalog['successor_book_code']=='JHN'
 sch=load(bk/'schemas/asv1901-luke-chapter.schema.json');ps=load(bk/'schemas/facsimile-page-index.schema.json')
 verses=[];italic=0
 for ch,count in enumerate(TRAD,1):
  c=load(data/f'chapters/{ch:02d}.json');Draft202012Validator(sch).validate(c)
  want=[v for v in range(1,count+1) if (ch,v) not in OMIT]
  assert [e['verse'] for e in c['verses']]==want,('CHAPTER',ch)
  for e in c['verses']:
   v=e['verse'];assert e['id']==f'LUK.{ch}.{v}' and e['edition_verse_id']==f'ASV1901:LUK.{ch}.{v}'
   assert all(s['text'] for s in e['spans'])
   italic+=sum(s['kind']=='supplied' for s in e['spans']);verses.append((ch,v))
 assert len(verses)==1149 and italic==209
 idx=load(data/'page-index.json');Draft202012Validator(ps).validate(idx)
 assert idx['source_pdf_sha256']==manifest['source_hashes']['original_pdf']
 assert [x['source_pdf_page'] for x in idx['pages']]==list(range(1036,1073))
 assert idx['pages'][0]['type']=='map' and all(p['type']=='scripture' for p in idx['pages'][1:])
 coverage={key:[] for key in verses}
 for item in idx['pages'][1:]:
  def tup(x):return tuple(map(int,x.split('.')[1:]))
  a=tup(item['first_verse']);b=tup(item['last_verse'])
  assert a<=b
  for key in verses:
   if a<=key<=b:coverage[key].append(item['source_pdf_page'])
 assert all(1<=len(v)<=2 for v in coverage.values()),'Every verse must have 1-2 original physical pages'
 assert all(len(p)==1 or p[1]==p[0]+1 for p in coverage.values())
 continuations={key:p for key,p in coverage.items() if len(p)>1}
 assert len(continuations)==29
 # Each continuation flag from printed page agrees with actual shared verse coverage.
 for row in idx['pages'][2:]:
  if row['page_begins_with_verse_continuation']:
   key=tuple(map(int,row['first_verse'].split('.')[1:]));assert len(coverage[key])==2
 for entry in idx['volumes']:
  pp=data/'facsimile'/entry['filename'];assert pp.stat().st_size==entry['bytes'] and sha(pp)==entry['sha256']
  with fitz.open(pp) as doc:assert len(doc)==entry['last_source_pdf_page']-entry['first_source_pdf_page']+1
 for row in idx['pages']:
  vol=next(v for v in idx['volumes'] if v['filename']==row['volume'])
  assert row['volume_pdf_page']==row['source_pdf_page']-vol['first_source_pdf_page']+1
 omit=load(data/'verse-omissions.json');assert {x['verse_id'] for x in omit['omissions']}=={'LUK.17.36','LUK.23.17'}
 assert all(x['status']=='NOT_IN_1901_MAIN_TEXT' for x in omit['omissions'])
 apparatus=load(data/'textual-apparatus.json');assert {x['passage'] for x in apparatus['apparatus']}=={
  'LUK.22.43-LUK.22.44','LUK.23.34','LUK.24.12','LUK.24.40','LUK.24.51','LUK.24.52'}
 assert sha(bk/'sources/asv1901-english-only/42-LUK.usx')==manifest['source_hashes']['primary_usx']
 assert sha(bk/'sources/comparison-only/72-LUKeng-asv.usfm')==manifest['source_hashes']['comparison_usfm']
 if original:
  assert sha(original)==manifest['source_hashes']['original_pdf']
  from contextlib import ExitStack
  with ExitStack() as stack:
   doc=stack.enter_context(fitz.open(original))
   assert len(doc)==1310
   vdocs={v['filename']:stack.enter_context(fitz.open(data/'facsimile'/v['filename'])) for v in idx['volumes']}
   # Iterate exactly once over original and extracted pages, matching all embedded images
   # including byte-identical compressed streams and their matrix placements.
   for row in idx['pages']:
    s=doc[row['source_pdf_page']-1];vd=vdocs[row['volume']];t=vd[row['volume_pdf_page']-1]
    assert s.rect==t.rect
    ai=s.get_images(full=True);bi=t.get_images(full=True)
    assert len(ai)==len(bi),(row['source_pdf_page'],len(ai),len(bi))
    for x,y in zip(ai,bi):
     # Compare original unchanged embedded compressed object bytes, not costly
     # decompressed multi-megabyte image streams, then compare placements.
     assert doc.xref_stream_raw(x[0])==vd.xref_stream_raw(y[0]),('IMAGE_STREAM',row['source_pdf_page'])
     ar=s.get_image_rects(x[0],transform=True);br=t.get_image_rects(y[0],transform=True)
     assert [(tuple(q),tuple(m)) for q,m in ar]==[(tuple(q),tuple(m)) for q,m in br],('IMAGE_TRANSFORM',row['source_pdf_page'])
 return {'status':'PASS','book':'LUK','chapters':24,'main_text_verses':len(verses),'italics':italic,
    'original_pages':len(idx['pages']),'page_spanning_verses':len(continuations),
    'manifest_file_count':len(manifest['files']),'source_pdf_image_identity':bool(original)}
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
if __name__=='__main__':
 print(json.dumps(run(sys.argv[1] if len(sys.argv)>1 else '.',sys.argv[2] if len(sys.argv)>2 else None),indent=2))
