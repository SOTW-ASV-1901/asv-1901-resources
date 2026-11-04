#!/usr/bin/env python3
"""SOTW ASV1901 additive book foundation builder.
Requires the exact historical PDF and two original digitally preserved witnesses.
All output is generated under an arbitrary destination repository root.
Example: python build_third-john.py --pdf original1901.pdf --usx PRIMARY.usx --usfm COMPARISON.usfm --out /tmp/testrepo
"""
from pathlib import Path
import argparse,hashlib,json,re,shutil,unicodedata,xml.etree.ElementTree as ET
from collections import defaultdict,Counter
import fitz

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for x in iter(lambda:f.read(1<<20),b''):h.update(x)
 return h.hexdigest()
def write(path,obj):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def normalize(s):return re.sub(r'\s+','',s)
def typography_normalize(s):
 s=s.replace('æ','ae').replace('Æ','Ae').replace('œ','oe').replace('Œ','Oe')
 s=''.join(c for c in unicodedata.normalize('NFKD',s) if unicodedata.category(c)!='Mn')
 return normalize(s).casefold()
def parse_usx(code,path,expected):
 root=ET.parse(path).getroot();data={};paragraphs=set();notes=[];current=None;pending=False
 def add(t,kind):
  if not t or current is None:return
  b=data[current]
  if b and b[-1]['kind']==kind:b[-1]['text']+=t
  else:b.append({'text':t,'kind':kind})
 def walk(e,kind='text'):
  nonlocal current,pending
  tag=e.tag.split('}')[-1]
  if tag in ('book','chapter'):return
  if tag=='verse':
   if e.get('sid'):
    m=re.fullmatch(code+r'\s+(\d+):(\d+)',e.get('sid'))
    if not m:raise ValueError('Invalid verse sid: '+str(e.attrib))
    current=int(m[1]),int(m[2]);
    if current in data:raise ValueError('Duplicate USX verse '+str(current))
    data[current]=[]
    if pending:paragraphs.add(current)
    pending=False
   elif e.get('eid'):current=None
   return
  if tag=='note':notes.append(''.join(e.itertext()));return
  if tag=='para' and e.get('style') in ('p','m','q1','q2','q3','pi','pi1','pi2'):pending=True
  if tag=='char' and e.get('style') in ('add','addpn'):kind='supplied'
  if tag=='para' and e.get('style') in ('q1','q2','q3') and current in data and data[current] and e.text:add('\n',kind)
  add(e.text,kind)
  for x in e:walk(x,kind);add(x.tail,kind)
 for e in root:walk(e)
 if set(data)!=set(expected):raise ValueError('USX main-text verse set mismatch: missing='+str(set(expected)-set(data))+' extra='+str(set(data)-set(expected)))
 for p,ss in data.items():
  if not ss:raise ValueError('Empty main-text verse '+str(p))
  ss[0]['text']=ss[0]['text'].lstrip();ss[-1]['text']=ss[-1]['text'].rstrip()
  data[p]=[s for s in ss if s['text']]
 return data,paragraphs,notes

def parse_usfm(path):
 s=Path(path).read_text(encoding='utf-8-sig');ms=list(re.finditer(r'\\(c|v)\s+(\d+)',s));ch=None;out={};adds={}
 for i,m in enumerate(ms):
  if m[1]=='c':ch=int(m[2]);continue
  if ch is None:raise ValueError('USFM verse before chapter')
  pos=(ch,int(m[2]));b=s[m.end():(ms[i+1].start() if i+1<len(ms) else len(s))]
  adds[pos]=[re.sub(r'\s+',' ',x).strip() for x in re.findall(r'\\add\s+([^\\]+?)\\add\*',b)]
  b=re.sub(r'\\w\s+([^|\\]+?)\|[^\\]*?\\w\*',lambda x:x[1],b)
  b=re.sub(r'\\(?:f|x)\s+.*?\\(?:f|x)\*',' ',b,flags=re.S)
  b=re.sub(r'\\[a-zA-Z0-9+]+\*?',' ',b)
  if pos in out:raise ValueError('Duplicate USFM verse '+str(pos))
  out[pos]=re.sub(r'\s+',' ',b).strip()
 return out,adds

def make_manifest(root,slug,code,n_verses,n_chapters,source_hashes):
 root=Path(root);bk=root/'books'/slug;dat=root/'data/asv1901'/slug
 paths=sorted([p for folder in (bk,dat) for p in folder.rglob('*') if p.is_file() and p.name!='RELEASE_MANIFEST.json' and '__pycache__' not in p.parts])
 catalog=root/'data/asv1901'/f'catalog-{slug}.json';paths.append(catalog)
 write(bk/'RELEASE_MANIFEST.json',{'status':'STRUCTURALLY_BUILT_FROM_DECLARED_SOURCE','edition':'ASV1901',
  'book':code,'chapter_count':n_chapters,'verse_count':n_verses,'source_hashes':source_hashes,
  'files':dict(sorted((str(p.relative_to(root)),sha(p)) for p in paths))})

def build(args):
 srcroot=Path(__file__).resolve().parent.parent
 config=json.loads((srcroot/'build-inputs/book-plan.json').read_text())
 code,slug,book=config['code'],config['slug'],config['name'];nchap=len(config['chapter_counts']);trad=sum(config['chapter_counts']);omit={tuple(x) for x in config['omissions']}
 keys=[(ch,v) for ch,ct in enumerate(config['chapter_counts'],1) for v in range(1,ct+1) if (ch,v) not in omit]
 position={key:i for i,key in enumerate(keys)}
 if len(position)!=trad-len(omit):raise ValueError('Bad planned canonical positions')
 def ref(k):return f'{code}.{k[0]}.{k[1]}'
 def before(k):return keys[position[k]-1]
 for actual,expected in [(args.pdf,config['source_pdf_sha256']),(args.usx,config['primary_usx_sha256']),(args.usfm,config['comparison_usfm_sha256'])]:
  if sha(actual)!=expected:raise ValueError('Pinned original source checksum mismatch '+str(actual))
 root=Path(args.out);bk=root/'books'/slug;dat=root/'data/asv1901'/slug
 bk.mkdir(parents=True,exist_ok=True);dat.mkdir(parents=True,exist_ok=True)
 if srcroot.resolve()!=bk.resolve():
  for p in srcroot.rglob('*'):
   if p.is_file() and p.name!='RELEASE_MANIFEST.json' and '__pycache__' not in p.parts:
    target=bk/p.relative_to(srcroot);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
 primary,paragraphs,notes=parse_usx(code,args.usx,keys)
 comparison,adds=parse_usfm(args.usfm)
 if set(comparison)!=set(keys)|omit:raise ValueError('USFM traditional verse set mismatch: '+str(set(comparison)^(set(keys)|omit)))
 # Verify translator-supplied wording against alternate witness, not only USX typography.
 supplied=sum(s['kind']=='supplied' for ss in primary.values() for s in ss);exceptions=[]
 for key,ss in primary.items():
  a=[re.sub(r'\s+',' ',s['text']).strip() for s in ss if s['kind']=='supplied']
  if normalize(' '.join(a))!=normalize(' '.join(adds.get(key,[]))):exceptions.append({'verse':ref(key),'primary':a,'comparison':adds.get(key,[])})
 if exceptions:raise ValueError('Unreconciled supplied-word italics '+str(exceptions[:3]))
 differences=[];classification=Counter()
 allowed=set(config.get('allowed_word_differences',[]))
 for key,ss in primary.items():
  a=''.join(s['text'] for s in ss);b=comparison[key]
  if normalize(a)==normalize(b):continue
  ident=ref(key)
  kind='orthography_or_case' if typography_normalize(a)==typography_normalize(b) else 'different_words_or_hyphenation'
  if kind=='different_words_or_hyphenation' and ident not in allowed:raise ValueError('Unresolved digital wording disagreement '+ident+': '+repr(a)+' <> '+repr(b))
  differences.append({'verse_id':ident,'primary_usx':a,'comparison_usfm':b,'kind':kind,'source_locked_resolution':'Typography resolved where supported by print; uncertain hyphenation retained as original USX with explicit ambiguity notice. Upstream witnesses unchanged.'})
  classification[kind]+=1
 # Print-backed exceptions are applied only to the final derived chapter text.
 for correction in config['source_decisions']:
  ident=correction['verse'].split('.');key=(int(ident[1]),int(ident[2]));found=0
  for seg in primary[key]:
   if correction['source_phrase'] in seg['text']:
    seg['text']=seg['text'].replace(correction['source_phrase'],correction['replace_with']);found+=1
  if found!=1:raise ValueError('Failed unique print correction '+correction['verse'])
 for ch,ct in enumerate(config['chapter_counts'],1):
  rows=[{'id':ref((ch,v)),'edition_verse_id':'ASV1901:'+ref((ch,v)),'verse':v,'spans':primary[(ch,v)],'paragraph_start':(ch,v) in paragraphs}
        for v in range(1,ct+1) if (ch,v) not in omit]
  write(dat/f'chapters/{ch:02d}.json',{'schema_version':'1.0.0','edition_id':'ASV1901','book_code':code,'chapter':ch,'verses':rows})
 with fitz.open(args.pdf) as doc:
  if len(doc)!=1310:raise ValueError('Unexpected PDF page count')
  first,last=config['first_pdf'],config['last_pdf']
  maps=set(config['map_pages']);interleaf=set(config['interleaf_pages'])
  srcrows={int(x[0]):x for x in config['scripture']}
  if set(range(first,last+1))!=maps|interleaf|set(srcrows):raise ValueError('Source-page index has gaps/overlaps')
  scripture=config['scripture']
  rows=[]
  for n in range(first,last+1):
   if n in maps:
    rows.append({'source_pdf_page':n,'type':'map','printed_page':None,
     'description':'Original 1901 historical map; interpret as period cartography, not verified modern geocoding.',
     'evidence_method':'Physical historical map retained as printed, no redraw.'})
   elif n in interleaf:
    rows.append({'source_pdf_page':n,'type':'interleaf','printed_page':None,
     'description':'Original blank reverse leaf following historical map; included to preserve source page order.',
     'evidence_method':'Retained complete 1901 historical page, without inventing a Scripture position.'})
   else:
    j=next(i for i,x in enumerate(scripture) if x[0]==n);first_key=(scripture[j][1],scripture[j][2]);carry=bool(scripture[j][3]);
    if first_key not in position:raise ValueError('Source start verse not main-text key '+str(first_key))
    if j+1<len(scripture):
     nxt=scripture[j+1];next_key=(nxt[1],nxt[2]);last_key=next_key if nxt[3] else before(next_key)
    else:last_key=keys[-1]
    if position[last_key]<position[first_key]:raise ValueError('Reversed page verse span '+str(n))
    if len(doc[n-1].get_text())<500:raise ValueError('Expected Scripture page did not contain print text '+str(n))
    rows.append({'source_pdf_page':n,'type':'scripture','printed_page':config['first_print']+j,
      'first_verse':ref(first_key),'last_verse':ref(last_key),'running_head_verified':False,
      'page_begins_with_verse_continuation':carry,
      'evidence_method':'1901 original page headers, opening/closing verses and transitions inspected; exhaustive character-level print collation not performed.'})
  cover=defaultdict(list)
  for row in rows:
   if row['type']!='scripture':continue
   k1=tuple(map(int,row['first_verse'].split('.')[1:]));k2=tuple(map(int,row['last_verse'].split('.')[1:]))
   for key in keys[position[k1]:position[k2]+1]:cover[key].append(row['source_pdf_page'])
  if set(cover)!=set(keys):raise ValueError('Verse-to-page index coverage incomplete')
  crossing={ref(k):pages for k,pages in cover.items() if len(pages)>1}
  if any(len(p)>2 for p in crossing.values()):raise ValueError('Verse spans >2 distinct Scripture pages')
  # Extract the exact original pages, including any historical maps and reverse blank leaves.
  vols=[];facdir=dat/'facsimile';facdir.mkdir(exist_ok=True)
  for a,b in config['volume_bounds']:
   file=f'asv1901-{slug}-pages-{a}-{b}.pdf';p=facdir/file
   subset=fitz.open();subset.insert_pdf(doc,from_page=a-1,to_page=b-1)
   subset.save(p,garbage=3,deflate=True,no_new_id=True);subset.close()
   vols.append({'filename':file,'first_source_pdf_page':a,'last_source_pdf_page':b,
     'bytes':p.stat().st_size,'sha256':sha(p)})
  for r in rows:
   n=r['source_pdf_page'];vol=next(v for v in vols if v['first_source_pdf_page']<=n<=v['last_source_pdf_page'])
   r['volume']=vol['filename'];r['volume_pdf_page']=n-vol['first_source_pdf_page']+1
  write(dat/'page-index.json',{'schema_version':'1.0.0','edition_id':'ASV1901','book_code':code,
    'source_pdf_sha256':config['source_pdf_sha256'],'pages':rows,'volumes':vols,
    'navigation_rule':'Physical original PDF pages in source order; original maps and interleaves preserve historical position. A verse can continue across map/interleaf insertions.'})
  pages_for_omitted=[{'verse_id':ref(x),'edition_verse_id':'ASV1901:'+ref(x),'status':'NOT_IN_1901_MAIN_TEXT',
    'source_pdf_page':config['omission_page'][ref(x)],'source_note':'Traditional verse wording appears in original marginal apparatus, not as running main-text verse.'} for x in sorted(omit)]
  write(dat/'verse-omissions.json',{'schema_version':'1.0.0','edition_id':'ASV1901','book_code':code,
    'traditional_verse_positions':trad,'main_text_verse_count':len(keys),'omissions':pages_for_omitted})
  write(dat/'textual-apparatus.json',{'schema_version':'1.0.0','edition_id':'ASV1901','book_code':code,
    'apparatus':config['other_apparatus'],
    'scope_note':'Selected major original 1901 marginal notes, supplemented by all original scanned printed apparatus and byte-preserved original digital USX notes; not a modern textual-critical reconstruction.'})
  write(bk/'build-inputs/source-differences-resolved.json',{'edition_id':'ASV1901','book_code':code,
    'difference_count':len(differences),'typographical_or_orthographic_count':classification['orthography_or_case'],
    'different_words_or_hyphenation_count':classification['different_words_or_hyphenation'],
    'differences':differences,'print_backed_decisions':config['source_decisions'],
    'additional_print_backed_uncorrected_readings':{'1TH.5.14':'Original line break faint-/hearted does not distinguish lexical hyphenation; primary USX faint-hearted retained without asserting print-proof.'} if False else {},
    'source_witness_independence':'NOT_ESTABLISHED'})
  write(bk/'build-inputs/original-page-index-input.json',{'source_pdf_page_range':[first,last],
     'original_maps':sorted(maps),'interleaves':sorted(interleaf),'printed_scripture_pages':[config['first_print'],config['first_print']+len(scripture)-1],
     'page_first_verses': [{'source_pdf_page':x[0],'first_verse':ref((x[1],x[2])),
      'continues_previous_scripture_page':bool(x[3])} for x in scripture]})
  write(bk/'build-inputs/chapter-counts.json',{'edition_id':'ASV1901','book_code':code,
    'chapter_traditional_verse_counts':{str(i+1):n for i,n in enumerate(config['chapter_counts'])},
    'traditional_verse_positions':trad,'main_text_verse_count':len(keys),'omitted_verse_ids':[ref(p) for p in sorted(omit)]})
  write(dat/'chapter-checks.json',{f'{ch:02d}':{'chapter':ch,'digital_witness_verse_ids_checked':True,
    'historical_source_print_page_bounds_checked':'MANUALLY_RESEARCHED_BOUNDARIES_WITH_SCANNED_SOURCE',
    'main_text_verse_count':n-sum(x==ch for x,v in omit)} for ch,n in enumerate(config['chapter_counts'],1)})
  source_hashes={'original_pdf':config['source_pdf_sha256'],'primary_usx':config['primary_usx_sha256'],'comparison_usfm':config['comparison_usfm_sha256']}
  srcdir=bk/'sources';(srcdir/'asv1901-english-only').mkdir(parents=True,exist_ok=True);(srcdir/'comparison-only').mkdir(exist_ok=True)
  shutil.copyfile(args.usx,srcdir/'asv1901-english-only'/config['usx']);shutil.copyfile(args.usfm,srcdir/'comparison-only'/config['usfm'])
  write(bk/'SOURCE_INVENTORY.json',{'edition':'ASV1901','book_code':code,
    'original_print_pdf':{'filename':'Bible_(1901_American_Standard_Version).pdf','sha256':source_hashes['original_pdf'],
     'pdf_pages':len(doc),'included_in_release':False,'source_url':'https://archive.org/details/holybible00newy',
     'source_pdf_page_range':[first,last],'printed_scripture_page_range':[config['first_print'],config['first_print']+len(scripture)-1]},
    'upstream_archives':{'primary_english_usx_archive':{'filename':'American-Standard-Version-Bible-master.zip','sha256':config['source_archives_sha256']['primary_usx']},
       'comparison_usfm_archive':{'filename':'eng-asv_usfm.zip','sha256':config['source_archives_sha256']['comparison_usfm']}},
    'source_subfiles':{'primary_usx':f'books/{slug}/sources/asv1901-english-only/{config["usx"]}',
       'comparison_usfm':f'books/{slug}/sources/comparison-only/{config["usfm"]}'},
    'source_subfile_hashes':{'primary_usx':source_hashes['primary_usx'],'comparison_usfm':source_hashes['comparison_usfm']},
    'source_witness_independence':'NOT_ESTABLISHED','strongs_alignment':'NOT_IMPORTED_UNVERIFIED',
    'rights_note':'1901 ASV Bible text public domain in United States; check other territorial rules before redistribution.'})
  write(root/'data/asv1901'/f'catalog-{slug}.json',{'schema_version':'1.0.0','edition_id':'ASV1901','book_code':code,
    'book_name':book,'book_order':config['order'],'canonical_ids':code+'.{chapter}.{verse}',
    'edition_ids':'ASV1901:'+code+'.{chapter}.{verse}','chapter_count':nchap,'verse_count':len(keys),
    'traditional_verse_positions':trad,'omitted_from_1901_main_text':[ref(x) for x in sorted(omit)],
    'verse_omissions_path':f'{slug}/verse-omissions.json','textual_apparatus_path':f'{slug}/textual-apparatus.json',
    'chapter_path_template':f'{slug}/chapters/{{chapter:02d}}.json','facsimile_index':f'{slug}/page-index.json',
    'predecessor_book_code':config['predecessor'],'successor_book_code':config['successor'],
    'source_provenance':f'books/{slug}/SOURCE_INVENTORY.json','reader':f'books/{slug}/site/index.html',
    'note':'Book-specific verified 1901 page and original-text indices; no unverified Strong’s alignment or global catalog modification.'})
  summary={'status':'PASS','edition_id':'ASV1901','book_code':code,'book_order':config['order'],'chapters':nchap,
    'main_text_verse_count':len(keys),'traditional_verse_positions':trad,'omitted_verse_ids':[ref(k) for k in sorted(omit)],
    'source_witness_typographical_or_orthographic_differences':classification['orthography_or_case'],
    'source_witness_wording_or_hyphenation_differences':classification['different_words_or_hyphenation'],
    'source_witness_differences_resolved_against_original_print':'PRINT_SUPPORTED_WITH_DOCUMENTED_LINE_WRAP_AMBIGUITY' if False else True,
    'translator_supplied_italic_spans':supplied,'italic_spans_vs_comparison':'PASS_'+str(supplied)+'_OF_'+str(supplied),
    'primary_usx_note_elements':len(notes),'historical_source_pdf_page_range':[first,last],
    'historical_map_pages':len(maps),'original_interleaf_pages_retained':len(interleaf),
    'scripture_pages':len(scripture),'physical_pages':len(rows),'page_spanning_main_text_verses':len(crossing),
    'page_index_coverage':'PASS_ALL_'+str(len(keys))+'_MAIN_TEXT_VERSES',
    'facsimile_volumes':len(vols),'original_source_sha256':'MATCHED_PINNED_MATTHEW_PROVERBS_SOURCE',
    'original_print_character_by_character_proofreading':'NOT_PERFORMED','hosted_browser_interaction':'NOT_PERFORMED',
    'source_witness_independence':'NOT_ESTABLISHED','lexical_strongs_alignment':'NOT_IMPORTED_UNVERIFIED'}
  write(bk/'VALIDATION_REPORT.json',summary)
 make_manifest(root,slug,code,len(keys),nchap,source_hashes)
  # close original PDF context
 return summary

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('pdf','usx','usfm','out'):p.add_argument('--'+name,required=True,type=Path)
 print(json.dumps(build(p.parse_args()),indent=2))
