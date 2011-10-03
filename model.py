from datetime import datetime

from mongokit import Document, Connection, ObjectId
#MONGODB_HOST = 'localhost'
#MONGODB_PORT = 27017
#conn = Connection(MONGODB_HOST, MONGODB_PORT)
con = Connection()
        

@con.register
class Search(Document):
    """
    Dyanmically store searches of the RTC system. 

    This allows for dynamic storage of a search so it can be used for
    later purposes.
    """
    __database__ = 'ertc'
    __collection__ = 'search'

    structure = {
            'created': datetime,
            'name': unicode, # Display for user to remember the reference
            'description': unicode, # Help keep track of searches for users
            'type': unicode, # bill, videos, votes ect
            'filters': dict # Fields to filter seach by
            }
    
    required_fields = ['name', 'type', 'created']
    default_values = {'created':datetime.utcnow}
    use_dot_notation = True

@con.register
class Topic(Document):
    """
    Collection of search that are group together to associate together.

    Provides a way to take a specific item and group all information about
    into a single location. If all the videos, votes and ammendments for 
    farming woulc be grouped into a topic to provide on location to find 
    information about it.
    """
    __database__ = 'ertc'
    __collection__ = 'topic'
    structure = {
            'created':datetime,
            'name': unicode,
            'searches':[ObjectId] # Link to search in the database
            }
    required_fields = ['name', 'created']
    default_values = {'created':datetime.utcnow}
    use_dot_notation = True


@con.register
class TopicComment(Document):
    """
    Stream user comments about a specific topic
    """
    __database__ = 'ertc'
    __collection__ = 'topic_comment'

    structure = {
            'created': datetime,
            'user': unicode,
            'content': unicode,
            'votes': { 
                    'user': unicode,
                    'point': int # Positive or negative up/down vote
                    }
            }
    required_fields = ['created', 'user', 'content', 'votes']
    use_dot_notation = True

