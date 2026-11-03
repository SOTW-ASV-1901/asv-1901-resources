#!/usr/bin/env python3
"""Independently validate the additive SOTW ASV1901 Proverbs book release.

Pass --original-pdf for exact parent-scan image/page placements and rendered
pixel comparisons; otherwise only package-internal integrity is established.
"""
import argparse
import hashlib
import json
import re
import sys
from xml.etree import ElementTree as ET
from collections import defaultdict
from pathlib import Path

import fitz
from jsonschema import Draft202012Validator

CHAPTER_COUNTS=[33,22,35,27,23,35,27,36,18,32,31,28,25,35,33,33,28,24,29,30,31,29,35,34,28,28,27,28,27,33,31]
BOOK='PRO';SLUG='proverbs';EDITION='ASV1901'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda:f.read(1<<20),b''):h.update(data)
    return h.hexdigest()
def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def tpair(ref):
    match=re.fullmatch(r'PRO\.(\d+)\.(\d+)',ref)
    if not match:raise ValueError(f'Wrong reference {ref}')
    return tuple(map(int,match.groups()))

def run(root,original_pdf=None):
    root=Path(root);bk=root/'books'/SLUG;data=root/'data/asv1901'/SLUG
    manifest=load(bk/'RELEASE_MANIFEST.json')
    assert manifest['book']==BOOK and manifest['chapter_count']==31 and manifest['verse_count']==915
    for rel,h in manifest['files'].items():
        path=root/rel
        assert path.is_file(),f'Missing file {rel}'
        assert sha(path)==h,f'Hash mismatch: {rel}'
    actual_files={str(p.relative_to(root)) for folder in (bk,data) for p in folder.rglob('*') if p.is_file() and p.name!='RELEASE_MANIFEST.json'}
    actual_files.add('data/asv1901/catalog-proverbs.json')
    assert set(manifest['files'])==actual_files,'Manifest path coverage mismatch'
    assert len(actual_files)+1<=99
    catalog=load(root/'data/asv1901/catalog-proverbs.json')
    assert catalog['book_code']==BOOK and catalog['verse_count']==915 and catalog['chapter_count']==31
    assert catalog['predecessor_book_code']=='PSA' and catalog['successor_book_code']=='ECC'
    inventory=load(bk/'SOURCE_INVENTORY.json')
    source=inventory['source_subfiles'];source_hashes=inventory['source_subfile_hashes']
    for typ in ('primary_usx','comparison_usfm'):
        assert sha(root/source[typ])==source_hashes[typ]==manifest['source_hashes'][typ]
    assert inventory['original_print_pdf']['sha256']==manifest['source_hashes']['original_pdf']
    # Independently cross-check every translator-supplied word span against
    # the other (USFM) witness, not just the primary USX derived JSON.
    raw_usx=(root/source['primary_usx']).read_bytes()
    raw_usfm=(root/source['comparison_usfm']).read_text(encoding='utf-8-sig')
    usx_supplied=defaultdict(list);active=None
    for element in ET.fromstring(raw_usx).iter():
        tag=element.tag.split('}')[-1]
        if tag=='verse':
            if element.get('sid'):
                m=re.fullmatch(r'PRO\s+(\d+):(\d+)',element.get('sid'))
                if m:active=(int(m[1]),int(m[2]))
            elif element.get('eid'):active=None
        elif tag=='char' and element.get('style') in ('add','addpn') and active is not None:
            usx_supplied[active].append(re.sub(r'\s+','', ''.join(element.itertext())))
    usfm_supplied=defaultdict(list);chapter=None
    matches=list(re.finditer(r'\\(c|v)\s+(\d+)',raw_usfm))
    for i,match in enumerate(matches):
        if match[1]=='c':chapter=int(match[2]);continue
        assert chapter is not None
        key=(chapter,int(match[2]));end=matches[i+1].start() if i+1<len(matches) else len(raw_usfm)
        body=raw_usfm[match.end():end]
        usfm_supplied[key]=[re.sub(r'\s+','',x) for x in re.findall(r'\\add\s*(.*?)\\add\*',body,re.S)]
    assert sum(len(x) for x in usx_supplied.values())==209
    assert sum(len(x) for x in usfm_supplied.values())==209
    for chapter,verse in [(ch,v) for ch,count in enumerate(CHAPTER_COUNTS,1) for v in range(1,count+1)]:
        assert usx_supplied[(chapter,verse)]==usfm_supplied[(chapter,verse)],('Italic mismatch',chapter,verse)
    schema=load(bk/'schemas/asv1901-proverbs-chapter.schema.json')
    pschema=load(bk/'schemas/facsimile-page-index.schema.json')
    validator=Draft202012Validator(schema)
    total=0;italics=0;seen=set()
    for chapter,expected_count in enumerate(CHAPTER_COUNTS,1):
        ch=load(data/'chapters'/f'{chapter:02d}.json');validator.validate(ch)
        assert ch['chapter']==chapter and len(ch['verses'])==expected_count
        actual_ids=[]
        for n,entry in enumerate(ch['verses'],1):
            assert entry['verse']==n
            key=f'PRO.{chapter}.{n}'
            assert entry['id']==key and entry['edition_verse_id']=='ASV1901:'+key
            assert entry['spans'] and ''.join(s['text'] for s in entry['spans']).strip()
            actual_ids.append(key);seen.add(key)
            italics+=sum(s['kind']=='supplied' for s in entry['spans'])
        assert len(set(actual_ids))==expected_count
        total+=len(ch['verses'])
    assert total==915 and len(seen)==915 and italics==209
    first=load(data/'chapters/01.json')['verses'][0]
    last=load(data/'chapters/31.json')['verses'][-1]
    assert 'The proverbs of Solomon' in ''.join(s['text'] for s in first['spans'])
    assert 'her works praise her in the gates' in ''.join(s['text'] for s in last['spans'])
    resolved=load(bk/'build-inputs/source-differences-resolved.json')
    assert len(resolved['dispositions'])==2
    assert [x['verse_id'] for x in resolved['dispositions']]==['PRO.14.10','PRO.27.1']
    ch14=load(data/'chapters/14.json')['verses'][9]
    ch27=load(data/'chapters/27.json')['verses'][0]
    assert 'inter-meddle' in ''.join(s['text'] for s in ch14['spans'])
    assert 'to-morrow' in ''.join(s['text'] for s in ch27['spans'])
    idx=load(data/'page-index.json');Draft202012Validator(pschema).validate(idx)
    assert [p['source_pdf_page'] for p in idx['pages']]==list(range(671,702))
    assert [p['printed_page'] for p in idx['pages']]==list(range(629,660))
    assert idx['source_pdf_sha256']==manifest['source_hashes']['original_pdf']
    coverage=defaultdict(list)
    for page in idx['pages']:
        a,b=tpair(page['first_verse']),tpair(page['last_verse'])
        assert a<=b
        for chapter,count in enumerate(CHAPTER_COUNTS,1):
            for verse in range(1,count+1):
                if a<=(chapter,verse)<=b:coverage[f'PRO.{chapter}.{verse}'].append(page['source_pdf_page'])
    assert set(coverage)==seen
    overlaps={k:pages for k,pages in coverage.items() if len(pages)>1}
    assert len(overlaps)==8
    assert all(len(pages)==2 and pages[1]==pages[0]+1 for pages in overlaps.values())
    vols=idx['volumes'];assert len(vols)==2
    for vol in vols:
        pp=data/'facsimile'/vol['filename']
        assert pp.exists() and pp.stat().st_size==vol['bytes'] and sha(pp)==vol['sha256']
        with fitz.open(pp) as d:assert len(d)==vol['last_source_pdf_page']-vol['first_source_pdf_page']+1
    for page in idx['pages']:
        matching=[v for v in vols if v['first_source_pdf_page']<=page['source_pdf_page']<=v['last_source_pdf_page']]
        assert len(matching)==1 and page['volume']==matching[0]['filename']
        assert page['volume_pdf_page']==page['source_pdf_page']-matching[0]['first_source_pdf_page']+1
    report={'status':'PASS','edition_id':EDITION,'book_code':BOOK,'files_in_upload':len(actual_files)+1,
      'chapters':31,'verses':915,'italic_spans':209,'facsimile_pages':31,
      'supplied_italics_vs_comparison_source':'PASS_209_OF_209',
      'page_spanning_verses':8,'files_manifest_sha256':'PASS',
      'schemas':'PASS','chapter_ids':'PASS','source_file_hashes':'PASS',
      'source_print_pdf_sha256':'PARENT_SOURCE_NOT_PROVIDED_FOR_RECHECK',
      'embedded_source_page_image_streams_and_placements':'PARENT_SOURCE_NOT_PROVIDED_FOR_RECHECK',
      'rendered_page_pixel_comparisons':'PARENT_SOURCE_NOT_PROVIDED_FOR_RECHECK'}
    if original_pdf:
        assert sha(original_pdf)==idx['source_pdf_sha256'],'Original PDF hash differs from locked source'
        parent=fitz.open(original_pdf)
        assert len(parent)==1310
        comp=0
        for vol in vols:
            with fitz.open(data/'facsimile'/vol['filename']) as subset:
                for i,original_pageno in enumerate(range(vol['first_source_pdf_page'],vol['last_source_pdf_page']+1)):
                    source_pg=parent[original_pageno-1];child_pg=subset[i]
                    assert source_pg.rect==child_pg.rect
                    source_images=source_pg.get_images(full=True)
                    child_images=child_pg.get_images(full=True)
                    assert len(source_images)==len(child_images),('Embedded image count',original_pageno)
                    for src,child in zip(source_images,child_images):
                        assert src[2:8]==child[2:8],('Embedded image descriptors differ',original_pageno)
                        assert hashlib.sha256(parent.xref_stream_raw(src[0])).digest()==hashlib.sha256(subset.xref_stream_raw(child[0])).digest(),('Embedded original compressed image streams differ',original_pageno)
                        assert source_pg.get_image_rects(src[0])==child_pg.get_image_rects(child[0]),('Image placement differs',original_pageno)
                    comp+=1
                for original_pageno in [671,673,683,687,696,701]:
                    if vol['first_source_pdf_page']<=original_pageno<=vol['last_source_pdf_page']:
                        matrix=fitz.Matrix(0.8,0.8)
                        src_pixels=parent[original_pageno-1].get_pixmap(matrix=matrix,alpha=False)
                        out_pixels=subset[original_pageno-vol['first_source_pdf_page']].get_pixmap(matrix=matrix,alpha=False)
                        assert src_pixels.samples==out_pixels.samples,('Rendered pixels differ',original_pageno)
        report['source_print_pdf_sha256']='PASS'
        report['embedded_source_page_image_streams_and_placements']=f'PASS_{comp}_OF_31'
        report['rendered_page_pixel_comparisons']='PASS_6_SELECTED_PAGES_0.8X'
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo-root',type=Path,default=Path('.'))
    ap.add_argument('--original-pdf',type=Path)
    args=ap.parse_args()
    try:print(json.dumps(run(args.repo_root,args.original_pdf),indent=2))
    except Exception as exc:
        print(f'FAIL: {type(exc).__name__}: {exc}',file=sys.stderr)
        raise
