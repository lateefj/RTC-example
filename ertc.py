import sys

from flask import Flask, render_template
from mongokit import ObjectId

import model

app = Flask(__name__)
app.config.from_object('default_settings')
app.config.from_pyfile('app.cfg', silent=True)

@app.route('/')
def index():
    topics = model.con.Topic.find()
    return render_template('index.html', topics=topics)

@app.route('/t/<name>')
def topic(name):
    topic = model.con.Topic.find_one({'name':name})
    searches = []
    for s in topic.searches:
        ts = model.con.Search.find_one({'_id':s})
        if ts is not None:
            searches.append(ts)
    print(searches) 
    return render_template('topic.html', topic=topic, searches=searches)

@app.route('/s/<oid>')
def search(oid):
    s = model.con.Search.find_one({'_id': ObjectId(oid=oid)})
    return render_template('search.html', search=s)

if __name__ == '__main__':
    if hasattr(app.config, 'DEBUG'):
        app.debug = app.config.DEBUG
        if app.debug:
            print('Application server in debug mod NOT FOR PRODUCTION!!')
    app.run()

