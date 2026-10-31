#!/usr/bin/env python3
from pathlib import Path
import sys,json,hashlib,collections
import fitz
from jsonschema import Draft202012Validator

def check(root):
    root=Path(root).resolve();book=root/'books/exodus';dat=root/'data/asv1901/exodus'
    man=json.loads((book/'RELEASE_MANIFEST.json').read_text());assert man['book']=='EXO'
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for rel,hash_expected in man['files'].items():
        p=root/rel
        assert p.is_file() and sha(p)==hash_expected,f'File missing or changed: {rel}'
    schema=json.loads((book/'schemas/asv1901-exodus-chapter.schema.json').read_text())
    idxschema=json.loads((book/'schemas/facsimile-page-index.schema.json').read_text())
    counts=[22,25,22,31,23,30,25,32,35,29,10,51,22,31,27,36,16,27,25,26,36,31,33,18,40,37,21,43,46,38,18,35,23,35,35,38,29,31,43,38]
    refs=set();sup=0
    for ch,n in enumerate(counts,1):
        c=json.loads((dat/'chapters'/f'{ch:02d}.json').read_text());Draft202012Validator(schema).validate(c)
        assert c['book_code']=='EXO' and c['chapter']==ch and len(c['verses'])==n
        for v in c['verses']:
            k=f'EXO.{ch}.{v["verse"]}';assert v['id']==k and v['edition_verse_id']=='ASV1901:'+k and k not in refs
            refs.add(k);sup+=sum(s['kind']=='supplied' for s in v['spans'])
    assert len(refs)==1213 and sup==83
    index=json.loads((dat/'page-index.json').read_text());Draft202012Validator(idxschema).validate(index)
    pages=index['pages'];assert [p['source_pdf_page'] for p in pages]==list(range(77,123))
    assert collections.Counter(p['type'] for p in pages)=={'scripture':44,'map':1,'interleaf':1}
    vol={v['filename']:v for v in index['volumes']};assert len(vol)==2
    for name,info in vol.items():
        p=dat/'facsimile'/name;assert p.stat().st_size==info['bytes'] and sha(p)==info['sha256']
        doc=fitz.open(p);assert len(doc)==info['last_source_pdf_page']-info['first_source_pdf_page']+1;doc.close()
    for p in pages:
        assert p['volume'] in vol
        assert p['volume_pdf_page']==p['source_pdf_page']-vol[p['volume']]['first_source_pdf_page']+1
    def asref(k):return tuple(map(int,k.split('.')[1:]))
    for key in refs:
        position=asref(key)
        match=[p['source_pdf_page'] for p in pages if p['type']=='scripture' and asref(p['first_verse'])<=position<=asref(p['last_verse'])]
        assert len(match) in (1,2),f'No page match: {key}'
        if len(match)==2:
            scripture_pages=[p['source_pdf_page'] for p in pages if p['type']=='scripture']
            assert scripture_pages.index(match[1])==scripture_pages.index(match[0])+1
    print(json.dumps({'result':'PASS','chapters':40,'verses':1213,'italic_spans':83,'historical_pages':46,'volumes':2,'SHA256_files':len(man['files'])},indent=2))
if __name__=='__main__':check(sys.argv[1] if len(sys.argv)>1 else '.')
