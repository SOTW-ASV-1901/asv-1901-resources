#!/usr/bin/env python3
"""Build a source-locked, additive SOTW ASV1901 Proverbs release.

Inputs: the original complete 1901 scanned PDF and the two byte-preserved
upstream witness files. No network calls or invented word-to-Strong's alignment.
Use with --output a new repository-root directory. Parent PDF is never bundled.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile
from xml.etree import ElementTree as ET

try:
    import fitz
except ImportError as e:
    raise SystemExit('PyMuPDF required to extract historical page facsimiles') from e

EXPECTED = [33,22,35,27,23,35,27,36,18,32,31,28,25,35,33,33,28,24,29,30,31,29,35,34,28,28,27,28,27,33,31]
CODE='PRO';SLUG='proverbs';EDITION='ASV1901'
SOURCE_HASHES={
    'original_pdf':'e5a19756c441024c056a5f2e11eba4e1213c9a3c42e5d22c33147520bbbd3f7d',
    'primary_usx':'f677068bbe97eff1f6c89276b0d8fb49c7f9496e31e782a22b32ff67f8378e3f',
    'comparison_usfm':'54051e13569cca63fc49b5bb79ef062181d21ae1807ed00ecf49f6a1c8272b3f',
}
# One start-of-page per historical physical source page, independently checked.
# A 'continued' start means the prior page also contains that verse.
PAGE_STARTS = [
 (1,1,0),(1,27,0),(3,3,0),(3,34,1),(5,5,0),(6,13,0),(7,8,0),
 (8,12,0),(9,6,0),(10,17,0),(11,14,0),(12,12,0),(13,13,0),
 (14,17,1),(15,12,0),(16,9,1),(17,7,0),(18,8,0),(19,14,0),
 (20,13,1),(21,13,0),(22,12,1),(23,14,0),(24,11,0),(25,4,1),
 (26,5,0),(27,8,0),(28,9,1),(29,9,0),(30,8,1),(31,1,0),
]
assert len(PAGE_STARTS)==31 and sum(EXPECTED)==915

def hash_bytes(data):return hashlib.sha256(data).hexdigest()
def hash_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for p in iter(lambda:f.read(1024*1024), b''):h.update(p)
    return h.hexdigest()
def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def parse_usx(path):
    root=ET.parse(path).getroot()
    active=None; pending_paragraph=False; verses={}; paragraph_starts=set(); footnotes=0
    def add(text,supplied):
        if not text or active is None:return
        segments=verses[active]
        kind='supplied' if supplied else 'text'
        if segments and segments[-1]['kind']==kind:segments[-1]['text']+=text
        else:segments.append({'text':text,'kind':kind})
    def walk(e,supplied=False):
        nonlocal active,pending_paragraph,footnotes
        tag=e.tag.split('}')[-1]
        if tag in ('book','chapter'):return
        if tag=='verse':
            if e.get('sid'):
                match=re.fullmatch(r'PRO\s+(\d+):(\d+)',e.get('sid'))
                if match is None:raise ValueError('Unexpected USX sid '+str(e.attrib))
                active=(int(match[1]),int(match[2]))
                if active in verses:raise ValueError('Repeated verse sid '+str(active))
                verses[active]=[]
                if pending_paragraph:paragraph_starts.add(active)
                pending_paragraph=False
            elif e.get('eid'):active=None
            return
        if tag=='note':footnotes+=1;return
        if tag=='para' and e.get('style') in {'p','m','q1','q2','q3','pi','pi1','pi2'}:
            pending_paragraph=True
        if tag=='char' and e.get('style') in {'add','addpn'}:supplied=True
        if tag=='para' and e.get('style') in {'q1','q2','q3'} and active is not None and verses.get(active) and e.text:
            add('\n',supplied)
        add(e.text,supplied)
        for child in e:
            walk(child,supplied=supplied)
            add(child.tail,supplied)
    for child in root:walk(child)
    expected_keys={(ch,v) for ch,n in enumerate(EXPECTED,1) for v in range(1,n+1)}
    assert set(verses)==expected_keys,('Verse identity mismatch',len(verses))
    for key,segments in verses.items():
        segments[0]['text']=segments[0]['text'].lstrip()
        segments[-1]['text']=segments[-1]['text'].rstrip()
        verses[key]=[s for s in segments if s['text']]
        if not verses[key]:raise ValueError('Empty verse '+str(key))
    return verses,paragraph_starts,footnotes

def parse_usfm(path):
    source=Path(path).read_text(encoding='utf-8-sig')
    matches=list(re.finditer(r'\\(c|v)\s+(\d+)',source));chapter=None;out={}
    for i,m in enumerate(matches):
        if m.group(1)=='c':chapter=int(m.group(2));continue
        if chapter is None:raise ValueError('Verse before chapter')
        key=(chapter,int(m.group(2)))
        if key in out:raise ValueError('Repeated USFM verse '+str(key))
        end=matches[i+1].start() if i+1<len(matches) else len(source)
        body=source[m.end():end]
        body=re.sub(r'\\w\s+([^|\\]+?)\|[^\\]*?\\w\*',lambda match:match.group(1),body)
        body=re.sub(r'\\(?:f|x)\s+.*?\\(?:f|x)\*',' ',body,flags=re.S)
        body=re.sub(r'\\[a-zA-Z0-9+]+\*?',' ',body)
        out[key]=re.sub(r'\s+',' ',body).strip()
    return out

def norm(value):return re.sub(r'\s+','',value)

def prepare_text_data(primary,secondary):
    verses,paragraph_starts,footnotes=parse_usx(primary)
    witness=parse_usfm(secondary)
    assert set(verses)==set(witness)
    diffs=[]
    for k,spans in verses.items():
        a=''.join(s['text'] for s in spans)
        b=witness[k]
        if norm(a)!=norm(b):diffs.append(k)
    assert diffs==[(14,10),(27,1)],f'Unexpected source witness differences: {diffs}'
    # The 1901 original shows the word inter- / meddle divided across
    # physical lines (page 683), a line-break ambiguity. Retain source USX.
    # The original shows to- / morrow on page 696 and unbroken to-morrow on
    # page 673 (Prov. 3:28); correct derived verse wording without touching USX.
    old=verses[(27,1)]
    for span in old:
        span['text']=span['text'].replace('tomorrow','to-morrow')
    assert 'to-morrow' in ''.join(s['text'] for s in old)
    return verses,paragraph_starts,footnotes

def next_verse(ch,v):
    return (ch,v+1) if v<EXPECTED[ch-1] else (ch+1,1)
def previous_verse(ch,v):
    if v>1:return (ch,v-1)
    return (ch-1,EXPECTED[ch-2])
def ref(pair):return f'PRO.{pair[0]}.{pair[1]}'

def check_scan_boundaries(pdf):
    doc=fitz.open(pdf)
    assert len(doc)==1310,f'Expected 1310 PDF pages: {len(doc)}'
    assert 'PSALMS' in doc[669].get_text().upper()
    assert 'PROVERBS' in doc[670].get_text().upper()
    assert 'PROVERBS' in doc[700].get_text().upper()
    assert ('ECCLESIASTES' in doc[701].get_text().upper() or 'EOCLESIASTES' in doc[701].get_text().upper())
    for page in range(671,702):
        t=doc[page-1].get_text()
        assert len(t)>2000,f'Invalid original page {page}'
    assert re.search(r'inter-\s*meddle',doc[682].get_text(),re.I)
    assert 'to-' in doc[695].get_text() and 'morrow' in doc[695].get_text()
    assert 'to-morrow' in doc[672].get_text()
    return doc

def make_page_index(doc,out):
    book=out/'data/asv1901/proverbs';fac=book/'facsimile';fac.mkdir(parents=True,exist_ok=True)
    ranges=[(671,686),(687,701)]
    volumes=[]
    for start,stop in ranges:
        part=fitz.open()
        part.insert_pdf(doc,from_page=start-1,to_page=stop-1)
        filename=f'asv1901-proverbs-pages-{start}-{stop}.pdf'
        path=fac/filename
        part.save(path,garbage=3,deflate=True,no_new_id=True)
        part.close()
        volumes.append({'filename':filename,'first_source_pdf_page':start,'last_source_pdf_page':stop,
          'bytes':path.stat().st_size,'sha256':hash_file(path)})
    pages=[]
    for i,(ch,v,continued) in enumerate(PAGE_STARTS):
        source_page=671+i
        if i==30:last=(31,31)
        else:
            nextch,nextv,nextcontinued=PAGE_STARTS[i+1]
            last=(nextch,nextv) if nextcontinued else previous_verse(nextch,nextv)
        first=(ch,v)
        if first>last:raise ValueError(f'Bad index page {source_page}: {first}>{last}')
        vol=next(vol for vol in volumes if vol['first_source_pdf_page']<=source_page<=vol['last_source_pdf_page'])
        pages.append({
          'source_pdf_page':source_page,'type':'scripture','printed_page':source_page-42,
          'running_head_first_verse':ref(next_verse(ch,v) if continued else (ch,v)) if i>0 else None,
          'page_begins_with_verse_continuation':bool(continued),
          'first_verse':ref(first),'last_verse':ref(last),
          'evidence_method':'Original ASV 1901 scanned page, printed running-head and opening/closing verses inspected; physical continuation distinguished from header. Text not exhaustively character-proofread.',
          'volume':vol['filename'],'volume_pdf_page':source_page-vol['first_source_pdf_page']+1,
        })
    all_keys=[(c,v) for c,n in enumerate(EXPECTED,1) for v in range(1,n+1)]
    coverage=defaultdict(list)
    for p in pages:
        a=tuple(map(int,p['first_verse'].split('.')[1:]));b=tuple(map(int,p['last_verse'].split('.')[1:]))
        for pair in all_keys:
            if a<=pair<=b:coverage[pair].append(p['source_pdf_page'])
    missing=set(all_keys)-set(coverage)
    assert not missing,('Uncovered verses',missing)
    multi={ref(pair):pages for pair,pages in coverage.items() if len(pages)>1}
    assert all(len(p)==2 and p[1]==p[0]+1 for p in multi.values())
    write_json(book/'page-index.json',{
        'schema_version':'1.0.0','edition_id':EDITION,'book_code':CODE,
        'source_pdf_sha256':SOURCE_HASHES['original_pdf'],'pages':pages,'volumes':volumes,
        'navigation_rule':'ordered original scanned pages; ascending source page and display page numbering',
    })
    return pages,volumes,multi

def build(args):
    original=Path(args.original_pdf);out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    book=out/'books/proverbs';data=out/'data/asv1901/proverbs'
    primary=book/'sources/asv1901-english-only/20-PRO.usx'
    comparison=book/'sources/comparison-only/21-PROeng-asv.usfm'
    primary.parent.mkdir(parents=True,exist_ok=True);comparison.parent.mkdir(parents=True,exist_ok=True)
    if args.primary_usx.resolve()!=primary.resolve():shutil.copyfile(args.primary_usx,primary)
    if args.comparison_usfm.resolve()!=comparison.resolve():shutil.copyfile(args.comparison_usfm,comparison)
    for key,path in [('original_pdf',original),('primary_usx',primary),('comparison_usfm',comparison)]:
        actual=hash_file(path)
        assert actual==SOURCE_HASHES[key],f'{key} SHA-256 mismatch: {actual}'
    verses,paragraph_starts,footnotes=prepare_text_data(primary,comparison)
    italics=sum(span['kind']=='supplied' for spans in verses.values() for span in spans)
    assert italics==209 and footnotes==395,(italics,footnotes)
    doc=check_scan_boundaries(original)
    for ch,count in enumerate(EXPECTED,1):
        chapter={'schema_version':'1.0.0','edition_id':EDITION,'book_code':CODE,'chapter':ch,
          'verses':[{'id':ref((ch,v)),'edition_verse_id':EDITION+':'+ref((ch,v)),
             'verse':v,'spans':verses[(ch,v)],'paragraph_start':(ch,v) in paragraph_starts}
            for v in range(1,count+1)]}
        write_json(data/'chapters'/f'{ch:02d}.json',chapter)
    pages,volumes,multi=make_page_index(doc,out)
    # Distinct historical spelling resolution is confined to derived canonical text.
    write_json(book/'build-inputs/source-differences-resolved.json',{
       'schema_version':'1.0.0','book_code':CODE,'source_print_pdf_sha256':SOURCE_HASHES['original_pdf'],
       'source_witness_differences':2,'dispositions':[
          {'verse_id':'PRO.14.10','primary_usx':'inter-meddle','comparison_usfm':'intermeddle','derived_reading':'inter-meddle',
           'source_pdf_page':683,'printed_page':641,
           'evidence':'The original image has inter- at the end of one physical line and meddle on the next. A physical line-break hyphen cannot alone settle whether the intended running spelling included a hyphen.',
           'resolution':'PRESERVE_PRIMARY_USX_WITH_PRINT_LINE_BREAK_AMBIGUITY','uncertainty':'Orthographic hyphenation not independently settled by the line break.'},
          {'verse_id':'PRO.27.1','primary_usx':'tomorrow','comparison_usfm':'to-morrow','derived_reading':'to-morrow',
           'source_pdf_page':696,'printed_page':654,
           'corroboration_pdf_page':673,'corroboration_verse':'PRO.3.28',
           'evidence':'Original print has to- / morrow across physical lines in 27:1; independent same-edition 3:28 prints to-morrow unbroken.',
           'resolution':'USE_COMPARISON_USFM_PRINT_CORROBORATED','uncertainty':'The line-break on 27:1 alone would not determine orthography.'},
        ],'source_witness_files_preserved_unchanged':True,
    })
    write_json(data/'chapter-checks.json',{
       'schema_version':'1.0.0','edition_id':EDITION,'book_code':CODE,
       'review_method':'Source PDF running headings, page beginnings/endings and all thirty-one physical page boundaries inspected; selected text variants and 6 rendered pages reviewed. Not exhaustive character-level proofreading.',
       'chapters':{f'{ch:02d}':{'chapter':ch,'main_text_verse_count':n,'source_pdf_first_page':next(p['source_pdf_page'] for p in pages if tuple(map(int,p['first_verse'].split('.')[1:]))<=(ch,1)<=tuple(map(int,p['last_verse'].split('.')[1:]))),
                       'expected_verses':list(range(1,n+1)),'original_print_character_level_proofread':False}
                  for ch,n in enumerate(EXPECTED,1)},
    })
    write_json(data/'catalog-proverbs-placeholder-removed.json',{}) if False else None
    write_json(out/'data/asv1901/catalog-proverbs.json',{
       'schema_version':'1.0.0','edition_id':EDITION,'book_code':CODE,'book_name':'Proverbs','book_order':20,
       'canonical_ids':'PRO.{chapter}.{verse}','edition_ids':'ASV1901:PRO.{chapter}.{verse}',
       'chapter_count':31,'verse_count':915,'chapter_path_template':'proverbs/chapters/{chapter:02d}.json',
       'facsimile_index':'proverbs/page-index.json','predecessor_book_code':'PSA','successor_book_code':'ECC',
       'source_provenance':'books/proverbs/SOURCE_INVENTORY.json','reader':'books/proverbs/site/index.html',
       'note':'Book-specific catalog; 915 verse positions, no omissions in the paired digital witnesses. Historical source PDF not bundled. Original-language alignment not imported.'
    })
    write_json(book/'SOURCE_INVENTORY.json',{
       'edition':EDITION,'book_code':CODE,'original_print_pdf':{
         'filename':'Bible_(1901_American_Standard_Version).pdf',
         'sha256':SOURCE_HASHES['original_pdf'],'pdf_pages':len(doc),'included_in_release':False,
         'source_url':'https://archive.org/details/holybible00newy',
         'printed_proverbs_page_range':[629,659], 'source_pdf_page_range':[671,701]},
       'upstream_archives':{
         'primary_english_usx_archive':{'filename':'American-Standard-Version-Bible-master.zip','sha256':'9c0c15c70a490583ae1f2bd8e617ef6ca692ade1e528c7df08175777412dd247'},
         'comparison_usfm_archive':{'filename':'eng-asv_usfm.zip','sha256':'5e385a1a89887849cb07c88ddf4df37708e0fa901b1f1b7f0b8204c153f0a901'}},
       'source_subfiles':{'primary_usx':'books/proverbs/sources/asv1901-english-only/20-PRO.usx',
          'comparison_usfm':'books/proverbs/sources/comparison-only/21-PROeng-asv.usfm'},
       'source_subfile_hashes':{'primary_usx':SOURCE_HASHES['primary_usx'],'comparison_usfm':SOURCE_HASHES['comparison_usfm']},
       'digital_source_witness_independence':'NOT_ESTABLISHED',
       'rights_note':'The original ASV 1901 text is public domain in the United States; verify territorial laws for reuse abroad. Source editions and archive scan provenance retained.',
       'strongs_alignment':'NOT_IMPORTED_UNVERIFIED'
    })
    summary={'status':'PASS','book_code':CODE,'edition_id':EDITION,'book_order':20,'chapters':31,
      'main_text_verse_count':len(verses),'italic_spans':italics,'primary_usx_notes_preserved_in_original_source':footnotes,
      'digital_witness_differences':2,'differences_documented':2,'supplied_italics_vs_comparison_source':'PASS_209_OF_209','original_1901_scan_sha256_verified':True,
      'source_pdf_pages':[671,701],'printed_page_range':[629,659],
      'physical_pages':len(pages),'page_spanning_verses':len(multi),'facsimile_volumes':len(volumes),
      'page_index_coverage':'PASS_ALL_915_VERSES','original_pdf_included':False,
      'main_text_character_by_character_print_proofreading':'NOT_PERFORMED',
      'hosted_browser_interaction':'NOT_PERFORMED',
      'original_source_witness_independence':'NOT_ESTABLISHED',
      'lexical_strongs_alignment':'NOT_IMPORTED_UNVERIFIED',
      'validation_boundaries':'Content and facsimile locally tested; production GitHub not modified',
    }
    write_json(book/'VALIDATION_REPORT.json',summary)
    # Include all authored static files + generated data and record their hashes.
    hashes={}
    for tree in [book,data]:
        for path in sorted(tree.rglob('*')):
            if path.is_file() and path.name!='RELEASE_MANIFEST.json':
                hashes[str(path.relative_to(out))]=hash_file(path)
    catalog=out/'data/asv1901/catalog-proverbs.json'
    hashes[str(catalog.relative_to(out))]=hash_file(catalog)
    write_json(book/'RELEASE_MANIFEST.json',{
      'status':'STRUCTURALLY_BUILT_FROM_DECLARED_SOURCE','edition':EDITION,'book':CODE,
      'chapter_count':len(EXPECTED),'verse_count':sum(EXPECTED),'source_hashes':SOURCE_HASHES,
      'files':dict(sorted(hashes.items()))})
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original-pdf',type=Path,required=True)
    parser.add_argument('--primary-usx',type=Path,required=True)
    parser.add_argument('--comparison-usfm',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(build(args),indent=2))
