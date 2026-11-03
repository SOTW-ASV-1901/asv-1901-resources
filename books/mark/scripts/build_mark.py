#!/usr/bin/env python3
"""Deterministic original-source build: SOTW American Standard Version 1901 Mark.

Requires original 1901 PDF and two preserved English digital witnesses. Historic
textual omissions are not promoted to main-text verses. Does not use the network.
"""
import argparse, hashlib, json, re, shutil, unicodedata
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET
import fitz

CODE='MRK'; SLUG='mark'; ED='ASV1901'
TRAD=[45,28,35,41,43,56,37,38,50,52,33,44,37,72,47,20]
OMIT={(7,16),(9,44),(9,46),(11,26),(15,28)}
SHAS={'original_pdf':'e5a19756c441024c056a5f2e11eba4e1213c9a3c42e5d22c33147520bbbd3f7d',
 'primary_usx':'033aafba50a1ee2fdc6218c3c7900e9250f756b782410ff520c9aa7d2d68ff63',
 'comparison_usfm':'7b3439876c90adb006961fc8f3fb6cf4699730765b715138c10bfe7d9cfa1c25'}
ARCHIVES={'primary_usx':'9c0c15c70a490583ae1f2bd8e617ef6ca692ade1e528c7df08175777412dd247',
'comparison_usfm':'5e385a1a89887849cb07c88ddf4df37708e0fa901b1f1b7f0b8204c153f0a901'}
# Map on source page 1012. Scripture starts 1013 and ends 1034.
# Tuple: chapter, verse physically visible at page opening, continues prior page.
PAGE_STARTS=[(1,1,0),(1,27,1),(2,14,1),(3,14,1),(4,17,0),(5,10,1),
 (6,1,0),(6,31,1),(7,6,1),(8,3,1),(8,38,1),(9,30,1),(10,15,1),
 (10,44,1),(11,23,1),(12,19,1),(13,6,1),(14,2,1),(14,32,1),
 (14,67,1),(15,32,1),(16,14,1)]
assert sum(TRAD)==678 and len(OMIT)==5 and len(PAGE_STARTS)==22

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()

def write(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def verse_list():return [(ch,v) for ch,n in enumerate(TRAD,1) for v in range(1,n+1) if (ch,v) not in OMIT]
KEYS=verse_list();POSITION={p:i for i,p in enumerate(KEYS)}
def vref(p):return f'MRK.{p[0]}.{p[1]}'
def before(p):return KEYS[POSITION[p]-1]
def after(p):return KEYS[POSITION[p]+1]

def parse_usx(path):
 r=ET.parse(path).getroot();current=None; pending=False; notes=0; data={}; paragraphs=set()
 def add(text,kind):
  if not text or current is None:return
  ss=data[current]
  if ss and ss[-1]['kind']==kind:ss[-1]['text']+=text
  else:ss.append({'text':text,'kind':kind})
 def walk(e,kind='text'):
  nonlocal current,pending,notes
  tag=e.tag.split('}')[-1]
  if tag in ('book','chapter'):return
  if tag=='verse':
   if e.get('sid'):
    m=re.fullmatch(r'MRK\s+(\d+):(\d+)',e.get('sid'))
    if not m:raise ValueError('Invalid verse SID '+str(e.attrib))
    current=int(m[1]),int(m[2])
    if current in data:raise ValueError('Duplicate verse SID')
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
  for child in e:
   walk(child,kind);add(child.tail,kind)
 for child in r:walk(child)
 if set(data)!=set(KEYS):raise ValueError(f'USX verse positions differ: missing {set(KEYS)-set(data)}, extra {set(data)-set(KEYS)}')
 for p,ss in data.items():
  ss[0]['text']=ss[0]['text'].lstrip();ss[-1]['text']=ss[-1]['text'].rstrip()
  data[p]=[x for x in ss if x['text']]
  if not data[p]:raise ValueError('Empty verse '+vref(p))
 return data,paragraphs,notes

def parse_usfm(path):
 s=Path(path).read_text(encoding='utf-8-sig');matches=list(re.finditer(r'\\(c|v)\s+(\d+)',s));ch=None;out={}
 for i,m in enumerate(matches):
  if m[1]=='c':ch=int(m[2]);continue
  if ch is None:raise ValueError('Verse without chapter')
  key=(ch,int(m[2]));b=s[m.end():(matches[i+1].start() if i+1<len(matches) else len(s))]
  b=re.sub(r'\\w\s+([^|\\]+?)\|[^\\]*?\\w\*',lambda q:q[1],b)
  b=re.sub(r'\\(?:f|x)\s+.*?\\(?:f|x)\*',' ',b,flags=re.S)
  b=re.sub(r'\\[a-zA-Z0-9+]+\*?',' ',b)
  if key in out:raise ValueError('Duplicate USFM')
  out[key]=re.sub(r'\s+',' ',b).strip()
 return out

def norm(s):return re.sub(r'\s+','',s)
def typographic_norm(s):
 s=s.replace('æ','ae').replace('Æ','Ae').replace('ï','i').replace('Ï','I')
 return norm(s).casefold()

def compare(data,alt):
 if set(alt)!=set(KEYS)|OMIT:raise ValueError('USFM positions unexpected')
 diffs=[]
 for key,ss in data.items():
  a=''.join(v['text'] for v in ss);b=alt[key]
  if norm(a)!=norm(b):
   typographic=typographic_norm(a)==typographic_norm(b)
   if not typographic:raise ValueError(f'Substantive witness difference requires new print check {key}: {a} / {b}')
   diffs.append({'verse_id':vref(key),'primary_usx':a,'comparison_usfm':b,
    'kind':'historical_ligature_diacritic_or_capitals','resolution':('Original 1901 print uses small capitals for the inscription, reproduced as uppercase in derived text. Preserve both unmodified witnesses.' if key==(15,26) else 'Retain primary USX wording while documenting the comparison edition typography. The original facsimile remains the appearance authority.'),
    'substantive_difference':False})
 if len(diffs)!=17:raise ValueError(f'Unexpected number of typographic differences {len(diffs)}')
 inscription=data[(15,26)]
 assert sum('the King of the Jews' in x['text'] for x in inscription)==1
 for span in inscription:span['text']=span['text'].replace('the King of the Jews','THE KING OF THE JEWS')
 return diffs

EXCEPTIONS=[
 (7,16,1021,'MRK.7.15','Many ancient authorities insert verse 16 in the printed footnote.'),
 (9,44,1024,'MRK.9.43','Verses 44 and 46 (identical with verse 48) are omitted by the best ancient authorities.'),
 (9,46,1024,'MRK.9.43','Verses 44 and 46 (identical with verse 48) are omitted by the best ancient authorities.'),
 (11,26,1027,'MRK.11.25','Many ancient authorities add verse 26 in the printed footnote.'),
 (15,28,1032,'MRK.15.27','Many ancient authorities insert verse 28 in the printed footnote.'),
]

def generate_pages(doc,data):
 if len(doc)!=1310:raise ValueError('Original PDF page count unexpected')
 if not ('ACCORDING' in doc[1012].get_text().upper() and 'MARK' in doc[1012].get_text().upper()):raise ValueError('Mark begins wrong page')
 if not 'MARK' in doc[1033].get_text().upper():raise ValueError('Mark ends wrong page')
 if not 'LUKE' in doc[1036].get_text().upper():raise ValueError('Luke begins wrong page')
 for page in range(1013,1035):
  if len(doc[page-1].get_text())<1000:raise ValueError(f'Empty Scripture source page {page}')
 rows=[{'source_pdf_page':1012,'type':'map','printed_page':None,
  'description':'Original historical Palestine map illustrating the Gospel by Mark immediately before the first Mark page.',
  'evidence_method':'Original 1901 scanned page directly inspected; title identifies the Gospel by Mark.'}]
 for i,(ch,vs,continued) in enumerate(PAGE_STARTS):
  p=(ch,vs);last=KEYS[-1] if i==len(PAGE_STARTS)-1 else (PAGE_STARTS[i+1][0],PAGE_STARTS[i+1][1])
  if i<len(PAGE_STARTS)-1 and not PAGE_STARTS[i+1][2]:last=before(last)
  if p>last:raise ValueError(f'Reversed physical page index {i}')
  rows.append({'source_pdf_page':1013+i,'type':'scripture','printed_page':35+i,
   'first_verse':vref(p),'last_verse':vref(last),
   'running_head_first_verse':vref(after(p) if continued else p) if i else None,
   'page_begins_with_verse_continuation':bool(continued),
   'evidence_method':'Original 1901 scanned page opening/closing and printed running heads independently inspected, including physical carryover verses; not exhaustive character-by-character proofreading.'})
 coverage=defaultdict(list)
 for row in rows[1:]:
  a=POSITION[tuple(map(int,row['first_verse'].split('.')[1:]))]
  b=POSITION[tuple(map(int,row['last_verse'].split('.')[1:]))]
  for pos in KEYS[a:b+1]:coverage[pos].append(row['source_pdf_page'])
 if set(coverage)!=set(KEYS):raise ValueError('Incomplete verse-to-page coverage')
 crossing={vref(k):pages for k,pages in coverage.items() if len(pages)>1}
 if not all(len(p)==2 and p[1]==p[0]+1 for p in crossing.values()):raise ValueError('Non-adjacent page continuation')
 return rows,crossing

def write_volumes(doc,dataroot,rows):
 dest=dataroot/'facsimile';dest.mkdir(parents=True,exist_ok=True)
 volumes=[]
 for first,last in [(1012,1023),(1024,1034)]:
  sub=fitz.open();sub.insert_pdf(doc,from_page=first-1,to_page=last-1)
  filename=f'asv1901-mark-pages-{first}-{last}.pdf';target=dest/filename
  sub.save(target,garbage=3,deflate=True,no_new_id=True);sub.close()
  volumes.append({'filename':filename,'first_source_pdf_page':first,'last_source_pdf_page':last,
  'bytes':target.stat().st_size,'sha256':sha(target)})
 for row in rows:
  page=row['source_pdf_page'];vol=next(v for v in volumes if v['first_source_pdf_page']<=page<=v['last_source_pdf_page'])
  row['volume']=vol['filename'];row['volume_pdf_page']=page-vol['first_source_pdf_page']+1
 return volumes

def build(args):
 for path,key in [(args.pdf,'original_pdf'),(args.usx,'primary_usx'),(args.usfm,'comparison_usfm')]:
  if sha(path)!=SHAS[key]:raise ValueError('Pinned source SHA-256 mismatch: '+key)
 out=Path(args.out);bk=out/'books/mark';dat=out/'data/asv1901/mark';bk.mkdir(parents=True,exist_ok=True);dat.mkdir(parents=True,exist_ok=True)
 dest=bk/'sources/asv1901-english-only/41-MRK.usx';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.usx,dest)
 dest=bk/'sources/comparison-only/71-MRKeng-asv.usfm';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.usfm,dest)
 primary,paragraphs,notes=parse_usx(args.usx);other=parse_usfm(args.usfm);diffs=compare(primary,other)
 for ch,n in enumerate(TRAD,1):
  verses=[]
  for v in range(1,n+1):
   if (ch,v) in OMIT:continue
   spans=primary[(ch,v)]
   verses.append({'id':f'MRK.{ch}.{v}','edition_verse_id':f'ASV1901:MRK.{ch}.{v}','verse':v,
    'spans':spans,'paragraph_start':(ch,v) in paragraphs})
  write(dat/f'chapters/{ch:02d}.json',{'schema_version':'1.0.0','edition_id':ED,'book_code':CODE,'chapter':ch,'verses':verses})
 doc=fitz.open(args.pdf);rows,crossings=generate_pages(doc,primary);volumes=write_volumes(doc,dat,rows)
 write(dat/'page-index.json',{'schema_version':'1.0.0','edition_id':ED,'book_code':CODE,'source_pdf_sha256':SHAS['original_pdf'],
   'pages':rows,'volumes':volumes,'navigation_rule':'original physical scan pages, including Mark-associated map'})
 omission_data=[{'verse_id':vref((c,v)),'edition_verse_id':f'ASV1901:MRK.{c}.{v}',
    'status':'NOT_IN_1901_MAIN_TEXT','source_pdf_page':p,'printed_new_testament_page':p-978,
    'apparatus_after_verse':prior,'evidence':descr} for c,v,p,prior,descr in EXCEPTIONS]
 write(bk/'build-inputs/verse-exceptions.json',{'edition_id':ED,'book_code':CODE,'record_type':'intentional_print_main_text_omission',
   'exceptions':omission_data})
 write(dat/'verse-omissions.json',{'schema_version':'1.0.0','edition_id':ED,'book_code':CODE,
   'traditional_verse_positions':sum(TRAD),'main_text_verse_count':len(KEYS),'omissions':omission_data})
 textual={'schema_version':'1.0.0','edition_id':ED,'book_code':CODE,'apparatus':[{
   'passage':'MRK.16.9-MRK.16.20','main_text_status':'PRESENT_IN_ASV1901_MAIN_TEXT',
   'source_pdf_page':1033,'printed_new_testament_page':55,
   'note':'The two oldest Greek manuscripts, and some other authorities, omit from verse 9 to the end. Some other authorities have a different ending to the Gospel.',
   'evidence_status':'Original ASV 1901 English-only USX note confirmed against historical printed page; not an independent current critical edition judgment.',
   'display_rule':'Preserve verses in 1901 main text and present a visible manuscript-variant notice.'}]}
 write(dat/'textual-apparatus.json',textual)
 write(bk/'build-inputs/original-page-index-input.json',{'source_pdf_page_range':[1012,1034],
   'book_map_page':1012,'scripture_pages':[1013,1034],
   'page_first_verse_continuations':[['MRK.'+str(ch)+'.'+str(v),bool(cont)] for ch,v,cont in PAGE_STARTS],
   'research_note':'Indexed against actual original 1901 PDF, including wrapped previous-page verses and an illustrative map.'})
 write(bk/'build-inputs/chapter-counts.json',{'edition_id':ED,'book_code':CODE,'traditional_verse_positions':sum(TRAD),
  'printed_main_text_verses':len(KEYS), 'chapter_traditional_verse_counts':{str(i):n for i,n in enumerate(TRAD,1)},
  'omitted_verse_ids':[vref(x) for x in sorted(OMIT)]})
 write(bk/'build-inputs/source-differences-resolved.json',{'edition_id':ED,'book_code':CODE,'differences':diffs,
  'difference_count':len(diffs),'status':'TYPOGRAPHIC_ONLY_NOT_SUBSTANTIVE',
  'warning':'The two digital witnesses are not established as independently produced transcriptions. Exact 1901 facsimile retained; no exhaustive character-by-character printed proofread.'})
 italic=sum(x['kind']=='supplied' for ss in primary.values() for x in ss)
 chapter_checks={f'{ch:02d}':{'chapter':ch,'digital_witness_verse_ids_checked':True,
  'source_print_page_range_checked':True,'main_text_verses':TRAD[ch-1]-sum(c==ch for c,v in OMIT)} for ch in range(1,17)}
 write(dat/'chapter-checks.json',chapter_checks)
 write(out/'data/asv1901/catalog-mark.json',{'schema_version':'1.0.0','edition_id':ED,'book_code':CODE,'book_name':'Mark','book_order':41,
  'canonical_ids':'MRK.{chapter}.{verse}','edition_ids':'ASV1901:MRK.{chapter}.{verse}',
  'chapter_count':16,'verse_count':len(KEYS),'traditional_verse_positions':sum(TRAD),
  'omitted_from_1901_main_text':[vref(p) for p in sorted(OMIT)],
  'verse_omissions_path':'mark/verse-omissions.json','textual_apparatus_path':'mark/textual-apparatus.json',
  'chapter_path_template':'mark/chapters/{chapter:02d}.json','facsimile_index':'mark/page-index.json',
  'predecessor_book_code':'MAT','successor_book_code':'LUK',
  'source_provenance':'books/mark/SOURCE_INVENTORY.json','reader':'books/mark/site/index.html',
  'note':'Original 1901 ASV main text omits five traditional Mark verses documented in print apparatus; Mark 16:9–20 remains in main text with a printed manuscript warning. No unverified Strong’s alignments.'})
 write(bk/'SOURCE_INVENTORY.json',{'edition':ED,'book_code':CODE,'original_print_pdf':{
    'filename':'Bible_(1901_American_Standard_Version).pdf','sha256':SHAS['original_pdf'],
    'pdf_pages':len(doc),'included_in_release':False,'source_url':'https://archive.org/details/holybible00newy',
    'source_pdf_page_range':[1012,1034],'printed_scripture_page_range':[35,56]},
    'upstream_archives':{'primary_english_usx_archive':{'filename':'American-Standard-Version-Bible-master.zip','sha256':ARCHIVES['primary_usx']},
    'comparison_usfm_archive':{'filename':'eng-asv_usfm.zip','sha256':ARCHIVES['comparison_usfm']}},
    'source_subfiles':{'primary_usx':'books/mark/sources/asv1901-english-only/41-MRK.usx',
                      'comparison_usfm':'books/mark/sources/comparison-only/71-MRKeng-asv.usfm'},
    'source_subfile_hashes':{'primary_usx':SHAS['primary_usx'],'comparison_usfm':SHAS['comparison_usfm']},
    'source_witness_independence':'NOT_ESTABLISHED','strongs_alignment':'NOT_IMPORTED_UNVERIFIED',
    'rights_note':'ASV 1901 is public domain in the United States; check reuse rights for non-US publication and individual transcriptions.'})
 summary={'status':'PASS','book_code':CODE,'edition_id':ED,'book_order':41,'chapters':16,
   'main_text_verse_count':len(KEYS),'traditional_verse_positions':sum(TRAD),
   'omitted_verse_ids':[vref(p) for p in sorted(OMIT)],'source_witness_differences':len(diffs),
   'non_substantive_differences':len(diffs),'italic_spans':italic,'primary_usx_notes':notes,
   'page_index_coverage':f'PASS_ALL_{len(KEYS)}_MAIN_TEXT_VERSES',
   'original_pdf_page_range':[1012,1034],'historical_map_pages':1,'scripture_pages':22,'physical_pages':len(rows),
   'page_spanning_verses':len(crossings),'facsimile_volumes':len(volumes),
   'manuscript_variant_note':'MRK.16.9-MRK.16.20 preserved from 1901 main text and annotated',
   'main_text_character_by_character_print_proofreading':'NOT_PERFORMED',
   'hosted_browser_interaction':'NOT_PERFORMED','source_witness_independence':'NOT_ESTABLISHED',
   'lexical_strongs_alignment':'NOT_IMPORTED_UNVERIFIED'}
 write(bk/'VALIDATION_REPORT.json',summary)
 hashes={str(p.relative_to(out)):sha(p) for root in (bk,dat) for p in root.rglob('*') if p.is_file() and p.name!='RELEASE_MANIFEST.json' and '__pycache__' not in p.parts}
 catalog=out/'data/asv1901/catalog-mark.json';hashes[str(catalog.relative_to(out))]=sha(catalog)
 write(bk/'RELEASE_MANIFEST.json',{'status':'STRUCTURALLY_BUILT_FROM_DECLARED_SOURCE','edition':ED,'book':CODE,
  'chapter_count':16,'verse_count':len(KEYS),'source_hashes':SHAS,'files':dict(sorted(hashes.items()))})
 return summary

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('pdf','usx','usfm','out'):p.add_argument('--'+name,type=Path,required=True)
 print(json.dumps(build(p.parse_args()),indent=2))
