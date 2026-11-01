#!/usr/bin/env python3
"""Deterministic local production builder for a source-locked ASV 1901 Job edition.

This builds only when required real source inputs are present. It never writes
placeholder chapter text or invents historical page ranges. Does not call the network.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from collections import defaultdict
from xml.etree import ElementTree as ET

EXPECTED = [22, 13, 26, 21, 27, 30, 21, 22, 35, 22, 20, 25, 28, 22, 35, 22, 16, 21, 29, 29, 34, 30, 17, 25, 6, 14, 23, 28, 25, 31, 40, 22, 33, 37, 16, 33, 24, 41, 30, 24, 34, 17]
ROOT = Path(__file__).resolve().parents[3]


def hash_file(p):
    h = hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20), b''): h.update(chunk)
    return h.hexdigest()


def parse_usx(path):
    tree = ET.parse(path)
    root = tree.getroot()
    verses = {}; paragraphs = set(); active = None; current_chapter = None
    pending_paragraph = False

    def add(t, supplied=False):
        if not t or active is None: return
        items = verses[active]
        if items and items[-1]['supplied'] == supplied: items[-1]['text'] += t
        else: items.append({'text':t,'supplied':supplied})

    def walk(element, inside_note=False, supplied=False):
        nonlocal active,current_chapter,pending_paragraph
        tag=element.tag.split('}')[-1]
        if tag=='book': return
        if tag=='chapter':
            if element.get('number') is not None: current_chapter = int(element.get('number'))
            return
        if tag=='verse':
            if element.get('sid'):
                m=re.fullmatch(r'JOB\s+(\d+):(\d+)', element.get('sid',''))
                if m is None: raise ValueError(f'Unexpected verse SID: {element.get("sid")}')
                active = (int(m[1]),int(m[2]))
                if active in verses: raise ValueError(f'Duplicate verse: {active}')
                verses[active] = []
                if pending_paragraph: paragraphs.add(active)
                pending_paragraph = False
            elif element.get('eid'): active = None
            return
        if tag=='note': return  # Separate historic apparatus; not merged into clean Scripture
        if tag=='para':
            if element.get('style') in {'p','m','q1','q2','q3','pi','pi1','pi2'}:
                pending_paragraph=True
        if tag=='char' and element.get('style') in {'add','addpn'}:
            supplied=True
        if tag=='para' and element.get('style') in {'q1','q2','q3'} and active is not None and verses.get(active) and element.text:
            add('\n', supplied)
        add(element.text, supplied)
        for child in element:
            walk(child, supplied=supplied)
            add(child.tail, supplied)

    for child in root: walk(child)
    if set(ch for ch,v in verses)!={*range(1,43)}: raise ValueError('USX does not cover exactly Job 1-42')
    for ch, expected in enumerate(EXPECTED,1):
        actual = sorted(v for c,v in verses if c==ch)
        if actual != list(range(1,expected+1)): raise ValueError(f'Chapter {ch} expected 1..{expected}, got {actual}')
    if len(verses)!=1070: raise ValueError('Expected 1070 verses')
    rows={}
    for ch in range(1,43):
        out=[]
        for vs in range(1,EXPECTED[ch-1]+1):
            # Strip leading/trailing whitespace only across all segments, not within italics.
            parts=[dict(x) for x in verses[(ch,vs)]]
            if parts:
                parts[0]['text']=parts[0]['text'].lstrip()
                parts[-1]['text']=parts[-1]['text'].rstrip()
            parts=[x for x in parts if x['text']]
            if not parts: raise ValueError(f'Empty verse JOB.{ch}.{vs}')
            out.append({'id':f'JOB.{ch}.{vs}', 'edition_verse_id':f'ASV1901:JOB.{ch}.{vs}', 'verse':vs,
                        'spans':[{'text':x['text'],'kind':'supplied' if x['supplied'] else 'text'} for x in parts],
                        'paragraph_start':(ch,vs) in paragraphs})
        rows[ch]=out
    return rows


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def load_verse_index(rows):
    return {v['id']:''.join(part['text'] for part in v['spans']) for c in rows.values() for v in c}


def parse_usfm(path):
    """Return comparison-only English verse wording; never import unverified Strong's mapping.

    USFM word tags store English text before |strong. Notes, paragraph markers and
    Strong's labels are excluded, but translator-supplied word content is retained.
    """
    s=Path(path).read_text(encoding='utf-8-sig')
    matches=list(re.finditer(r'\\(c|v)\s+(\d+)',s))
    ch=None; result={}
    for i,m in enumerate(matches):
        if m.group(1)=='c':ch=int(m.group(2));continue
        if ch is None:raise ValueError('Verse before chapter')
        key=f'JOB.{ch}.{int(m.group(2))}'
        if key in result:raise ValueError('Duplicate USFM verse '+key)
        end=matches[i+1].start() if i+1<len(matches) else len(s)
        part=s[m.end():end]
        part=re.sub(r'\\w\s+([^|\\]+?)\|[^\\]*?\\w\*',lambda x:x.group(1),part)
        part=re.sub(r'\\(?:f|x)\s+.*?\\(?:f|x)\*',' ',part,flags=re.S)
        part=re.sub(r'\\[a-zA-Z0-9+]+\*?',' ',part)
        result[key]=norm(part)
    return result


def compare_norm(s):
    # Ignore formatting spaces: USX poetry lines and USFM standalone punctuation
    # have different whitespace. Preserve all punctuation and hyphens.
    return re.sub(r'\s+', '', s)


def compare_witnesses(rows, witness):
    canon=load_verse_index(rows)
    diffs=[]
    for key in sorted(canon, key=lambda k:tuple(int(x) for x in k.split('.')[1:])):
        rhs=witness.get(key)
        if rhs is None or compare_norm(canon[key])!=compare_norm(rhs):
            diffs.append({'id':key,'primary':norm(canon[key]),'comparison':rhs,
                          'status':'ORIGINAL_PRINT_CHECK_REQUIRED'})
    return diffs


def parse_ref(s):
    m=re.fullmatch(r'(?:JOB\.|Job\s+)(\d+)[.:](\d+)',s.strip(),re.I)
    if not m: raise ValueError(f'Invalid Job reference: {s}')
    c,v=int(m[1]),int(m[2]);
    if c<1 or c>42 or v<1 or v>EXPECTED[c-1]: raise ValueError(f'Out-of-range verse reference: {s}')
    return (c,v)


def load_page_index(path, pdf_count):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    pages=data.get('pages',[])
    if not pages: raise ValueError('Page index is empty. Real inspected page evidence is required.')
    indexed=[]
    for item in pages:
        n=item['source_pdf_page']
        if not (isinstance(n,int) and 1<=n<=pdf_count): raise ValueError(f'Bad source page {n}')
        typ=item['type']
        if typ=='scripture':
            lo,hi=parse_ref(item['first_verse']),parse_ref(item['last_verse'])
            if lo>hi: raise ValueError(f'Backwards range on page {n}')
            indexed.append((n,lo,hi))
        elif typ not in {'map','front_matter','interleaf','other_historical'}: raise ValueError(f'Unrecognized page type {typ}')
    if len({p['source_pdf_page'] for p in pages})!=len(pages): raise ValueError('Duplicate source PDF page')
    all_page_nums=sorted(p['source_pdf_page'] for p in pages)
    if all_page_nums != list(range(min(all_page_nums),max(all_page_nums)+1)):
        raise ValueError('Every physical page within the extracted book must be classified, including historical interleaves')
    indexed.sort()
    if not indexed: raise ValueError('No original Scripture pages indexed')
    # Gaps in SOURCE page first_chronicles require explicit non-scripture pages; gaps across verses are prohibited.
    all_verses=[(c,v) for c in range(1,43) for v in range(1,EXPECTED[c-1]+1)]
    coverage=defaultdict(list)
    for page,lo,hi in indexed:
        for verse in all_verses:
            if lo<=verse<=hi: coverage[verse].append(page)
    missing=[f'JOB.{c}.{v}' for (c,v) in all_verses if (c,v) not in coverage]
    if missing: raise ValueError(f'Uncovered verses: {missing[:12]} (total {len(missing)})')
    for p in pages:
        if p['type']=='scripture':
            k=parse_ref(p['first_verse']);m=parse_ref(p['last_verse'])
            # All duplicate ranges are allowed ONLY at a page boundary; do not infer positions.
    scripture_pages_sorted=[x[0] for x in indexed]
    for verse, pp in coverage.items():
        if len(pp)>2: raise ValueError(f'Verse {verse} spans >2 Scripture pages; manually investigate')
        if len(pp)==2 and scripture_pages_sorted.index(pp[1])!=scripture_pages_sorted.index(pp[0])+1:
            raise ValueError(f'Verse {verse} on nonconsecutive Scripture pages')
    return pages


def partition_pdf(pdf_path, index_pages, output, target_mb=8):
    import fitz
    doc=fitz.open(str(pdf_path))
    page_nums=sorted({x['source_pdf_page'] for x in index_pages})
    if not page_nums: raise ValueError('No PDF pages to extract')
    # Disjoint, consecutive full-page volumes, split again if actual compressed file sizes exceed target.
    volumes=[]; target=int(target_mb*1024*1024)
    def write_volume(nums):
        sub=fitz.open()
        for num in nums:sub.insert_pdf(doc,from_page=num-1,to_page=num-1)
        filename=f'asv1901-job-pages-{nums[0]:03d}-{nums[-1]:03d}.pdf'
        target_path=output/filename
        sub.save(str(target_path),garbage=3,deflate=True,no_new_id=True)
        sub.close()
        if target_path.stat().st_size>target and len(nums)>1:
            target_path.unlink()
            mid=len(nums)//2
            return write_volume(nums[:mid])+write_volume(nums[mid:])
        if target_path.stat().st_size>25*1024*1024:
            raise ValueError(f'An indivisible source page exceeds GitHub browser-upload limit: {filename}')
        return [{'filename':filename,'first_source_pdf_page':nums[0], 'last_source_pdf_page':nums[-1],
                'bytes':target_path.stat().st_size,'sha256':hash_file(target_path)}]
    for start in range(0,len(page_nums),24):volumes.extend(write_volume(page_nums[start:start+24]))
    lookup={}
    for v in volumes:
        for pos,num in enumerate(range(v['first_source_pdf_page'],v['last_source_pdf_page']+1),1):
            lookup[num]={'volume':v['filename'],'volume_pdf_page':pos}
    for p in index_pages:
        p.update(lookup.get(p['source_pdf_page'],{}))
    doc.close()
    return volumes


def build(args):
    import fitz
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    base=out/'data'/'asv1901'/'job'; chapters=base/'chapters';volumes_dir=base/'facsimile'
    chapters.mkdir(parents=True,exist_ok=True);volumes_dir.mkdir(parents=True,exist_ok=True)
    rows=parse_usx(args.primary_usx)
    witness=parse_usfm(args.comparison_usfm)
    differences=compare_witnesses(rows,witness)
    if differences and not args.resolution_record:
        raise ValueError(f'{len(differences)} digital disagreements. A source-verified resolution record is required.')
    if differences:
        resolutions=json.loads(Path(args.resolution_record).read_text(encoding='utf-8'))
        unresolved=[d['id'] for d in differences if resolutions.get(d['id'],{}).get('original_print_checked') is not True]
        if unresolved: raise ValueError(f'{len(unresolved)} unverified disagreements: {unresolved[:12]}')
        # Apply only specifically recorded, print-verified corrections to the derived text.
        # Source witness files are retained unchanged under books/job/sources.
        if set(resolutions)!=set(d['id'] for d in differences):
            raise ValueError('Resolution keys must exactly match detected source disagreements')
        for ident, record in sorted(resolutions.items()):
            correction=record.get('correction_to_derived_data')
            if not correction:
                if record.get('decision') in ('retain_primary_as_printed','retain_primary_with_print_linebreak_ambiguity'): continue
                raise ValueError(f'Missing print-backed derived correction for {ident}')
            _,c,v=ident.split('.');verse=rows[int(c)][int(v)-1]
            spans=verse['spans'];joined=''.join(x['text'] for x in spans)
            old,new=correction['from'],correction['to']
            if joined.count(old)!=1: raise ValueError(f'Expected unique correction target in {ident}: {old!r}')
            # For documented print-backed differences, the replacement resides
            # entirely in a single span and does not touch italic span boundaries.
            match=[x for x in spans if old in x['text']]
            if len(match)!=1 or match[0]['kind']!='text':
                raise ValueError(f'Unexpected span boundary for correction {ident}')
            match[0]['text']=match[0]['text'].replace(old,new,1)
    doc=fitz.open(args.original_pdf); page_count=len(doc);doc.close()
    pages=load_page_index(args.page_index,page_count)
    # Requires operator evidence: every chapter checked against original; not a flag auto-created by generator.
    inspections=json.loads(Path(args.chapter_checks).read_text(encoding='utf-8'))
    not_done=[c for c in range(1,43) if inspections.get(f'{c:02d}',{}).get('original_print_chapter_checked') is not True]
    if not_done:raise ValueError(f'Original-print chapter checks incomplete: {not_done}')
    for ch in range(1,43):
        data={'schema_version':'1.0.0','edition_id':'ASV1901','book_code':'JOB','chapter':ch,
              'verses':rows[ch]}
        (chapters/f'{ch:02d}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    vol_list=partition_pdf(Path(args.original_pdf),pages,volumes_dir,args.volume_target_mb)
    index={'schema_version':'1.0.0','edition_id':'ASV1901','book_code':'JOB','source_pdf_sha256':hash_file(args.original_pdf),
           'pages':pages,'volumes':vol_list,'navigation_rule':'ordered source PDF pages; lower number first'}
    (base/'page-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (base/'chapter-checks.json').write_text(json.dumps(inspections,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    hashes={str(f.relative_to(out)):hash_file(f) for tree in (out/'books/job',out/'data/asv1901/job') for f in sorted(tree.rglob('*')) if f.is_file() and f.name!='RELEASE_MANIFEST.json'}
    catalog=out/'data/asv1901/catalog-job.json'
    if catalog.is_file():hashes[str(catalog.relative_to(out))]=hash_file(catalog)
    manifest={'status':'STRUCTURALLY_BUILT_FROM_DECLARED_SOURCE','edition':'ASV1901','book':'JOB',
      'chapter_count':42,'verse_count':sum(map(len,rows.values())),'source_hashes':{
      'primary_usx':hash_file(args.primary_usx),'comparison_usfm':hash_file(args.comparison_usfm),
      'original_pdf':hash_file(args.original_pdf)},'files':hashes}
    (out/'books/job/RELEASE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--primary-usx',required=True,type=Path)
    parser.add_argument('--comparison-usfm',required=True,type=Path)
    parser.add_argument('--original-pdf',required=True,type=Path)
    parser.add_argument('--page-index',required=True,type=Path)
    parser.add_argument('--chapter-checks',required=True,type=Path)
    parser.add_argument('--resolution-record',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT)
    parser.add_argument('--volume-target-mb',type=float,default=8.0)
    args=parser.parse_args()
    try:print(json.dumps(build(args),indent=2))
    except Exception as e:
        print(f'BLOCKED: {e}',file=sys.stderr);sys.exit(1)
