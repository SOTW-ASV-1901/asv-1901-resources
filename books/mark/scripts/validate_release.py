#!/usr/bin/env python3
"""Independent Mark ASV1901 integrity validator for a manual GitHub upload.

Reads a repository-root directory. Original PDF used only for page-level tests
when supplied by --original-pdf, not embedded in the public release.
"""
import argparse, hashlib, json, re, zipfile
from collections import defaultdict
from pathlib import Path
import fitz
from jsonschema import Draft202012Validator
TRAD=[45,28,35,41,43,56,37,38,50,52,33,44,37,72,47,20]
OMIT={(7,16),(9,44),(9,46),(11,26),(15,28)}

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for part in iter(lambda:f.read(1048576),b''):h.update(part)
 return h.hexdigest()

def run(root,original_pdf=None,render_compare=False):
 root=Path(root);book=root/'books/mark';data=root/'data/asv1901/mark'
 manifest=json.loads((book/'RELEASE_MANIFEST.json').read_text())
 assert manifest['book']=='MRK' and manifest['chapter_count']==16 and manifest['verse_count']==673
 local_files={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 assert local_files==set(manifest['files'])|{'books/mark/RELEASE_MANIFEST.json'},(local_files-set(manifest['files']))
 for rel,hashval in manifest['files'].items():assert sha(root/rel)==hashval,rel
 schema=json.loads((book/'schemas/asv1901-mark-chapter.schema.json').read_text())
 page_schema=json.loads((book/'schemas/facsimile-page-index.schema.json').read_text())
 versekeys=[];supplied=0
 for chapter,n in enumerate(TRAD,1):
  obj=json.loads((data/f'chapters/{chapter:02d}.json').read_text())
  Draft202012Validator(schema).validate(obj)
  assert obj['chapter']==chapter
  expected=[v for v in range(1,n+1) if (chapter,v) not in OMIT]
  assert [v['verse'] for v in obj['verses']]==expected,(chapter,expected)
  for item in obj['verses']:
   ref=f'MRK.{chapter}.{item["verse"]}'
   assert item['id']==ref and item['edition_verse_id']=='ASV1901:'+ref
   assert item['spans'] and all(x['text'] and x['kind'] in ('text','supplied') for x in item['spans'])
   supplied+=sum(x['kind']=='supplied' for x in item['spans']);versekeys.append((chapter,item['verse']))
 assert len(versekeys)==673 and supplied==95
 idx=json.loads((data/'page-index.json').read_text());Draft202012Validator(page_schema).validate(idx)
 assert [p['source_pdf_page'] for p in idx['pages']]==list(range(1012,1035))
 assert idx['pages'][0]['type']=='map'
 coverage=defaultdict(list)
 for p in idx['pages'][1:]:
  a,b=[tuple(map(int,p[k].split('.')[1:])) for k in ('first_verse','last_verse')]
  assert a<=b
  for key in versekeys:
   if a<=key<=b:coverage[key].append(p['source_pdf_page'])
 assert set(coverage)==set(versekeys)
 cross={key:val for key,val in coverage.items() if len(val)==2}
 assert len(cross)==19
 assert all(val[1]==val[0]+1 for val in cross.values())
 exc=json.loads((data/'verse-omissions.json').read_text())['omissions']
 assert {tuple(map(int,o['verse_id'].split('.')[1:])) for o in exc}==OMIT
 assert all(o['status']=='NOT_IN_1901_MAIN_TEXT' for o in exc)
 note=json.loads((data/'textual-apparatus.json').read_text())['apparatus']
 assert len(note)==1 and note[0]['passage']=='MRK.16.9-MRK.16.20'
 assert note[0]['main_text_status']=='PRESENT_IN_ASV1901_MAIN_TEXT'
 for vol in idx['volumes']:
  path=data/'facsimile'/vol['filename']
  assert path.stat().st_size==vol['bytes'] and sha(path)==vol['sha256']
  with fitz.open(path) as d:
   assert len(d)==vol['last_source_pdf_page']-vol['first_source_pdf_page']+1
 if original_pdf:
  assert sha(original_pdf)==manifest['source_hashes']['original_pdf']
  with fitz.open(original_pdf) as parent:
   for vol in idx['volumes']:
    with fitz.open(data/'facsimile'/vol['filename']) as child:
     for i,page in enumerate(range(vol['first_source_pdf_page'],vol['last_source_pdf_page']+1)):
      a=parent[page-1];b=child[i]
      assert (round(a.rect.width,6),round(a.rect.height,6))==(round(b.rect.width,6),round(b.rect.height,6))
      assert a.get_text()==b.get_text(),('text layer changed',page)
      ia=a.get_images(full=True);ib=b.get_images(full=True)
      assert len(ia)==len(ib),(page,'image count')
      for x,y in zip(ia,ib):
       assert a.parent.xref_stream_raw(x[0])==b.parent.xref_stream_raw(y[0]),('embedded-image-bytes',page)
       assert a.get_image_rects(x[0])==b.get_image_rects(y[0]),('image placement',page)
      if render_compare and page in (1012,1013,1018,1024,1033,1034):
       m=fitz.Matrix(.3,.3);pa=a.get_pixmap(matrix=m,alpha=False);pb=b.get_pixmap(matrix=m,alpha=False)
       assert pa.samples==pb.samples,('render pixel difference',page)
 html=(book/'site/index.html').read_text();assert 'Mark 16:9' in html and 'MRK.' in html
 assert 'Strong' in html and 'No unverified' in html
 return {'status':'PASS','book':'MRK','chapters':16,'main_text_verses':673,
  'traditional_positions':678,'omitted_verses':5,'supplied_spans':95,'source_original_pages':23,
  'page_spanning_verses':19,'release_sha256_files':len(manifest['files']),
  'original_parent_pdf_compared':bool(original_pdf),'rendered_pixel_compared_pages':6 if (original_pdf and render_compare) else 0}

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('root');parser.add_argument('--original-pdf');parser.add_argument('--render-compare',action='store_true')
 args=parser.parse_args();print(json.dumps(run(args.root,args.original_pdf,args.render_compare),indent=2))
