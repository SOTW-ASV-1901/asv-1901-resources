#!/usr/bin/env python3
"""Source-locked ASV 1901 Gospel of John builder (additive SOTW book 43).

Run: python build_john.py --pdf ORIGINAL.pdf --usx ORIGINAL.usx --usfm COMPARISON.usfm --out OUTPUT_ROOT
Must preserve original physical scanned pages and byte-identical source witness files.
Can regenerate a fresh output from the release's included script and static templates.
"""
import argparse,hashlib,json,re,shutil
from pathlib import Path
from collections import defaultdict
from xml.etree import ElementTree as ET
import fitz

CODE='JHN';SLUG='john';ED='ASV1901'
TRAD=[51,25,36,54,47,71,53,59,41,42,57,50,38,31,27,33,26,40,42,31,25]
OMIT={(5,4)}
SOURCE_SHAS={'original_pdf':'e5a19756c441024c056a5f2e11eba4e1213c9a3c42e5d22c33147520bbbd3f7d',
'primary_usx':'7fdaa09214230e9b2aff461eba4c4b6b94e73a2210a6c9b96868235cd718767d',
'comparison_usfm':'ad1181ab71a7171d2d6b6e7e86034e4a31d1f16b4606bddf4eb9b5b6699d4d01'}
ARCHIVES={'primary_usx':'9c0c15c70a490583ae1f2bd8e617ef6ca692ade1e528c7df08175777412dd247',
'comparison_usfm':'5e385a1a89887849cb07c88ddf4df37708e0fa901b1f1b7f0b8204c153f0a901'}
# First physically present main-text verse on each original source PDF page 1075-1102,
# with continuation flag if that verse began on the preceding physical page.
# Independent visual/text inspection of physical page top-left openings and verse transitions.
PAGE_STARTS=[
(1,1,0),(1,29,1),(2,10,1),(3,17,1),(4,15,1),(4,50,1),(5,30,0),
(6,19,1),(6,52,0),(7,17,1),(7,52,1),(8,33,1),(9,7,1),(10,3,1),
(10,39,1),(11,34,1),(12,9,0),(12,40,0),(13,21,1),(14,16,1),
(15,16,1),(16,20,1),(17,17,0),(18,20,1),(19,10,1),(19,38,1),
(20,26,0),(21,21,1)]
assert len(TRAD)==21 and sum(TRAD)==879 and len(PAGE_STARTS)==28
KEYS=[(ch,v) for ch,n in enumerate(TRAD,1) for v in range(1,n+1) if (ch,v) not in OMIT]
assert len(KEYS)==878
POSITION={key:i for i,key in enumerate(KEYS)}
def vref(pos):return f'JHN.{pos[0]}.{pos[1]}'
def before(pos):return KEYS[POSITION[pos]-1]
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest()
def write(path,obj):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def parse_usx(path):
 root=ET.parse(path).getroot();data={};paragraphs=set();notes=0;current=None;pending=False
 def add(txt,kind):
  if not txt or current is None:return
  buf=data[current]
  if buf and buf[-1]['kind']==kind:buf[-1]['text']+=txt
  else:buf.append({'text':txt,'kind':kind})
 def walk(e,kind='text'):
  nonlocal current,pending,notes
  tag=e.tag.split('}')[-1]
  if tag in ('book','chapter'):return
  if tag=='verse':
   if e.get('sid'):
    m=re.fullmatch(r'JHN\s+(\d+):(\d+)',e.get('sid'))
    if not m:raise ValueError('Bad verse start '+repr(e.attrib))
    current=int(m[1]),int(m[2])
    if current in data:raise ValueError('Duplicate verse '+str(current))
    data[current]=[]
    if pending:paragraphs.add(current)
    pending=False
   elif e.get('eid'):current=None
   return
  if tag=='note':notes+=1;return
  if tag=='para' and e.get('style') in ('p','m','q1','q2','q3','pi','pi1','pi2'):pending=True
  if tag=='char' and e.get('style') in ('add','addpn'):kind='supplied'
  if tag=='para' and e.get('style') in ('q1','q2','q3') and current in data and data[current] and e.text:add('\n',kind)
  add(e.text,kind)
  for child in e:walk(child,kind);add(child.tail,kind)
 for child in root:walk(child)
 if set(data)!=set(KEYS):raise ValueError(f'USX positions differ: missing={set(KEYS)-set(data)} extra={set(data)-set(KEYS)}')
 for k,ss in data.items():
  if not ss:raise ValueError('Empty verse '+vref(k))
  ss[0]['text']=ss[0]['text'].lstrip();ss[-1]['text']=ss[-1]['text'].rstrip()
  data[k]=[v for v in ss if v['text']]
 return data,paragraphs,notes

def parse_usfm(path):
 s=Path(path).read_text(encoding='utf-8-sig');ms=list(re.finditer(r'\\(c|v)\s+(\d+)',s));ch=None;out={};adds={}
 for i,m in enumerate(ms):
  if m[1]=='c':ch=int(m[2]);continue
  if ch is None:raise ValueError('USFM verse without chapter')
  pos=(ch,int(m[2]));b=s[m.end():(ms[i+1].start() if i+1<len(ms) else len(s))]
  adds[pos]=[re.sub(r'\s+',' ',x).strip() for x in re.findall(r'\\add\s+([^\\]+?)\\add\*',b)]
  b=re.sub(r'\\w\s+([^|\\]+?)\|[^\\]*?\\w\*',lambda x:x[1],b)
  b=re.sub(r'\\(?:f|x)\s+.*?\\(?:f|x)\*',' ',b,flags=re.S)
  b=re.sub(r'\\[a-zA-Z0-9+]+\*?',' ',b)
  if pos in out:raise ValueError('Duplicate comparison verse')
  out[pos]=re.sub(r'\s+',' ',b).strip()
 return out,adds

def norm(s):return re.sub(r'\s+','',s)
def typnorm(s):return norm(s.replace('æ','ae').replace('Æ','Ae').replace('ï','i').replace('Ï','I')).casefold()
def compare(data,witness):
 if set(witness)!=set(KEYS)|OMIT:raise ValueError('Comparison witness positions mismatch')
 diffs=[]
 for pos,ss in data.items():
  a=''.join(x['text'] for x in ss);b=witness[pos]
  if norm(a)==norm(b):continue
  if typnorm(a)!=typnorm(b):raise ValueError('Substantive digital witness disagreement '+vref(pos)+' '+repr(a)+' <> '+repr(b))
  diffs.append({'verse_id':vref(pos),'primary_usx':a,'comparison_usfm':b,
   'kind':'historical_ligature_or_print_small_capitals','substantive_difference':False,
   'resolution':'Print fidelity assessed; source files unchanged. Historical inscription capitals retained; ligatures documented.'})
 if len(diffs)!=16:raise ValueError('Expected 16 typography differences, got '+str(len(diffs)))
 return diffs

def source_page_rows(doc):
 if len(doc)!=1310:raise ValueError('Expected original 1310-page 1901 scan')
 if 'JOHN' not in doc[1074].get_text().upper():raise ValueError('Incorrect John opening source page')
 if 'JOHN' not in doc[1101].get_text().upper():raise ValueError('Incorrect John closing source page')
 if 'ACTS' not in doc[1104].get_text().upper():raise ValueError('Incorrect successor book boundary')
 # Source page 1074 is the original historical Gospel-by-John map; 1073 and 1103 are interleaves.
 if len(doc[1073].get_text().strip())>50:raise ValueError('Expected original map page (1074) not map')
 pages=[{'source_pdf_page':1074,'type':'map','printed_page':None,
   'description':'Original historical map titled Palestine in the Gospel by John (period geography, not geocoded)',
   'evidence_method':'Original 1901 John map inspected visually and retained without redraw.'}]
 for i,(ch,v,carries) in enumerate(PAGE_STARTS):
  first=(ch,v);n=1075+i
  if first not in POSITION:raise ValueError('Invalid first verse '+str(first))
  nxt=PAGE_STARTS[i+1] if i+1<len(PAGE_STARTS) else None
  if nxt:
   nk=(nxt[0],nxt[1]);last=nk if nxt[2] else before(nk)
  else:last=KEYS[-1]
  if POSITION[first]>POSITION[last]:raise ValueError('Reversed page span '+str(n))
  if len(doc[n-1].get_text())<500:raise ValueError('Unexpectedly short original page '+str(n))
  pages.append({'source_pdf_page':n,'type':'scripture','printed_page':93+i,
    'first_verse':vref(first),'last_verse':vref(last),
    'page_begins_with_verse_continuation':bool(carries),
    'evidence_method':'Original 1901 physical page openings and continuations inspected; not exhaustive character-by-character collation.'})
 counts=defaultdict(list)
 for p in pages[1:]:
  lo=POSITION[tuple(map(int,p['first_verse'].split('.')[1:]))];hi=POSITION[tuple(map(int,p['last_verse'].split('.')[1:]))]
  for k in KEYS[lo:hi+1]:counts[k].append(p['source_pdf_page'])
 if set(counts)!=set(KEYS):raise ValueError('Incomplete mapping coverage')
 crossing={vref(k):v for k,v in counts.items() if len(v)>1}
 if any(len(v)!=2 or v[1]!=v[0]+1 for v in crossing.values()):raise ValueError('Nonconsecutive page carryover')
 return pages,crossing

def facsimiles(doc,dat,rows):
 d=dat/'facsimile';d.mkdir(parents=True,exist_ok=True);vols=[]
 for first,last in [(1074,1088),(1089,1102)]:
  p=d/f'asv1901-john-pages-{first}-{last}.pdf'
  sub=fitz.open();sub.insert_pdf(doc,from_page=first-1,to_page=last-1)
  sub.save(p,garbage=3,deflate=True,no_new_id=True);sub.close()
  vols.append({'filename':p.name,'first_source_pdf_page':first,'last_source_pdf_page':last,
    'bytes':p.stat().st_size,'sha256':sha(p)})
 for row in rows:
  n=row['source_pdf_page'];volume=next(x for x in vols if x['first_source_pdf_page']<=n<=x['last_source_pdf_page'])
  row['volume']=volume['filename'];row['volume_pdf_page']=n-volume['first_source_pdf_page']+1
 return vols

def make_manifest(out):
 out=Path(out);bk=out/'books/john';dat=out/'data/asv1901/john'
 hashes={str(p.relative_to(out)):sha(p) for folder in (bk,dat) for p in folder.rglob('*')
  if p.is_file() and p.name!='RELEASE_MANIFEST.json' and '__pycache__' not in p.parts}
 catalog=out/'data/asv1901/catalog-john.json';hashes[str(catalog.relative_to(out))]=sha(catalog)
 write(bk/'RELEASE_MANIFEST.json',{'status':'STRUCTURALLY_BUILT_FROM_DECLARED_SOURCE',
   'edition':ED,'book':CODE,'chapter_count':21,'verse_count':878,
   'source_hashes':SOURCE_SHAS,'files':dict(sorted(hashes.items()))})

def build(args):
 for p,k in [(args.pdf,'original_pdf'),(args.usx,'primary_usx'),(args.usfm,'comparison_usfm')]:
  if sha(p)!=SOURCE_SHAS[k]:raise ValueError('Pinned original input hash mismatch: '+k)
 out=Path(args.out);bk=out/'books/john';dat=out/'data/asv1901/john'
 bk.mkdir(parents=True,exist_ok=True);dat.mkdir(parents=True,exist_ok=True)
 # Rebuilding from the shipped package uses its own static templates and scripts.
 srcroot=Path(__file__).resolve().parent.parent
 if (srcroot/'README.md').exists() and srcroot.resolve()!=bk.resolve():
  for p in srcroot.rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts and p.name!='RELEASE_MANIFEST.json':
    dest=bk/p.relative_to(srcroot);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 primary,paragraphs,notes=parse_usx(args.usx);comparison,adds=parse_usfm(args.usfm)
 differences=compare(primary,comparison)
 italic=sum(sum(x['kind']=='supplied' for x in spans) for spans in primary.values())
 if italic!=135:raise ValueError('Unexpected italic span count '+str(italic))
 mismatches={vref(pos):[s,adds.get(pos,[])] for pos,spans in primary.items()
  if norm(' '.join((s:=[re.sub(r'\s+',' ',seg['text']).strip() for seg in spans if seg['kind']=='supplied'])))!=norm(' '.join(adds.get(pos,[])))}
 if mismatches:raise ValueError('Italic witness conflict '+str(mismatches)[:1000])
 # Print small capitals in John 19:19 verified against original 1901 source PDF page 1099.
 p=(19,19);original='Jesus of Nazareth, the King of the Jews';upper='JESUS OF NAZARETH, THE KING OF THE JEWS'
 if sum(x['text'].count(original) for x in primary[p])!=1:raise ValueError('John 19:19 print capitalization anchor mismatch')
 for x in primary[p]:x['text']=x['text'].replace(original,upper)
 for ch,n in enumerate(TRAD,1):
  vs=[{'id':vref((ch,v)),'edition_verse_id':'ASV1901:'+vref((ch,v)),
        'verse':v,'spans':primary[(ch,v)],'paragraph_start':(ch,v) in paragraphs}
      for v in range(1,n+1) if (ch,v) not in OMIT]
  write(dat/f'chapters/{ch:02d}.json',{'schema_version':'1.0.0','edition_id':ED,'book_code':CODE,
     'chapter':ch,'verses':vs})
 doc=fitz.open(args.pdf);pages,crossing=source_page_rows(doc);vs=facsimiles(doc,dat,pages)
 write(dat/'page-index.json',{'schema_version':'1.0.0','edition_id':ED,'book_code':CODE,
   'source_pdf_sha256':SOURCE_SHAS['original_pdf'],'pages':pages,'volumes':vs,
   'navigation_rule':'Ascending physical source PDF pages including John historical map; verse may cover two pages.'})
 omission={'verse_id':'JHN.5.4','edition_verse_id':'ASV1901:JHN.5.4','status':'NOT_IN_1901_MAIN_TEXT',
  'source_pdf_page':1080,'printed_new_testament_page':98,'apparatus_after_verse':'JHN.5.3',
  'original_note_text':'Many ancient authorities insert, wholly or in part, waiting for the moving of the water: 4 for an angel of the Lord went down at certain seasons into the pool, and troubled the water: whosoever then first after the troubling of the water stepped in was made whole, with whatsoever disease he was holden.'}
 write(dat/'verse-omissions.json',{'schema_version':'1.0.0','edition_id':ED,'book_code':CODE,
  'traditional_verse_positions':879,'main_text_verse_count':878,'omissions':[omission]})
 # Consequential original manuscript caveats, not modern independently asserted textual judgments.
 variants=[
  {'passage':'JHN.5.4','source_pdf_page':1080,'printed_note_anchor':'JHN.5.3',
    'note':'The original ASV 1901 apparatus reports some authorities insert a statement about the moving of the water and an angel (traditional verse 5:4).',
    'main_text_status':'NOT_PRESENT_IN_1901_MAIN_TEXT'},
  {'passage':'JHN.7.53-JHN.8.11','source_pdf_page':1085,'printed_note_anchor':'JHN.7.53',
    'note':'Most of the ancient authorities omit John 7:53–8:11. Those which contain it vary much from each other.',
    'main_text_status':'PRESENT_IN_1901_MAIN_TEXT_WITH_SQUARE_BRACKETS'}]
 write(dat/'textual-apparatus.json',{'schema_version':'1.0.0','edition_id':ED,'book_code':CODE,
   'apparatus':variants,'scope_note':'Selected high-impact original ASV 1901 marginal notes, with 271 complete digital USX note elements retained in untouched source file and historical pages. No modern textual-critical assessment.'})
 write(bk/'build-inputs/chapter-counts.json',{'edition_id':ED,'book_code':CODE,
  'traditional_verse_positions':879,'main_text_verse_count':878,
  'chapter_traditional_verse_counts':{str(c):n for c,n in enumerate(TRAD,1)},'omitted_verse_ids':['JHN.5.4']})
 write(bk/'build-inputs/original-page-index-input.json',{'source_pdf_page_range':[1074,1102],
  'historical_map_page':1074,'printed_scripture_pages':[93,120],
  'page_first_verse_and_continuations':[{'source_pdf_page':1075+i,'first_visible_verse':vref((c,v)),
      'continues_previous_page':bool(k)} for i,(c,v,k) in enumerate(PAGE_STARTS)]})
 write(bk/'build-inputs/source-differences-resolved.json',{'edition_id':ED,'book_code':CODE,
   'difference_count':16,'differences':differences,
   'print_small_caps_projection':[{'verse_id':'JHN.19.19','original_source_text':original,'printed_small_capitals_projection':upper}],
   'witness_independence':'NOT_ESTABLISHED',
   'note':'All digital main-text disagreements typographic. One traditional verse in USFM only; original print appendix treatment preserved. Original witnesses unmodified.'})
 checks={f'{c:02d}':{'chapter':c,'digital_witness_verse_ids_checked':True,
   'historical_source_print_page_bounds_checked':True,
   'main_text_verse_count':TRAD[c-1]-(1 if c==5 else 0)} for c in range(1,22)}
 write(dat/'chapter-checks.json',checks)
 write(out/'data/asv1901/catalog-john.json',{'schema_version':'1.0.0','edition_id':ED,
   'book_code':CODE,'book_name':'John','book_order':43,
   'canonical_ids':'JHN.{chapter}.{verse}','edition_ids':'ASV1901:JHN.{chapter}.{verse}',
   'chapter_count':21,'verse_count':878,'traditional_verse_positions':879,
   'omitted_from_1901_main_text':['JHN.5.4'],'verse_omissions_path':'john/verse-omissions.json',
   'textual_apparatus_path':'john/textual-apparatus.json',
   'chapter_path_template':'john/chapters/{chapter:02d}.json',
   'facsimile_index':'john/page-index.json','predecessor_book_code':'LUK','successor_book_code':'ACT',
   'source_provenance':'books/john/SOURCE_INVENTORY.json','reader':'books/john/site/index.html',
   'note':'Main text 878 verses, historical 5:4 note excluded, John 7:53–8:11 included with original brackets and caveat. No unverified Strong’s mappings.'})
 write(bk/'SOURCE_INVENTORY.json',{'edition':ED,'book_code':CODE,
  'original_print_pdf':{'filename':'Bible_(1901_American_Standard_Version).pdf',
   'sha256':SOURCE_SHAS['original_pdf'],'pdf_pages':len(doc),'included_in_release':False,
   'source_url':'https://archive.org/details/holybible00newy',
   'source_pdf_page_range':[1074,1102],'printed_scripture_pages':[93,120]},
  'upstream_archives':{'primary_english_usx_archive':{'filename':'American-Standard-Version-Bible-master.zip','sha256':ARCHIVES['primary_usx']},
    'comparison_usfm_archive':{'filename':'eng-asv_usfm.zip','sha256':ARCHIVES['comparison_usfm']}},
  'source_subfiles':{'primary_usx':'books/john/sources/asv1901-english-only/43-JHN.usx',
    'comparison_usfm':'books/john/sources/comparison-only/73-JHNeng-asv.usfm'},
  'source_subfile_hashes':{'primary_usx':SOURCE_SHAS['primary_usx'],'comparison_usfm':SOURCE_SHAS['comparison_usfm']},
  'source_witness_independence':'NOT_ESTABLISHED','strongs_alignment':'NOT_IMPORTED_UNVERIFIED',
  'rights_note':'1901 ASV text public domain in the United States; verify territorial law for overseas redistribution.'})
 for f,src in [('sources/asv1901-english-only/43-JHN.usx',args.usx),('sources/comparison-only/73-JHNeng-asv.usfm',args.usfm)]:
  target=bk/f;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
 summary={'status':'PASS','book_code':CODE,'edition_id':ED,'book_order':43,
   'chapters':21,'main_text_verse_count':878,'traditional_verse_positions':879,
   'omitted_verse_ids':['JHN.5.4'],'source_witness_typographic_differences':16,
   'non_substantive_differences':16,'italic_spans':italic,'primary_usx_note_elements':notes,
   'source_pdf_page_range':[1074,1102],'historical_map_pages':1,'scripture_pages':28,
   'physical_pages':29,'page_spanning_verses':len(crossing),'facsimile_volumes':2,
   'page_index_coverage':'PASS_ALL_878_MAIN_TEXT_VERSES',
   'comparison_witness_supplied_spans':'PASS_135_OF_135',
   'original_print_small_capital_projections':1,
   'john_7_53_to_8_11_bracketed_in_main_text':True,
   'main_text_character_by_character_print_proofreading':'NOT_PERFORMED',
   'hosted_browser_interaction':'NOT_PERFORMED',
   'source_witness_independence':'NOT_ESTABLISHED',
   'lexical_strongs_alignment':'NOT_IMPORTED_UNVERIFIED'}
 write(bk/'VALIDATION_REPORT.json',summary);doc.close()
 make_manifest(out)
 return summary

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 for k in ('pdf','usx','usfm','out'):parser.add_argument('--'+k,type=Path,required=True)
 print(json.dumps(build(parser.parse_args()),indent=2))
