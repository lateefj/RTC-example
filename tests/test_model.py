from datetime import datetime

import model

def test_search():
    s = model.con.Search()
    try:
        s.save()
        assert False, 'no required fields are set'
    except Exception, e:
        pass
    s.name = u'test'
    s.created = datetime.utcnow()
    s.description = u'testing descirption'
    s.type = u'house_video'
    s.filters = {'bill_id': 'wer233'}
    s.save()
    fs = model.con.Search.find_one({'_id':s._id})
    for k, v in s.items():
        if k == 'created': # Date storage percision issue
            pass
        else:
            assert fs.has_key(k), 'found search did not have key %s' % k
            assert fs[k] == v, 'key "%s" found is %s does not match ' % (
                    k, fs[k]) + 'value set %s' % (v,)
    
    s.delete()
    ds = model.con.Search.find_one({'_id':s._id})
    assert ds is None, 'Should not be able to find deleted search'



