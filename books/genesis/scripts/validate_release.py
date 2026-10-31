#!/usr/bin/env python3
"""Check actual generated Genesis files and original-print PDF navigation offline."""
import hashlib,json,sys
from pathlib import Path
from build_genesis import EXPECTED,parse_ref


def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for part in iter(lambda:f.read(1<<20),b''):h.update(part)
 return h.hexdigest()


def validate(root):
 root=Path(root);book=root/'books/genesis';base=root/'data/asv1901/genesis'
 manifest=json.loads((book/'RELEASE_MANIFEST.json').read_text())
 assert manifest['verse_count']==1533 and manifest['chapter_count']==50
 for rel,expected in manifest['files'].items():
  p=root/rel
  assert p.exists(),f'Missing file {rel}'
  assert sha(p)==expected,f'Hash failure {rel}'
 refs=set();supplied_count=0
 for chapter,count in enumerate(EXPECTED,1):
  p=base/f'chapters/{chapter:02d}.json'
  ch=json.loads(p.read_text())
  assert ch['edition_id']=='ASV1901' and ch['book_code']=='GEN' and ch['chapter']==chapter
  assert len(ch['verses'])==count
  for v in ch['verses']:
   n=v['verse'];assert 1<=n<=count
   vid=f'GEN.{chapter}.{n}'
   assert v['id']==vid and v['edition_verse_id']==f'ASV1901:{vid}'
   assert vid not in refs;refs.add(vid)
   assert v['spans'] and all(x['text'] and x['kind'] in {'text','supplied'} for x in v['spans'])
   supplied_count+=sum(x['kind']=='supplied' for x in v['spans'])
 assert len(refs)==1533
 pageindex=json.loads((base/'page-index.json').read_text())
 volumes={v['filename']:v for v in pageindex['volumes']}
 all_pages=pageindex['pages'];assert all_pages
 pages={};all_coverage={key:[] for key in refs}
 for p in all_pages:
  pdf_page=p['source_pdf_page'];assert pdf_page not in pages;pages[pdf_page]=p
  vol=volumes[p['volume']]
  assert (base/'facsimile'/p['volume']).exists()
  assert (base/'facsimile'/p['volume']).stat().st_size==vol['bytes']
  assert sha(base/'facsimile'/p['volume'])==vol['sha256']
  assert vol['first_source_pdf_page']<=pdf_page<=vol['last_source_pdf_page']
  assert p['volume_pdf_page']==pdf_page-vol['first_source_pdf_page']+1
  if p['type']=='scripture':
   lo,hi=parse_ref(p['first_verse']),parse_ref(p['last_verse'])
   assert lo<=hi
   for r in refs:
    c,v=map(int,r.split('.')[1:]);
    if lo<=(c,v)<=hi:all_coverage[r].append(pdf_page)
 assert sorted(pages)==list(range(min(pages),max(pages)+1)),'Unclassified source pages'
 for ref, pp in all_coverage.items():
  assert len(pp) in {1,2},f'Unmapped / unexpected page count {ref}: {pp}'
  if len(pp)==2:
   scripture_nums=[p['source_pdf_page'] for p in all_pages if p['type']=='scripture']
   assert scripture_nums.index(pp[1])==scripture_nums.index(pp[0])+1,f'Nonconsecutive Scripture page pair {ref}'
 # Validate physical-page continuation claims against preserved running-head identities.
 def predecessor(t):
  c,v=t;return (c,v-1) if v>1 else (c-1,EXPECTED[c-2])
 scripture_sorted=[p for p in all_pages if p['type']=='scripture']
 assert len(scripture_sorted)==52
 source_audit=json.loads((book/'build-inputs/page-boundary-evidence.json').read_text())['scripture_page_evidence']
 evidence_by_page={p['source_pdf_page']:p for p in source_audit}
 assert len(evidence_by_page)==52
 for i,p in enumerate(scripture_sorted):
  page_no=p['source_pdf_page'];e=evidence_by_page[page_no]
  actual=parse_ref(p['first_verse']);header=parse_ref(p['running_head_first_verse'])
  assert e['actual_first_verse']==p['first_verse']
  assert e['running_head_first_verse']==p['running_head_first_verse']
  is_continuation=actual!=header
  assert is_continuation==p['page_begins_with_verse_continuation']
  assert is_continuation==e['page_begins_with_prior_verse_continuation']
  assert actual==(predecessor(header) if is_continuation else header)
  if i and is_continuation:
   assert scripture_sorted[i-1]['last_verse']==p['first_verse']
 documented=json.loads((book/'build-inputs/spanning-verses.json').read_text())
 assert {ref:pp for ref,pp in all_coverage.items() if len(pp)==2}==documented['verse_page_pairs']
 assert len(documented['special_cases_with_historical_map_interleaves'])==3
 # PDF page positions, not just file presence
 try:
  import fitz
  for v in volumes.values():
   doc=fitz.open(base/'facsimile'/v['filename'])
   assert len(doc)==v['last_source_pdf_page']-v['first_source_pdf_page']+1
   doc.close()
 except ImportError:
  raise AssertionError('PyMuPDF is required for final facsimile validation')
 return {'status':'STRUCTURAL_INTEGRITY_PASS','chapters':50,'verses':len(refs),'italics_spans':supplied_count,
         'historical_pages':len(all_pages),'pdf_volumes':len(volumes),'page_range_coverage':'ALL_VERSES','verses_on_two_pages':len(documented['verse_page_pairs'])}

if __name__=='__main__':
 if len(sys.argv)!=2:print('Usage: validate_release.py <release-root>');sys.exit(2)
 try:print(json.dumps(validate(sys.argv[1]),indent=2))
 except Exception as exc:print(f'VALIDATION FAILED: {exc}',file=sys.stderr);sys.exit(1)
