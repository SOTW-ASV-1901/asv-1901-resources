#!/usr/bin/env python3
"""Independent ASV1901 book-release validation: scan, text, UI, source, reproducibility.
Run from any cloned repository with the whole original source PDF and witness files:
python validate_release.py <repo-root> <original-pdf> [--write-audit]
"""
from pathlib import Path
import sys,hashlib,json,re,argparse,subprocess,threading,functools,http.server,urllib.request,zipfile
from jsonschema import Draft202012Validator
import fitz

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def run(root,pdf,write_audit=False):
 here=Path(__file__).resolve().parent.parent
 cfg=json.loads((here/'build-inputs/book-plan.json').read_text());slug=cfg['slug'];code=cfg['code']
 root=Path(root);pdf=Path(pdf);bk=root/'books'/slug;data=root/'data/asv1901'/slug
 assert sha(pdf)==cfg['source_pdf_sha256'],'parent source scan hash mismatch'
 mf=json.loads((bk/'RELEASE_MANIFEST.json').read_text())
 assert mf['book']==code and mf['chapter_count']==len(cfg['chapter_counts'])
 for p,h in mf['files'].items():
  assert (root/p).is_file() and sha(root/p)==h,('MANIFEST_SHA',p)
 catalog=json.loads((root/'data/asv1901'/f'catalog-{slug}.json').read_text())
 assert catalog['book_code']==code and catalog['book_order']==cfg['order']
 expected={(ch,v) for ch,n in enumerate(cfg['chapter_counts'],1) for v in range(1,n+1)}
 omit={tuple(k) for k in cfg['omissions']};expected_main=expected-omit;got=set();all_italics=0
 schema=json.loads((bk/'schemas'/f'asv1901-{slug}-chapter.schema.json').read_text())
 page_schema=json.loads((bk/'schemas/facsimile-page-index.schema.json').read_text())
 def verse_text(ch,verse):
  d=json.loads((data/'chapters'/f'{ch:02d}.json').read_text());return ''.join(s['text'] for v in d['verses'] if v['verse']==verse for s in v['spans'])
 for ch,n in enumerate(cfg['chapter_counts'],1):
  d=json.loads((data/'chapters'/f'{ch:02d}.json').read_text());Draft202012Validator(schema).validate(d)
  assert len(d['verses'])==n-sum(x==ch for x,v in omit)
  for v in d['verses']:
   key=(ch,v['verse']);assert key not in got and key in expected_main
   assert v['id']==f'{code}.{ch}.{v["verse"]}' and v['edition_verse_id']=='ASV1901:'+v['id']
   got.add(key);all_italics+=sum(x['kind']=='supplied' for x in v['spans'])
 assert got==expected_main and catalog['verse_count']==len(got)
 omissions=json.loads((data/'verse-omissions.json').read_text())
 assert {tuple(map(int,x['verse_id'].split('.')[1:])) for x in omissions['omissions']}==omit
 index=json.loads((data/'page-index.json').read_text());Draft202012Validator(page_schema).validate(index)
 rows=index['pages'];assert [p['source_pdf_page'] for p in rows]==list(range(cfg['first_pdf'],cfg['last_pdf']+1))
 assert {p['source_pdf_page'] for p in rows if p['type']=='map'}==set(cfg['map_pages'])
 assert {p['source_pdf_page'] for p in rows if p['type']=='interleaf'}==set(cfg['interleaf_pages'])
 expected_scripture={x[0] for x in cfg['scripture']}
 assert {p['source_pdf_page'] for p in rows if p['type']=='scripture'}==expected_scripture
 assert [p['printed_page'] for p in rows if p['type']=='scripture']==list(range(cfg['first_print'],cfg['first_print']+len(expected_scripture)))
 allkeys=[(ch,v) for ch,n in enumerate(cfg['chapter_counts'],1) for v in range(1,n+1) if (ch,v) not in omit]
 positions={p:i for i,p in enumerate(allkeys)};coverage={}
 for p in rows:
  if p['type']!='scripture':continue
  x=tuple(map(int,p['first_verse'].split('.')[1:]));y=tuple(map(int,p['last_verse'].split('.')[1:]));assert x in positions and y in positions and positions[x]<=positions[y]
  for key in allkeys[positions[x]:positions[y]+1]:coverage.setdefault(key,[]).append(p['source_pdf_page'])
 assert set(coverage)==expected_main
 crossing={k:v for k,v in coverage.items() if len(v)>1}
 assert all(len(v)<=2 for v in crossing.values())
 parent=fitz.open(pdf)
 assert len(parent)==1310
 original_streams=0;rendered_samples=0;source_pages=0
 volume_docs={v['filename']:fitz.open(data/'facsimile'/v['filename']) for v in index['volumes']}
 try:
  for volume in index['volumes']:
   path=data/'facsimile'/volume['filename'];doc=volume_docs[volume['filename']]
   assert path.stat().st_size==volume['bytes'] and sha(path)==volume['sha256']
   assert len(doc)==volume['last_source_pdf_page']-volume['first_source_pdf_page']+1
  samples=sorted({cfg['first_pdf'],cfg['first_pdf']+1,(cfg['first_pdf']+cfg['last_pdf'])//2,
                  cfg['last_pdf']-2,cfg['last_pdf']-1,cfg['last_pdf']})
  for p in rows:
   n=p['source_pdf_page'];orig=parent[n-1];ex=volume_docs[p['volume']][p['volume_pdf_page']-1]
   assert tuple(orig.rect)==tuple(ex.rect),('PAGE_SIZE',n)
   im1=orig.get_images(full=True);im2=ex.get_images(full=True)
   assert len(im1)==len(im2),('IMAGE_COUNT',n,len(im1),len(im2))
   for a,b in zip(im1,im2):
    aa=parent.xref_stream_raw(a[0]);bb=volume_docs[p['volume']].xref_stream_raw(b[0])
    assert aa==bb,('ORIGINAL_IMAGE_BYTES',n)
    xx=orig.get_image_rects(a[0],transform=True);yy=ex.get_image_rects(b[0],transform=True)
    assert len(xx)==len(yy),('PLACEMENT_COUNT',n)
    for (ar,am),(br,bm) in zip(xx,yy):
     assert tuple(ar)==tuple(br) and tuple(am)==tuple(bm),('PLACEMENT',n)
    original_streams+=1
   if n in samples:
    x=orig.get_pixmap(matrix=fitz.Matrix(.32,.32),alpha=False);y=ex.get_pixmap(matrix=fitz.Matrix(.32,.32),alpha=False)
    assert (x.width,x.height,x.n)==(y.width,y.height,y.n) and x.samples==y.samples,('RENDERED_PIXELS',n)
    rendered_samples+=1
   source_pages+=1
 finally:
  parent.close()
  for d in volume_docs.values():d.close()
 # Original witnesses must remain unmodified, and their word/italic alignment is source-checked during deterministic build.
 for sub,name,hashkey in [('asv1901-english-only',cfg['usx'],'primary_usx_sha256'),('comparison-only',cfg['usfm'],'comparison_usfm_sha256')]:
  assert sha(bk/'sources'/sub/name)==cfg[hashkey]
 differences=json.loads((bk/'build-inputs/source-differences-resolved.json').read_text())
 assert differences['difference_count']==sum(differences[x] for x in ['typographical_or_orthographic_count','different_words_or_hyphenation_count'])
 import xml.etree.ElementTree as ET
 original_root=ET.parse(bk/'sources/asv1901-english-only'/cfg['usx']).getroot()
 note_count=sum(1 for x in original_root.iter() if x.tag.split('}')[-1]=='note')
 assert len(omit)==0
 assert verse_text(1,1) and verse_text(len(cfg['chapter_counts']),cfg['chapter_counts'][-1])
 for change in cfg['source_decisions']:
  parts=change['verse'].split('.');assert change['replace_with'] in verse_text(int(parts[1]),int(parts[2]))
 html=(bk/'site/index.html').read_text();scripts=re.findall(r'<script>(.*?)</script>',html,flags=re.S)
 assert len(scripts)==1 and '../../../data/asv1901/'+slug+'/' in html
 assert 'nextVersePage' in html and 'showMatchingPages' in html
 assert f'original source PDF pages {cfg["first_pdf"]}–{cfg["last_pdf"]}' in html
 assert f'{len(got)} main-text verses' in html
 assert f'for(let i=1;i<={len(cfg["chapter_counts"])};i++)' in html
 assert f'#{code}.{cfg["note_verse"][0]}.{cfg["note_verse"][1]}' in html
 assert 'Colossians' not in html and 'Romans' not in html and '#COL.' not in html and r'#COL\.' not in html and '#2TH.' not in html
 assert 'const canonical=(c,v)=>`2TI.${c}.${v}`' in html
 assert 'match=location.hash.match(/^#2TI\\.' in html
 assert 'About This Translation' in (bk/'README.md').read_text()
 scriptfile=bk/'scripts'/'__reader_syntax_check.js';scriptfile.write_text(scripts[0]);
 try:subprocess.run(['node','--check',str(scriptfile)],capture_output=True,check=True)
 finally:scriptfile.unlink(missing_ok=True)
 class QuietServer(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietServer,directory=str(root)))
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 paths=[f'/books/{slug}/site/index.html',f'/books/{slug}/index.html',
   f'/data/asv1901/{slug}/page-index.json',f'/data/asv1901/{slug}/chapters/01.json',
   f'/data/asv1901/{slug}/chapters/{len(cfg["chapter_counts"]):02d}.json',
   f'/data/asv1901/{slug}/verse-omissions.json',f'/data/asv1901/{slug}/textual-apparatus.json',
   f'/data/asv1901/{slug}/facsimile/{index["volumes"][0]["filename"]}']
 try:
  for path in paths:
   with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}{path}',timeout=12) as r:
    assert r.status==200 and r.read(),('HTTP_RESOURCE',path)
 finally:server.shutdown();server.server_close()
 audit={'status':'PASS','book_code':code,'edition_id':'ASV1901','chapters':len(cfg['chapter_counts']),
   'main_text_verse_count':len(got),'traditional_positions':len(expected),
   'original_source_3_hashes':'PASS','source_archive_hashes':'PINNED','source_witness_integrity':'PASS',
   'original_historical_pages':source_pages,'original_image_streams_verified':original_streams,
   'original_image_streams_and_placements':'PASS_ALL_SOURCE_PAGES',
   'rendered_pixel_comparisons':rendered_samples,'rendered_page_pixels':'PASS',
   'original_verse_index_coverage':'PASS_ALL_MAIN_TEXT_VERSES',
   'source_page_spanning_verses':len(crossing),
   'historical_map_pages':len(cfg['map_pages']),'historical_interleaves':len(cfg['interleaf_pages']),
   'book_schema':'PASS','release_manifest_sha256':'PASS',
   'translator_supplied_italic_spans':all_italics,'primary_usx_note_elements':note_count,
   'reader_javascript_syntax':'PASS','local_reader_http_resources':'PASS_8_OF_8',
   'real_browser_test':'NOT_PERFORMED',
   'source_witness_independence':'NOT_ESTABLISHED','exhaustive_character_by_character_print_proofreading':'NOT_PERFORMED',
   'strongs_alignment':'NOT_IMPORTED_UNVERIFIED','hosted_github_pages_test':'NOT_PERFORMED',
   'git_repository_change':'NONE','release_paths':[f'books/{slug}/',f'data/asv1901/{slug}/',f'data/asv1901/catalog-{slug}.json']}
 if write_audit:
  (bk/'INDEPENDENT_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
 return audit
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('pdf',type=Path);p.add_argument('--write-audit',action='store_true')
 args=p.parse_args();print(json.dumps(run(args.root,args.pdf,args.write_audit),indent=2))
