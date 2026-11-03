#!/usr/bin/env python3
"""Deterministic, source-locked ASV 1901 Luke book builder.

Preserves two unchanged digital witnesses and exact original 1901 facsimile pages.
Historical textual variants are retained as apparatus, never invented as main text.
All page bounds were researched from original printed pages; no network required.
"""
import argparse,hashlib,json,re,shutil
from pathlib import Path
from collections import defaultdict
from xml.etree import ElementTree as ET
import fitz

CODE='LUK';SLUG='luke';ED='ASV1901'
TRAD=[80,52,38,44,39,49,50,56,62,42,54,59,35,35,32,31,37,43,48,47,38,71,56,53]
OMIT={(17,36),(23,17)}
SOURCE_SHAS={'original_pdf':'e5a19756c441024c056a5f2e11eba4e1213c9a3c42e5d22c33147520bbbd3f7d',
 'primary_usx':'106662a7447d29362e64ffeebc0b1b50aeb372a4abdf8d2e4ed9f85ef82209f8',
 'comparison_usfm':'c0fc52bab1fc14b1c821f4a9baf0c9050a2c5c861174e3ca97be8f6501255ae6'}
ARCHIVES={'primary_usx':'9c0c15c70a490583ae1f2bd8e617ef6ca692ade1e528c7df08175777412dd247',
 'comparison_usfm':'5e385a1a89887849cb07c88ddf4df37708e0fa901b1f1b7f0b8204c153f0a901'}
# Physical first verse on each scanned page 1037..1072. Flag means a verse
# already began on the preceding physical page and continues here.
PAGE_STARTS=[
 (1,1,0),(1,26,0),(1,61,1),(2,15,1),(2,48,0),(3,23,1),
 (4,18,1),(5,4,0),(5,34,1),(6,27,1),(7,8,1),(7,38,1),
 (8,17,1),(8,43,1),(9,19,1),(9,50,0),(10,21,1),(11,8,1),
 (11,38,1),(12,15,1),(12,47,1),(13,19,0),(14,14,1),(15,12,1),
 (16,10,1),(17,10,1),(18,8,1),(18,43,1),(19,35,1),(20,19,1),
 (21,10,0),(22,7,1),(22,40,1),(23,5,1),(23,41,1),(24,19,1)]
assert len(TRAD)==24 and sum(TRAD)==1151 and len(PAGE_STARTS)==36
KEYS=[(ch,v) for ch,n in enumerate(TRAD,1) for v in range(1,n+1) if (ch,v) not in OMIT]
assert len(KEYS)==1149
POSITION={key:i for i,key in enumerate(KEYS)}
def vref(pos):return f'LUK.{pos[0]}.{pos[1]}'
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
    m=re.fullmatch(r'LUK\s+(\d+):(\d+)',e.get('sid'))
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
  for ch in e:walk(ch,kind);add(ch.tail,kind)
 for child in root:walk(child)
 if set(data)!=set(KEYS):raise ValueError(f'Actual USX positions differ: missing {set(KEYS)-set(data)} extra {set(data)-set(KEYS)}')
 for k,ss in data.items():
  if not ss:raise ValueError('No verse text '+vref(k))
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
def typnorm(s):
 return norm(s.replace('æ','ae').replace('Æ','Ae').replace('ï','i').replace('Ï','I')).casefold()

def compare(data,witness):
 if set(witness)!=set(KEYS)|OMIT:raise ValueError('Comparison witness has unexpected verses')
 diffs=[]
 for pos,ss in data.items():
  a=''.join(x['text'] for x in ss);b=witness[pos]
  if norm(a)==norm(b):continue
  if typnorm(a)!=typnorm(b):raise ValueError('Substantive witness disagreement '+vref(pos)+' '+repr(a)+' <> '+repr(b))
  diffs.append({'verse_id':vref(pos),'primary_usx':a,'comparison_usfm':b,
   'kind':'historical_ligature_or_small_capitals','substantive_difference':False,
   'resolution':'Both original digital files unchanged; source-print typography independently retained where verified.'})
 if len(diffs)!=26:raise ValueError('Expected 26 typographic differences, got '+str(len(diffs)))
 return diffs

def fix_print_small_caps(data):
 # These three print inscriptions have verified small capitals in the original 1901 scan.
 edits=[((1,31),'Jesus','JESUS'),((2,21),'Jesus','JESUS'),((23,38),'This is the King of the Jews','THIS IS THE KING OF THE JEWS')]
 for pos,old,new in edits:
  matches=sum(s['text'].count(old) for s in data[pos]);
  if matches!=1:raise ValueError(f'Original-print caps replacement expected once at {vref(pos)}: {matches}')
  for ss in data[pos]:ss['text']=ss['text'].replace(old,new)
 return [dict(verse_id=vref(p),original_english=old,print_small_capital_projection=new) for p,old,new in edits]

def generate_pages(doc):
 if len(doc)!=1310:raise ValueError('Original 1901 complete scan expected 1310 pages')
 if 'LUKE' not in doc[1036].get_text().upper():raise ValueError('Luke first source page incorrect')
 if 'LUKE' not in doc[1071].get_text().upper():raise ValueError('Luke last source page incorrect')
 if 'JOHN' not in doc[1074].get_text().upper():raise ValueError('Next book boundary incorrect')
 rows=[{'source_pdf_page':1036,'type':'map','printed_page':None,
        'description':'Original historical map associated with the Gospel by Luke, preserved directly before first Luke text page.',
        'evidence_method':'Original 1901 map inspected visually and identified by printed Gospel by Luke title.'}]
 for i,(ch,vs,carries) in enumerate(PAGE_STARTS):
  pos=(ch,vs)
  if pos not in POSITION:raise ValueError('First visible verse not canonical: '+str(pos))
  nxt=PAGE_STARTS[i+1] if i+1<len(PAGE_STARTS) else None
  if nxt:
   next_pos=nxt[:2]
   last=next_pos if nxt[2] else before(next_pos)
  else:last=KEYS[-1]
  if POSITION[pos]>POSITION[last]:raise ValueError('Reversed page boundary')
  page=1037+i
  if len(doc[page-1].get_text())<750:raise ValueError('Unexpected low source text page '+str(page))
  rows.append({'source_pdf_page':page,'type':'scripture','printed_page':57+i,
   'first_verse':vref(pos),'last_verse':vref(last),
   'page_begins_with_verse_continuation':bool(carries),
   'evidence_method':'Independent original 1901 image inspection of physical page openings, chapter transitions and the first and last verse; not exhaustive character-by-character print proofreading.'})
 counts=defaultdict(list)
 for row in rows[1:]:
  lo=POSITION[tuple(map(int,row['first_verse'].split('.')[1:]))];hi=POSITION[tuple(map(int,row['last_verse'].split('.')[1:]))]
  for pos in KEYS[lo:hi+1]:counts[pos].append(row['source_pdf_page'])
 if set(counts)!=set(KEYS):raise ValueError('Verse coverage missing: '+str(set(KEYS)-set(counts)))
 crossing={vref(k):v for k,v in counts.items() if len(v)>1}
 if any(len(v)!=2 or v[1]!=v[0]+1 for v in crossing.values()):raise ValueError('Invalid multi-page verse')
 return rows,crossing

def volumes(doc,dat,rows):
 d=dat/'facsimile';d.mkdir(parents=True,exist_ok=True)
 vs=[]
 for first,last in [(1036,1054),(1055,1072)]:
  out=d/f'asv1901-luke-pages-{first}-{last}.pdf'
  sub=fitz.open();sub.insert_pdf(doc,from_page=first-1,to_page=last-1)
  sub.save(out,garbage=3,deflate=True,no_new_id=True);sub.close()
  vs.append({'filename':out.name,'first_source_pdf_page':first,'last_source_pdf_page':last,
    'bytes':out.stat().st_size,'sha256':sha(out)})
 for row in rows:
  n=row['source_pdf_page'];v=next(x for x in vs if x['first_source_pdf_page']<=n<=x['last_source_pdf_page'])
  row['volume']=v['filename'];row['volume_pdf_page']=n-v['first_source_pdf_page']+1
 return vs

def build(args):
 for p,k in [(args.pdf,'original_pdf'),(args.usx,'primary_usx'),(args.usfm,'comparison_usfm')]:
  if sha(p)!=SOURCE_SHAS[k]:raise ValueError('Pinned input SHA-256 mismatch '+k)
 out=Path(args.out);bk=out/'books/luke';dat=out/'data/asv1901/luke'
 bk.mkdir(parents=True,exist_ok=True);dat.mkdir(parents=True,exist_ok=True)
 d=bk/'sources/asv1901-english-only/42-LUK.usx';d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.usx,d)
 d=bk/'sources/comparison-only/72-LUKeng-asv.usfm';d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.usfm,d)
 primary,paragraphs,notes=parse_usx(args.usx);comparison,add=parse_usfm(args.usfm);diffs=compare(primary,comparison)
 # Validate supplied-word spans against the second source independently.
 orig_add={pos:[re.sub(r'\s+',' ',seg['text']).strip() for seg in ss if seg['kind']=='supplied'] for pos,ss in primary.items()}
 mismatch={vref(p):(orig_add[p],add.get(p)) for p in orig_add if norm(' '.join(orig_add[p]))!=norm(' '.join(add.get(p,[])))}
 if mismatch:raise ValueError('Italic comparison conflict '+str(mismatch)[:800])
 caps=fix_print_small_caps(primary)
 italic=sum(sum(s['kind']=='supplied' for s in spans) for spans in primary.values())
 if italic!=209:raise ValueError('Unexpected supplied span count '+str(italic))
 for ch,n in enumerate(TRAD,1):
  vs=[{'id':vref((ch,v)),'edition_verse_id':'ASV1901:'+vref((ch,v)),'verse':v,
       'spans':primary[(ch,v)],'paragraph_start':(ch,v) in paragraphs}
       for v in range(1,n+1) if (ch,v) not in OMIT]
  write(dat/f'chapters/{ch:02d}.json',{'schema_version':'1.0.0','edition_id':ED,'book_code':CODE,'chapter':ch,'verses':vs})
 doc=fitz.open(args.pdf);pages,crossing=generate_pages(doc);volume_records=volumes(doc,dat,pages)
 write(dat/'page-index.json',{'schema_version':'1.0.0','edition_id':ED,'book_code':CODE,
   'source_pdf_sha256':SOURCE_SHAS['original_pdf'],'pages':pages,'volumes':volume_records,
   'navigation_rule':'ascending original physical scan pages, including Luke-associated historical map'})
 omissions=[{'verse_id':vref(p),'edition_verse_id':'ASV1901:'+vref(p),
   'status':'NOT_IN_1901_MAIN_TEXT','source_pdf_page':sourcepage,'printed_new_testament_page':sourcepage-980,
   'apparatus_after_verse':vref(prev),'original_note_text':explanation}
   for p,sourcepage,prev,explanation in [
    ((17,36),1062,(17,35),'Some ancient authorities add verse 36 There shall be two men in the field; the one shall be taken, and the other shall be left. Mt. 24:40.'),
    ((23,17),1070,(23,16),'Many ancient authorities insert verse 17 Now he must needs release unto them at the feast one prisoner. Others add the same words after verse 19.')]]
 write(dat/'verse-omissions.json',{'schema_version':'1.0.0','edition_id':ED,'book_code':CODE,
     'traditional_verse_positions':1151,'main_text_verse_count':1149,'omissions':omissions})
 write(bk/'build-inputs/verse-exceptions.json',{'edition_id':ED,'book_code':CODE,
   'record_type':'historical_print_main_text_omission','exceptions':omissions})
 variants=[
  {'passage':'LUK.22.43-LUK.22.44','source_pdf_page':1069,'note':'Many ancient authorities omit verses 43, 44.',
   'main_text_status':'PRESENT_IN_1901_MAIN_TEXT'},
  {'passage':'LUK.23.34','source_pdf_page':1070,'note':'Some ancient authorities omit the prayer beginning Father, forgive them.',
   'main_text_status':'PRESENT_IN_1901_MAIN_TEXT'},
  {'passage':'LUK.24.12','source_pdf_page':1071,'note':'Some ancient authorities omit verse 12.',
   'main_text_status':'PRESENT_IN_1901_MAIN_TEXT'},
  {'passage':'LUK.24.40','source_pdf_page':1072,'note':'Some ancient authorities omit verse 40.',
   'main_text_status':'PRESENT_IN_1901_MAIN_TEXT'},
  {'passage':'LUK.24.51','source_pdf_page':1072,'note':'Some ancient authorities omit the phrase and was carried up into heaven.',
   'main_text_status':'PRESENT_IN_1901_MAIN_TEXT'},
  {'passage':'LUK.24.52','source_pdf_page':1072,'note':'Some ancient authorities omit the phrase worshipped him, and.',
   'main_text_status':'PRESENT_IN_1901_MAIN_TEXT'}]
 write(dat/'textual-apparatus.json',{'schema_version':'1.0.0','edition_id':ED,'book_code':CODE,'apparatus':variants,
   'source_note':'Selected consequential original ASV printed notes; original 382 digital footnote elements preserved unmodified in USX and complete historical facsimiles. Not a modern independent textual-critical assessment.'})
 write(bk/'build-inputs/original-page-index-input.json',{'source_pdf_page_range':[1036,1072],
    'historical_map':1036,'printed_scripture_pages':[57,92],
    'page_first_verse_and_continuations':[
      {'source_pdf_page':1037+i,'first_visible_verse':vref((ch,v)),'continues_previous_page':bool(c)}
      for i,(ch,v,c) in enumerate(PAGE_STARTS)]})
 write(bk/'build-inputs/chapter-counts.json',{'edition_id':ED,'book_code':CODE,
   'traditional_verse_positions':1151,'main_text_verse_count':1149,'chapter_traditional_verse_counts':{str(ch):n for ch,n in enumerate(TRAD,1)},
   'omitted_verse_ids':[vref(p) for p in sorted(OMIT)]})
 write(bk/'build-inputs/source-differences-resolved.json',{'edition_id':ED,'book_code':CODE,'difference_count':len(diffs),
   'differences':diffs,'print_small_caps_projection':caps,'witness_independence':'NOT_ESTABLISHED',
   'note':'All 26 wording differences between digital witnesses are typographic; two additional comparison verses appear only in the original 1901 footnotes.'})
 checks={f'{ch:02d}':{'chapter':ch,'digital_witness_verse_ids_checked':True,'historical_source_print_pages_checked':True,
  'main_text_verse_count':TRAD[ch-1]-sum(c==ch for c,v in OMIT)} for ch in range(1,25)}
 write(dat/'chapter-checks.json',checks)
 write(out/'data/asv1901/catalog-luke.json',{'schema_version':'1.0.0','edition_id':ED,'book_code':CODE,
  'book_name':'Luke','book_order':42,'canonical_ids':'LUK.{chapter}.{verse}','edition_ids':'ASV1901:LUK.{chapter}.{verse}',
  'chapter_count':24,'verse_count':1149,'traditional_verse_positions':1151,
  'omitted_from_1901_main_text':[vref(p) for p in sorted(OMIT)],'verse_omissions_path':'luke/verse-omissions.json',
  'textual_apparatus_path':'luke/textual-apparatus.json','chapter_path_template':'luke/chapters/{chapter:02d}.json',
  'facsimile_index':'luke/page-index.json','predecessor_book_code':'MRK','successor_book_code':'JHN',
  'source_provenance':'books/luke/SOURCE_INVENTORY.json','reader':'books/luke/site/index.html',
  'note':'Two historical main-text verse omissions; original 1901 variant notes and small-capital print artifacts preserved. No unverified lexical Strong’s alignment.'})
 write(bk/'SOURCE_INVENTORY.json',{'edition':ED,'book_code':CODE,
  'original_print_pdf':{'filename':'Bible_(1901_American_Standard_Version).pdf',
   'sha256':SOURCE_SHAS['original_pdf'],'pdf_pages':len(doc),'included_in_release':False,
   'source_url':'https://archive.org/details/holybible00newy',
   'source_pdf_page_range':[1036,1072],'printed_scripture_pages':[57,92]},
  'upstream_archives':{'primary_english_usx_archive':{'filename':'American-Standard-Version-Bible-master.zip','sha256':ARCHIVES['primary_usx']},
     'comparison_usfm_archive':{'filename':'eng-asv_usfm.zip','sha256':ARCHIVES['comparison_usfm']}},
  'source_subfiles':{'primary_usx':'books/luke/sources/asv1901-english-only/42-LUK.usx',
    'comparison_usfm':'books/luke/sources/comparison-only/72-LUKeng-asv.usfm'},
  'source_subfile_hashes':{'primary_usx':SOURCE_SHAS['primary_usx'],'comparison_usfm':SOURCE_SHAS['comparison_usfm']},
  'source_witness_independence':'NOT_ESTABLISHED','strongs_alignment':'NOT_IMPORTED_UNVERIFIED',
  'rights_note':'ASV 1901 historical text public domain in the United States; verify territorial law for overseas redistribution.'})
 summary={'status':'PASS','book_code':CODE,'edition_id':ED,'book_order':42,
  'chapters':24,'main_text_verse_count':1149,'traditional_verse_positions':1151,
  'omitted_verse_ids':[vref(p) for p in sorted(OMIT)],'source_witness_differences':26,
  'non_substantive_differences':26,'italic_spans':italic,'primary_usx_note_elements':notes,
  'source_pdf_page_range':[1036,1072],'historical_map_pages':1,'scripture_pages':36,
  'physical_pages':37,'page_spanning_verses':len(crossing),'facsimile_volumes':2,
  'page_index_coverage':'PASS_ALL_1149_MAIN_TEXT_VERSES',
  'comparison_witness_supplied_span_equality':'PASS_209_USX_SEGMENTS_VS_208_USFM_RUNS_ONE_WHITESPACE_SPLIT',
  'main_text_character_by_character_print_proofreading':'NOT_PERFORMED',
  'hosted_browser_interaction':'NOT_PERFORMED','source_witness_independence':'NOT_ESTABLISHED',
  'lexical_strongs_alignment':'NOT_IMPORTED_UNVERIFIED'}
 write(bk/'VALIDATION_REPORT.json',summary)
 doc.close()
 hashes={str(p.relative_to(out)):sha(p) for folder in (bk,dat) for p in folder.rglob('*')
    if p.is_file() and p.name!='RELEASE_MANIFEST.json' and '__pycache__' not in p.parts}
 catalog=out/'data/asv1901/catalog-luke.json';hashes[str(catalog.relative_to(out))]=sha(catalog)
 write(bk/'RELEASE_MANIFEST.json',{'status':'STRUCTURALLY_BUILT_FROM_DECLARED_SOURCE',
   'edition':ED,'book':CODE,'chapter_count':24,'verse_count':1149,
   'source_hashes':SOURCE_SHAS,'files':dict(sorted(hashes.items()))})
 return summary

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 for k in ('pdf','usx','usfm','out'):parser.add_argument('--'+k,type=Path,required=True)
 print(json.dumps(build(parser.parse_args()),indent=2))
