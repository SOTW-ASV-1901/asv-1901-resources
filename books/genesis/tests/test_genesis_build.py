import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_genesis import parse_ref, compare_witnesses, load_verse_index, EXPECTED

def test_expected_counts():
    assert len(EXPECTED)==50 and sum(EXPECTED)==1533

def test_ref_order():
    assert parse_ref('GEN.1.1')==(1,1)
    assert parse_ref('Genesis 2:12')==(2,12)
    try:parse_ref('GEN.1.99')
    except ValueError:pass
    else:raise AssertionError('Invalid verse accepted')

def test_supplied_word_preserved():
    rows={1:[{'id':'GEN.1.1','spans':[{'text':'word ','kind':'text'}, {'text':'supplied','kind':'supplied'}]}]}
    assert load_verse_index(rows)=={'GEN.1.1':'word supplied'}
    assert compare_witnesses(rows,{'GEN.1.1':'word supplied'})==[]

if __name__=='__main__':
    for f in (test_expected_counts,test_ref_order,test_supplied_word_preserved):f()
    print('3 tests passed')
