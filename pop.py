"""
Prduces some sample data for the applcation

"""
from model import con

s1 = con.Search()
s1.name = u'Mel Watt Video Search'
s1.description = u'Videos that Mel Watt has been associated with'
s1.type = u'house_video'
s1.filters = {'legislator_name':'Mr. Watt of NC'} # Example
s1.save()


s2 = con.Search()
s2.name = u'Mel Watt Floor Updates'
s2.description = u'Floor that Mel Watt has been associated with'
s2.type = u'floor_updates'
s2.filters = {'search':'Watt'} # Example
s2.save()

t = con.Topic()
t.name = u'Mel Watt'
t.searches = [s1._id, s2._id]
t.save()
