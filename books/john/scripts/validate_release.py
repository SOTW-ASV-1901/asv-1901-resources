#!/usr/bin/env python3
"""Independent validation of an extracted ASV1901 John release.
Usage: python books/john/scripts/validate_release.py ROOT [ORIGINAL_1901_PDF]
"""
import hashlib,json,sys
from pathlib import Path
from contextlib import ExitStack
import fitz
from jsonschema import Draft202012Validator
TRAD=[51,25,36,54,47,71,53,59,41,42,57,50,38,31,27,33,26,40,42,31,25]
OMIT={(5,4)}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def run(root,original=None):
 root=Path(root);bk=root/'books/john';dat=root/'data/asv1901/john'
 mf=load(bk/'RELEASE_MANIFEST.json');assert mf['book']=='JHN' and mf['chapter_count']==21 and mf['verse_count']==878
 assert len(mf['files'])<99
 assert not any(p.startswith('books/') and not p.startswith('books/john/') for p in mf['files'])
 assert not any(p.startswith('data/asv1901/') and not (p.startswith('data/asv1901/john/') or p=='data/asv1901/catalog-john.json') for p in mf['files'])
 for path,h in mf['files'].items():assert sha(root/path)==h,('MANIFEST_SHA',path)
 catalog=load(root/'data/asv1901/catalog-john.json')
 assert catalog['chapter_count']==21 and catalog['book_order']==43 and catalog['verse_count']==878
 assert catalog['predecessor_book_code']=='LUK' and catalog['successor_book_code']=='ACT'
 sch=load(bk/'schemas/asv1901-john-chapter.schema.json');ps=load(bk/'schemas/facsimile-page-index.schema.json')
 positions=[];italic=0;versetext={}
 for ch,count in enumerate(TRAD,1):
  chapter=load(dat/f'chapters/{ch:02d}.json');Draft202012Validator(sch).validate(chapter)
  expected=[v for v in range(1,count+1) if (ch,v) not in OMIT]
  assert [v['verse'] for v in chapter['verses']]==expected,('CHAPTER_IDS',ch)
  for verse in chapter['verses']:
   v=verse['verse'];pos=(ch,v)
   assert verse['id']==f'JHN.{ch}.{v}' and verse['edition_verse_id']=='ASV1901:'+verse['id']
   assert all(s['text'] for s in verse['spans'])
   italic+=sum(s['kind']=='supplied' for s in verse['spans']);positions.append(pos)
   versetext[pos]=''.join(s['text'] for s in verse['spans'])
 assert len(positions)==878 and italic==135
 assert 'JESUS OF NAZARETH, THE KING OF THE JEWS' in versetext[(19,19)]
 assert versetext[(7,53)].startswith('[') and versetext[(8,11)].endswith(']')
 assert (5,4) not in versetext
 idx=load(dat/'page-index.json');Draft202012Validator(ps).validate(idx)
 assert idx['source_pdf_sha256']==mf['source_hashes']['original_pdf']
 assert [x['source_pdf_page'] for x in idx['pages']]==list(range(1074,1103))
 assert idx['pages'][0]['type']=='map' and all(p['type']=='scripture' for p in idx['pages'][1:])
 coverage={p:[] for p in positions}
 for row in idx['pages'][1:]:
  def tuple_ref(s):return tuple(map(int,s.split('.')[1:]))
  a=tuple_ref(row['first_verse']);b=tuple_ref(row['last_verse']);assert a<=b
  for pos in positions:
   if a<=pos<=b:coverage[pos].append(row['source_pdf_page'])
 assert all(1<=len(v)<=2 for v in coverage.values())
 assert all(len(v)==1 or v[1]==v[0]+1 for v in coverage.values())
 crossing={p:pages for p,pages in coverage.items() if len(pages)>1}
 assert len(crossing)==21,('PAGE_SPANNING',len(crossing))
 for row in idx['pages'][2:]:
  if row['page_begins_with_verse_continuation']:
   pos=tuple(map(int,row['first_verse'].split('.')[1:]));assert len(coverage[pos])==2
 for v in idx['volumes']:
  path=dat/'facsimile'/v['filename']
  assert sha(path)==v['sha256'] and path.stat().st_size==v['bytes']
  with fitz.open(path) as d:assert len(d)==v['last_source_pdf_page']-v['first_source_pdf_page']+1
 for row in idx['pages']:
  vol=next(v for v in idx['volumes'] if v['filename']==row['volume'])
  assert row['volume_pdf_page']==row['source_pdf_page']-vol['first_source_pdf_page']+1
 omission=load(dat/'verse-omissions.json')
 assert [x['verse_id'] for x in omission['omissions']]==['JHN.5.4']
 assert omission['omissions'][0]['status']=='NOT_IN_1901_MAIN_TEXT'
 apparatus=load(dat/'textual-apparatus.json')
 assert {x['passage'] for x in apparatus['apparatus']}=={'JHN.5.4','JHN.7.53-JHN.8.11'}
 diff=load(bk/'build-inputs/source-differences-resolved.json')
 assert len(diff['differences'])==16 and diff['difference_count']==16
 assert sha(bk/'sources/asv1901-english-only/43-JHN.usx')==mf['source_hashes']['primary_usx']
 assert sha(bk/'sources/comparison-only/73-JHNeng-asv.usfm')==mf['source_hashes']['comparison_usfm']
 if original:
  assert sha(original)==mf['source_hashes']['original_pdf']
  with ExitStack() as stack:
   src=stack.enter_context(fitz.open(original))
   assert len(src)==1310
   extracted={v['filename']:stack.enter_context(fitz.open(dat/'facsimile'/v['filename'])) for v in idx['volumes']}
   for row in idx['pages']:
    a=src[row['source_pdf_page']-1];doc=extracted[row['volume']];b=doc[row['volume_pdf_page']-1]
    assert a.rect==b.rect
    imga=a.get_images(full=True);imgb=b.get_images(full=True)
    assert len(imga)==len(imgb),('IMAGE_COUNT',row['source_pdf_page'])
    for ia,ib in zip(imga,imgb):
     assert src.xref_stream_raw(ia[0])==doc.xref_stream_raw(ib[0]),('IMAGE_STREAM',row['source_pdf_page'])
     ra=a.get_image_rects(ia[0],transform=True);rb=b.get_image_rects(ib[0],transform=True)
     assert [(tuple(q),tuple(m)) for q,m in ra]==[(tuple(q),tuple(m)) for q,m in rb],('IMAGE_TRANSFORM',row['source_pdf_page'])
 return {'status':'PASS','book':'JHN','chapters':21,'main_text_verses':878,'italics':italic,
  'original_pages':len(idx['pages']),'page_spanning_verses':len(crossing),
  'manifest_file_count':len(mf['files']),'original_pdf_image_streams_and_placements':bool(original)}
if __name__=='__main__':
 print(json.dumps(run(sys.argv[1] if len(sys.argv)>1 else '.',sys.argv[2] if len(sys.argv)>2 else None),indent=2))
