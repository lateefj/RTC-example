from model import con

s = con.Search()
s.name = u'Mel Watt Video Search'
s.description = u'Videos that Mel Watt has been associated with'
s.type = u'house_video'
s.filters = {'legislature_name':'Mel Watt'} # Example
s.save()

t = con.Topic()
t.name = u'NC Politics'
t.searches = [s._id]
t.save()
